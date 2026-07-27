# Reddit Story Video Bot

Bot para generar vídeos verticales (9:16) estilo "Reddit Stories" para
TikTok / YouTube Shorts.

## Estado actual

- ✅ Módulo 1 — Scraping de Reddit (PRAW)
- ✅ Módulo 2 — Texto a voz (edge-tts)
- ⏳ Módulo 3 — Selección/recorte de gameplay de fondo (Fase 2)
- ⏳ Módulo 4 — Montaje con MoviePy + subtítulos karaoke con Whisper (Fase 2)
- ✅ Módulo 5 — Orquestador (`main.py`), preparado para encadenar todo

## Instalación

```bash
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # y rellena tus credenciales de Reddit
```

## Uso

### Desde la terminal de Windows

```powershell
.\run_with_venv.cmd run.py
```

### Si prefieres usar Python directamente

```powershell
.\.venv\Scripts\python.exe run.py
```

### Publicación

La opción de publicación se controla con la variable `PUBLISH_PLATFORM` en `.env`.
- `local`: solo simula el proceso y deja el vídeo en `assets/output/`.
- `youtube`: intenta subir los vídeos generados a YouTube usando `data/client_secrets.json`.

El historial de publicaciones se guarda en `data/published_videos.json`.

## Estructura del proyecto

```
reddit_video_bot/
├── main.py                  # Orquestador (Módulo 5)
├── config.py                # Configuración central (rutas, constantes, credenciales)
├── requirements.txt
├── .env.example
├── modules/
│   ├── scraper.py           # Módulo 1: scraping con PRAW
│   ├── tts.py                # Módulo 2: texto a voz con edge-tts
│   ├── video_processor.py   # Módulo 3: fondo de gameplay (placeholder, Fase 2)
│   └── video_editor.py      # Módulo 4: montaje + subtítulos (placeholder, Fase 2)
├── assets/
│   ├── audio/                # MP3 generados por el Módulo 2
│   ├── gameplay/              # ⚠️ Aquí debes copiar tus clips de Minecraft/GTA V
│   └── output/                 # Vídeos finales (Fase 2)
└── data/
    └── used_posts.json      # Histórico de posts ya usados (evita repetir historias)
```

## Cómo funciona el código y por qué se diseñó así

### `main.py`
- Este archivo es el orquestador del backend. Ejecuta el pipeline en orden:
  scraping, TTS, selección de vídeo, montaje y publicación.
- La decisión de centralizar el flujo en un solo archivo facilita que el proceso
  sea lineal y fácil de depurar.
- Alternativa: convertir esto en un servicio REST o un sistema basado en cola de
  tareas (Celery/RQ), pero para un prototipo era más sencillo mantener un
  pipeline secuencial.

### `config.py`
- Contiene constantes y rutas compartidas, además de cargar variables de entorno
  con `dotenv`.
- Usar un archivo central evita repetir rutas como `assets/audio` o `data/...`
  en varios módulos.
- Alternativa: usar un archivo YAML/JSON de configuración, o una clase de
  configuración más compleja. Se eligió `dotenv` porque es el estándar en
  proyectos pequeños y funciona bien con `.env.example`.

### `modules/scraper.py`
- Se usa scraping del feed RSS de Reddit en lugar de la API oficial de PRAW.
- Razón: no requiere credenciales específicas de Reddit y evita bloqueos por la
  API en un proyecto rápido.
- El módulo filtra historias por longitud y evita repetir posts usando `used_ids`.
- Si falla el scraping, el código devuelve una historia de emergencia para que el
  pipeline no quede totalmente bloqueado.
- Alternativas:
  - usar PRAW con credenciales y pagos de API si se necesita mayor fiabilidad.
  - usar Pushshift o la API de Reddit para búsquedas más avanzadas.

### `modules/tts.py`
- Convierte texto a audio con `edge-tts`, un motor neural gratuito de Microsoft.
- Se selecciona la voz y se generan pausas manuales entre título y cuerpo.
- Razón: `edge-tts` ofrece buena calidad de voz en español sin necesidad de una
  API paga en muchos casos.
- Alternativas:
  - `gTTS` o Azure TTS.
  - usar SSML para mejorar pausas y entonación, pero se eligió texto simple para
    mantener el sistema robusto y más fácil de depurar.

### `modules/downloader.py`
- Comprueba si ya hay gameplays en `assets/gameplay`.
- Si no hay vídeos, descarga automáticamente el siguiente clip desde los
  canales listados en `data/channels.txt` usando `yt-dlp`.
- Se mantiene un archivo `download_archive.txt` para no volver a bajar el mismo
  vídeo.
- Alternativa: usar un servicio de librerías de vídeo o almacenar vídeos en un
  bucket. Para este proyecto local, el enfoque con `yt-dlp` es práctico y rápido.

### `modules/video_processor.py`
- Selecciona el siguiente segmento disponible de un gameplay, manteniendo una
  memoria en `data/video_progress.json`.
- Esto permite que el bot use un clip largo en varios vídeos sin repetir el mismo
  tramo.
- Usa un umbral para archivar vídeos casi agotados en `assets/used_gameplays`.
- Alternativas:
  - usar una base de datos para almacenar progreso en lugar de JSON plano.
  - recortar vídeos por escena o por tiempo fijo desde el inicio.

### `modules/video_editor.py`
- Monta el vídeo final con MoviePy y genera subtítulos sincronizados usando
  Whisper para transcribir el audio generado.
- Recorta el gameplay a 9:16 y lo escala a 1080x1920, que es el formato de
  TikTok/Shorts.
- Si el vídeo supera 55 segundos, se fracciona en partes para cumplir con los
  límites de Shorts.
- Alternativas:
  - generar subtítulos directamente desde el texto usado para TTS y evitar
    transcripción, pero eso elimina la sincronización palabra por palabra.
  - usar filtros de FFMPEG en lugar de MoviePy para mejorar rendimiento.

### `modules/publisher.py`
- Permite publicar de forma local (simulada) o en YouTube.
- El backend usa OAuth y guarda el token en `data/youtube_token.json`.
- Se agregó una opción de `PUBLISH_PLATFORM` para no forzar la subida en cada
  ejecución.
- Alternativas:
  - añadir soporte para Instagram/Reels/TikTok.
  - usar una API de publicación propia o un CMS.

### `run_scheduler.py`
- Mantiene el bot ejecutándose cada cierto tiempo.
- Decisión: un proceso de Python simple mantiene la dependencia mínima.
- Alternativa: usar el programador de tareas de Windows, cron en Linux o un
  servicio Dockerizado.

### Estructura de estado y por qué JSON
- El proyecto usa JSON planos para persistir:
  - publicaciones usadas
  - historial de subreddits
  - progreso de vídeo
  - historial de publicación
- Razón: simple, fácil de leer y suficiente para un proyecto pequeño.
- Alternativa: usar SQLite, PostgreSQL o Redis si se necesitan múltiples procesos
  o mayor fiabilidad.

### Decisiones generales
- Se priorizó un diseño modular con responsabilidades claras por archivo.
- Se prefirió robustez sobre optimización extrema en el prototipo.
- En un producto más maduro, lo ideal sería:
  - tests automáticos
  - manejo de errores y reintentos más completo
  - validaciones más estrictas de credenciales
  - un backend de API o un microservicio

## Notas

- Necesitarás tener **ffmpeg** instalado en el sistema para las Fases 2 y 3
  (MoviePy y Whisper dependen de él).
- Whisper necesita PyTorch; si tienes GPU con CUDA, la transcripción irá
  mucho más rápido.

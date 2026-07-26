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
.\run_with_venv.cmd run.py --gui
```

o para el pipeline CLI:

```powershell
.\run_with_venv.cmd run.py
```

### Inicio rápido de la interfaz gráfica

Puedes abrir la GUI con doble clic usando el lanzador:

```powershell
.\start_gui.cmd
```

### Si prefieres usar Python directamente

```powershell
.\.venv\Scripts\python.exe run.py --gui
```

```powershell
.\.venv\Scripts\python.exe run.py
```

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

## Notas

- Necesitarás tener **ffmpeg** instalado en el sistema para las Fases 2 y 3
  (MoviePy y Whisper dependen de él).
- Whisper necesita PyTorch; si tienes GPU con CUDA, la transcripción irá
  mucho más rápido.

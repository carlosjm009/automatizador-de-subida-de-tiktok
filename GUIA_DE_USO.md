# Guía de uso y funcionamiento

Esta guía describe el comportamiento implementado en el proyecto. Aunque el
nombre conserva la referencia a Reddit, la aplicación no descarga historias
de Reddit: procesa archivos de texto locales. La descarga automática se usa
para obtener vídeos de gameplay de los canales configurados.

## 1. Qué hace la aplicación

El programa convierte una historia local en uno o varios vídeos verticales:

1. Comprueba que estén disponibles FFmpeg e ImageMagick y revisa la
   configuración de publicación.
2. Comprueba si hay gameplays en `assets/gameplay/`. Si no hay, intenta descargar
   uno de los canales escritos en `data/channels.txt`.
3. Busca una historia `.txt` pendiente en `data/stories/`.
4. Genera una narración en MP3 con `edge-tts`.
5. Reserva el siguiente tramo no usado de un gameplay, usando
   `data/video_progress.json` como memoria.
6. Transcribe la narración con Whisper y genera subtítulos palabra por palabra.
7. Monta el vídeo en formato vertical 1080 × 1920. Los vídeos de más de
   aproximadamente 60 segundos se dividen en partes de unos 55 segundos.
8. Simula la publicación local o intenta subir cada parte a YouTube, según la
   configuración.
9. Cuando termina el flujo, registra la historia como usada y la mueve a
   `data/stories/usadas/`.

Los registros diarios se escriben en `logs/`. El estado de la última ejecución
se guarda en `data/run_status.json`.

## 2. Requisitos

- Windows y Python 3.10 o posterior.
- FFmpeg instalado y disponible en `PATH`.
- ImageMagick instalado y disponible en `PATH`, o instalado en una de las rutas
  de Windows que comprueba `main.py`.
- Conexión a Internet para `edge-tts`, las descargas de YouTube y la descarga
  inicial del modelo de Whisper.
- Espacio libre para los audios, los vídeos descargados y el render final.

Whisper usa el modelo `base` y PyTorch. El procesamiento puede tardar bastante
en una máquina sin GPU; una GPU compatible puede acelerarlo.

## 3. Instalación en Windows

Abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Si PowerShell no permite activar el entorno virtual, puedes omitir la
activación y anteponer `.\.venv\Scripts\python.exe` a los comandos Python.
El lanzador `lanzar_gui.bat` también usa ese entorno virtual.

Instala FFmpeg e ImageMagick por separado. Cierra y vuelve a abrir la consola
después de añadir sus carpetas a `PATH`.

## 4. Preparar las entradas

### Historias

Coloca un archivo `.txt` por historia dentro de `data/stories/`. El formato
recomendado es:

```text
Título de la historia

Texto completo de la historia. Puede ocupar varios párrafos.
```

La primera línea se toma como título; una línea en blanco separa el título del
cuerpo. Si no hay separador, el archivo se interpreta como cuerpo y el título
se genera a partir del nombre del archivo. La aplicación procesa primero el
archivo pendiente que aparece antes por orden alfabético.

También puedes crear, editar, borrar, restaurar y consultar historias desde la
pestaña **Historias** de la interfaz. Al guardar una historia nueva, la
aplicación crea un nombre de archivo a partir del título.

### Vídeos de fondo

Puedes copiar vídeos `.mp4`, `.mov`, `.avi` o `.webm` a `assets/gameplay/`.
Cuando esa carpeta está vacía, `modules/downloader.py` lee las direcciones de
canal de YouTube de `data/channels.txt` y usa `yt-dlp` para intentar descargar
un vídeo nuevo. El archivo `data/downloaded_archive.txt` evita descargar de
nuevo los mismos vídeos. Usa únicamente vídeos que tengas derecho a utilizar.

## 5. Configuración

El archivo `.env` controla estas opciones principales:

```dotenv
PUBLISH_PLATFORM=local
VIDEO_TITLE_TEMPLATE=Historia: {title}
```

- `local`: no sube el vídeo; lo conserva en `assets/output/`.
- `youtube`: intenta subirlo a YouTube con la API oficial.
- `VIDEO_TITLE_TEMPLATE`: define el título y sustituye `{title}` por el título
  de la historia.

La pestaña **Configuración** permite guardar esos valores y elegir voz,
velocidad y tono de TTS. Nota: en la versión actual, `config.py` define los
valores de TTS como constantes y no los carga de `.env`; por eso, aunque la
interfaz guarde las opciones de voz, velocidad y tono, estas no cambian la
narración. Para modificarlas efectivamente, cambia `TTS_VOICE`, `TTS_RATE` y
`TTS_PITCH` en `config.py` y reinicia la aplicación.

### Activar YouTube

1. Crea un proyecto en Google Cloud Console y habilita YouTube Data API v3.
2. Crea credenciales OAuth de tipo aplicación de escritorio.
3. Guarda el JSON de credenciales como `data/client_secrets.json`.
4. Selecciona `youtube` en la configuración.
5. Inicia una ejecución y completa la autorización de Google en el navegador.

La autorización se conserva en `data/youtube_token.json` para ejecuciones
posteriores. El código publica los vídeos como **no listados** (`unlisted`),
no como públicos. Los resultados de los intentos de publicación se guardan en
`data/published_videos.json`. No compartas ni publiques las credenciales OAuth
ni el token.

## 6. Ejecutar la aplicación

### Interfaz gráfica

```powershell
.\lanzar_gui.bat
```

La interfaz tiene cuatro pestañas:

- **Historias**: administra las historias pendientes y usadas.
- **Configuración**: guarda la plataforma, la plantilla del título y las
  opciones de voz disponibles en la interfaz.
- **Ejecución**: inicia el pipeline, muestra los registros y permite cancelarlo.
- **Archivos**: abre las carpetas principales del proyecto.

También puedes iniciar la interfaz con
`.\.venv\Scripts\python.exe gui.py`.

### Ejecución desde la terminal

```powershell
.\.venv\Scripts\python.exe run.py
```

`run.py` prepara la ruta del proyecto y llama al punto de entrada de `main.py`.
También puedes ejecutar `.\.venv\Scripts\python.exe main.py` directamente.

### Ejecución programada

```powershell
.\.venv\Scripts\python.exe run_scheduler.py
```

El programador ejecuta un ciclo inmediatamente y después cada ocho horas.
Mantén abierta la ventana mientras quieras que siga activo; `Ctrl+C` lo detiene.
La interfaz gráfica no inicia este programador automáticamente.

## 7. Qué hace cada archivo de código

### Entradas y configuración

- `config.py`: define rutas, crea las carpetas necesarias, mantiene valores
  compartidos, valida la configuración de publicación y guarda cambios del
  archivo `.env`.
- `main.py`: coordina el pipeline completo, crea los registros, comprueba los
  requisitos externos y marca historias y tramos de gameplay cuando acaba el
  procesamiento.
- `run.py`: entrada corta para ejecutar el pipeline.
- `run_scheduler.py`: ejecuta el pipeline inmediatamente y lo repite cada ocho
  horas.
- `gui.py`: construye la interfaz Tkinter, gestiona historias y configuración,
  ejecuta `main.py` en segundo plano y muestra sus registros.
- `lanzar_gui.bat`: inicia la interfaz usando el Python del entorno `.venv` y
  deja la consola abierta al terminar.

### Módulos

- `modules/story_loader.py`: lee y separa título y cuerpo de las historias,
  evita seleccionar IDs ya usados y archiva los archivos terminados.
- `modules/downloader.py`: comprueba los gameplays y, cuando no hay ninguno,
  busca un vídeo nuevo en los canales configurados con `yt-dlp`.
- `modules/tts.py`: convierte el texto en audio con `edge-tts`; también permite
  listar voces en español con `python modules/tts.py --list-voices`.
- `modules/video_editor.py`: selecciona el tramo de fondo, conserva el progreso,
  transcribe el audio con Whisper, crea los subtítulos, renderiza y divide
  vídeos largos.
- `modules/publisher.py`: conserva los resultados de publicación local o los
  sube a YouTube mediante OAuth.
- `modules/__init__.py`: marca `modules` como paquete Python.

### Prueba auxiliar

- `test_subtitles.py`: crea imágenes de palabras de prueba para inspeccionar el
  recorte de los subtítulos sin ejecutar el pipeline ni cargar Whisper.
  Ejecútalo con `.\.venv\Scripts\python.exe test_subtitles.py`; genera imágenes
  en `test_output/`.

## 8. Carpetas y archivos de estado

- `assets/audio/`: narraciones MP3 generadas.
- `assets/gameplay/`: vídeos de fondo disponibles.
- `assets/used_gameplays/`: vídeos de fondo agotados.
- `assets/output/`: vídeos finales y partes generadas.
- `data/stories/`: historias pendientes.
- `data/stories/usadas/`: historias procesadas.
- `data/used_posts.json`: IDs de historias procesadas.
- `data/story_history.json`: historial de uso de historias.
- `data/video_progress.json`: segundo hasta el que se ha usado cada gameplay.
- `data/downloaded_archive.txt`: IDs de vídeos descargados con `yt-dlp`.
- `data/run_status.json`: estado de la última ejecución.
- `data/published_videos.json`: historial de intentos de publicación.
- `logs/`: registros diarios del pipeline.

No borres los archivos JSON de estado si quieres conservar el historial. Haz
una copia de seguridad antes de editarlos manualmente. Restaurar una historia
desde la interfaz también elimina su ID del registro de historias usadas para
permitir que vuelva a procesarse.

## 9. Solución de problemas

- **Falta FFmpeg o ImageMagick**: instala la herramienta, añádela a `PATH` y
  reinicia PowerShell o la aplicación.
- **No hay gameplay**: coloca un vídeo compatible en `assets/gameplay/` o añade
  URLs de canales a `data/channels.txt`.
- **No hay historias nuevas**: añade archivos `.txt` a `data/stories/` o
  restaura una historia usada desde la interfaz.
- **No se puede iniciar TTS o descargar**: comprueba la conexión a Internet y
  revisa el mensaje en la pestaña **Ejecución** y en el registro de `logs/`.
- **Whisper tarda o falla**: la primera ejecución puede descargar el modelo;
  comprueba la conexión, el espacio disponible y que PyTorch esté instalado.
- **La carga a YouTube falla**: comprueba `PUBLISH_PLATFORM`, las credenciales
  OAuth, la autorización y `data/published_videos.json`.
- **El subtítulo se recorta**: ejecuta `test_subtitles.py` y revisa las imágenes
  generadas antes de volver a ejecutar todo el pipeline.

Los archivos de registro más recientes se encuentran en `logs/`. La GUI muestra
la salida de la ejecución actual; `data/run_status.json` conserva su último
estado.

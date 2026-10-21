import subprocess  # Importa `subprocess` para utilizarlo en este archivo.
import sys  # Importa `sys` para utilizarlo en este archivo.
import time  # Importa `time` para utilizarlo en este archivo.
from datetime import datetime  # Importa los nombres necesarios desde `datetime`.
from pathlib import Path  # Importa los nombres necesarios desde `pathlib`.

PROJECT_ROOT = Path(__file__).resolve().parent  # Guarda en `PROJECT_ROOT` el resultado de `Path(__file__).resolve().parent`.
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"  # Guarda en `VENV_PYTHON` el resultado de `PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"`.

# Configuración del intervalo (ejemplo: cada 8 horas se lanzará un nuevo vídeo)
HOURS_INTERVAL = 8  # Guarda en `HOURS_INTERVAL` el resultado de `8`.
SECONDS_INTERVAL = HOURS_INTERVAL * 3600  # Guarda en `SECONDS_INTERVAL` el resultado de `HOURS_INTERVAL * 3600`.

print("=" * 60)  # Muestra en la consola el texto o resultado indicado.
print("🕒 PROGRAMADOR 24/7 — Bot de Vídeos Automatizado")  # Muestra en la consola el texto o resultado indicado.
print(f"✨ El bot se ejecutará automáticamente cada {HOURS_INTERVAL} horas.")  # Muestra en la consola el texto o resultado indicado.
print("⚠️ Deja esta ventana abierta en segundo plano. Para detenerlo, pulsa Ctrl + C.")  # Muestra en la consola el texto o resultado indicado.
print("=" * 60)  # Muestra en la consola el texto o resultado indicado.


def get_python_executable() -> str:  # Declara la funcion `get_python_executable` y especifica sus parametros y tipo de retorno.
    """Devuelve el intérprete de Python del entorno virtual si existe."""  # Ejecuta la operacion indicada por esta expresion.
    if VENV_PYTHON.exists():  # Solo ejecuta el bloque siguiente si se cumple `VENV_PYTHON.exists()`.
        return str(VENV_PYTHON)  # Devuelve `str(VENV_PYTHON)` al llamador y termina esta funcion.
    return sys.executable  # Devuelve `sys.executable` al llamador y termina esta funcion.


def run_bot():  # Declara la funcion `run_bot` y especifica sus parametros y tipo de retorno.
    """Ejecuta el script principal main.py de forma limpia."""  # Ejecuta la operacion indicada por esta expresion.
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Guarda en `current_time` el resultado de `datetime.now().strftime("%Y-%m-%d %H:%M:%S")`.
    print(f"\n🚀 [{current_time}] Iniciando ciclo automático del bot...")  # Muestra en la consola el texto o resultado indicado.
    print(f"🐍 Intérprete usado: {get_python_executable()}")  # Muestra en la consola el texto o resultado indicado.

    try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
        subprocess.run(  # Ejecuta el proceso o funcion indicado.
            [get_python_executable(), str(PROJECT_ROOT / "main.py")],  # Abre la agrupacion, lista o diccionario que se completa en las lineas siguientes.
            cwd=PROJECT_ROOT,  # Guarda en `cwd` el resultado de `PROJECT_ROOT,`.
            check=True,  # Guarda en `check` el resultado de `True,`.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Ciclo completado con éxito.")  # Muestra en la consola el texto o resultado indicado.
    except subprocess.CalledProcessError as e:  # Captura `subprocess.CalledProcessError as e` para gestionar el error en este bloque.
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] El ciclo encontró un error, pero el bucle continuará: {e}")  # Muestra en la consola el texto o resultado indicado.
    except Exception as e:  # Captura `Exception as e` para gestionar el error en este bloque.
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Error inesperado: {e}")  # Muestra en la consola el texto o resultado indicado.


# Primera ejecución inmediata al arrancar (opcional)
run_bot()  # Invoca `run_bot` con los argumentos indicados.

# Bucle infinito para mantener el bot activo 24/7
while True:  # Repite el bloque mientras se cumpla `True`.
    print(f"\n💤 Durmiendo... Próxima ejecución en {HOURS_INTERVAL} horas.")  # Muestra en la consola el texto o resultado indicado.
    try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
        time.sleep(SECONDS_INTERVAL)  # Pausa el proceso durante el intervalo indicado.
        run_bot()  # Invoca `run_bot` con los argumentos indicados.
    except KeyboardInterrupt:  # Captura `KeyboardInterrupt` para gestionar el error en este bloque.
        print("\n🛑 Programador detenido manualmente por el usuario.")  # Muestra en la consola el texto o resultado indicado.
        break  # Termina inmediatamente el bucle actual.
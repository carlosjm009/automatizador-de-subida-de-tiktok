import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

# Configuración del intervalo (ejemplo: cada 8 horas se lanzará un nuevo vídeo)
HOURS_INTERVAL = 8
SECONDS_INTERVAL = HOURS_INTERVAL * 3600

print("=" * 60)
print("🕒 PROGRAMADOR 24/7 — Bot de Vídeos Automatizado")
print(f"✨ El bot se ejecutará automáticamente cada {HOURS_INTERVAL} horas.")
print("⚠️ Deja esta ventana abierta en segundo plano. Para detenerlo, pulsa Ctrl + C.")
print("=" * 60)


def get_python_executable() -> str:
    """Devuelve el intérprete de Python del entorno virtual si existe."""
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable


def run_bot():
    """Ejecuta el script principal main.py de forma limpia."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n🚀 [{current_time}] Iniciando ciclo automático del bot...")
    print(f"🐍 Intérprete usado: {get_python_executable()}")

    try:
        subprocess.run(
            [get_python_executable(), str(PROJECT_ROOT / "main.py")],
            cwd=PROJECT_ROOT,
            check=True,
        )
        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Ciclo completado con éxito.")
    except subprocess.CalledProcessError as e:
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] El ciclo encontró un error, pero el bucle continuará: {e}")
    except Exception as e:
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Error inesperado: {e}")


# Primera ejecución inmediata al arrancar (opcional)
run_bot()

# Bucle infinito para mantener el bot activo 24/7
while True:
    print(f"\n💤 Durmiendo... Próxima ejecución en {HOURS_INTERVAL} horas.")
    try:
        time.sleep(SECONDS_INTERVAL)
        run_bot()
    except KeyboardInterrupt:
        print("\n🛑 Programador detenido manualmente por el usuario.")
        break
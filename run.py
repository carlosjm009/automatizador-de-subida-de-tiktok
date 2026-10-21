import sys  # Importa `sys` para utilizarlo en este archivo.
from pathlib import Path  # Importa los nombres necesarios desde `pathlib`.

ROOT = Path(__file__).resolve().parent  # Guarda en `ROOT` el resultado de `Path(__file__).resolve().parent`.
sys.path.insert(0, str(ROOT))  # Inserta el elemento o texto indicado en la interfaz.

from main import main  # Importa los nombres necesarios desde `main`.


if __name__ == "__main__":  # Solo ejecuta el bloque siguiente si se cumple `__name__ == "__main__"`.
    main()  # Invoca `main` con los argumentos indicados.
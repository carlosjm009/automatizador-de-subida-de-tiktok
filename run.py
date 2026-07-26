import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from main import main


def main_cli() -> None:
    parser = argparse.ArgumentParser(description="Lanzador del bot de Reddit Stories")
    parser.add_argument("--gui", action="store_true", help="abrir la interfaz gráfica en lugar del pipeline CLI")
    args = parser.parse_args()

    if args.gui:
        from app import RedditBotGUI

        app = RedditBotGUI()
        app.mainloop()
        return

    main()


if __name__ == "__main__":
    main_cli()

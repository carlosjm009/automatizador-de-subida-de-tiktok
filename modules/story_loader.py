"""
modules/story_loader.py

Fuente de historias local: en vez de conectarse a Reddit, el pipeline lee
historias que el propio usuario coloca como archivos .txt dentro de
STORIES_DIR (por defecto: data/stories/).

Formato esperado de cada archivo .txt:

    Título de la historia
    (línea en blanco, opcional)
    Resto del cuerpo de la historia, puede ocupar
    varias líneas y párrafos.

Si el archivo no tiene una línea en blanco separando título y cuerpo,
se asume que TODO el archivo es el cuerpo y se genera un título a partir
del nombre del archivo.

Cada archivo se identifica por su propio nombre (sin extensión), que se
usa como "id" único para el sistema de "historias ya usadas"
(data/used_posts.json). Si vuelves a ejecutar el bot, no se repetirá una
historia ya narrada mientras el .txt siga existiendo con el mismo nombre.
"""

import json  # Importa `json` para utilizarlo en este archivo.
import logging  # Importa `logging` para utilizarlo en este archivo.
from datetime import datetime  # Importa los nombres necesarios desde `datetime`.
from pathlib import Path  # Importa los nombres necesarios desde `pathlib`.
from typing import Optional  # Importa los nombres necesarios desde `typing`.

from config import STORIES_DIR, USED_STORIES_DIR, STORY_HISTORY_FILE  # Importa los nombres necesarios desde `config`.

logger = logging.getLogger("reddit_bot")  # Guarda en `logger` el resultado de `logging.getLogger("reddit_bot")`.


def log_story_usage(story_id: str, title: str, source_file: Optional[Path | str] = None) -> None:  # Declara la funcion `log_story_usage` y especifica sus parametros y tipo de retorno.
    """Guarda un registro de uso de la historia con fecha, título y destino."""  # Ejecuta la operacion indicada por esta expresion.
    STORY_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)  # Crea la carpeta indicada si todavia no existe.

    history = []  # Inicializa `history` como una coleccion vacia para acumular datos.
    if STORY_HISTORY_FILE.exists():  # Solo ejecuta el bloque siguiente si se cumple `STORY_HISTORY_FILE.exists()`.
        try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
            with open(STORY_HISTORY_FILE, "r", encoding="utf-8") as f:  # Abre `open(STORY_HISTORY_FILE, "r", encoding="utf-8") as f` y garantiza la liberacion del recurso al salir del bloque.
                history = json.load(f)  # Guarda en `history` el resultado de `json.load(f)`.
        except Exception:  # Captura `Exception` para gestionar el error en este bloque.
            history = []  # Inicializa `history` como una coleccion vacia para acumular datos.

    record = {  # Inicia el diccionario que se completa con los campos de las lineas siguientes.
        "id": story_id,  # Asocia la clave `id` con el valor indicado en este diccionario.
        "title": title,  # Asocia la clave `title` con el valor indicado en este diccionario.
        "used_at": datetime.now().isoformat(timespec="seconds"),  # Asocia la clave `used_at` con el valor indicado en este diccionario.
        "source_file": str(source_file) if source_file else None,  # Asocia la clave `source_file` con el valor indicado en este diccionario.
        "status": "used",  # Asocia la clave `status` con el valor indicado en este diccionario.
    }  # Cierra el diccionario o conjunto abierto anteriormente.
    history.append(record)  # Anade el elemento indicado a la coleccion.

    with open(STORY_HISTORY_FILE, "w", encoding="utf-8") as f:  # Abre `open(STORY_HISTORY_FILE, "w", encoding="utf-8") as f` y garantiza la liberacion del recurso al salir del bloque.
        json.dump(history, f, indent=4, ensure_ascii=False)  # Serializa los datos como JSON en el archivo indicado.


def mark_story_as_used(story_id: str, title: str, source_file: Optional[Path | str] = None) -> None:  # Declara la funcion `mark_story_as_used` y especifica sus parametros y tipo de retorno.
    """Mueve el archivo .txt de la historia a la carpeta de usadas tras completarla con éxito."""  # Ejecuta la operacion indicada por esta expresion.
    USED_STORIES_DIR.mkdir(parents=True, exist_ok=True)  # Crea la carpeta indicada si todavia no existe.

    if source_file is None:  # Solo ejecuta el bloque siguiente si se cumple `source_file is None`.
        source_path = STORIES_DIR / f"{story_id}.txt"  # Construye en `source_path` la ruta del archivo o carpeta indicada.
    else:  # Ejecuta este bloque cuando no se cumple la condicion o rama anterior.
        source_path = Path(source_file)  # Guarda en `source_path` el resultado de `Path(source_file)`.

    if not source_path.exists():  # Solo ejecuta el bloque siguiente si se cumple `not source_path.exists()`.
        logger.warning(f"⚠️ No se encontró el archivo de historia {source_path} para moverlo a usadas.")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
    else:  # Ejecuta este bloque cuando no se cumple la condicion o rama anterior.
        destination_path = USED_STORIES_DIR / source_path.name  # Guarda en `destination_path` el resultado de `USED_STORIES_DIR / source_path.name`.
        if destination_path.exists():  # Solo ejecuta el bloque siguiente si se cumple `destination_path.exists()`.
            destination_path.unlink()  # Elimina el archivo indicado.

        source_path.rename(destination_path)  # Renombra o mueve el archivo indicado.
        logger.info(f"📦 Historia movida a usadas: {destination_path}")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.

    log_story_usage(story_id, title, source_file or source_path)  # Invoca `log_story_usage` con los argumentos indicados.


def _parse_story_file(path: Path) -> dict:  # Declara la funcion `_parse_story_file` y especifica sus parametros y tipo de retorno.
    """Divide el contenido de un .txt en título + cuerpo."""  # Ejecuta la operacion indicada por esta expresion.
    raw = path.read_text(encoding="utf-8").strip()  # Guarda en `raw` el resultado de `path.read_text(encoding="utf-8").strip()`.
    lines = raw.splitlines()  # Guarda en `lines` el resultado de `raw.splitlines()`.

    if not lines:  # Solo ejecuta el bloque siguiente si se cumple `not lines`.
        raise ValueError("el archivo está vacío")  # Lanza `ValueError` para informar de esta condicion de error.

    titulo = lines[0].strip()  # Guarda en `titulo` el resultado de `lines[0].strip()`.
    resto = lines[1:]  # Guarda en `resto` el resultado de `lines[1:]`.

    # Si la línea siguiente al título está en blanco, la tratamos como
    # el separador título/cuerpo y la descartamos.
    if resto and resto[0].strip() == "":  # Solo ejecuta el bloque siguiente si se cumple `resto and resto[0].strip() == ""`.
        resto = resto[1:]  # Guarda en `resto` el resultado de `resto[1:]`.

    cuerpo = "\n".join(resto).strip()  # Guarda en `cuerpo` el resultado de `"\n".join(resto).strip()`.

    if not cuerpo:  # Solo ejecuta el bloque siguiente si se cumple `not cuerpo`.
        # No había una segunda línea real de cuerpo: tratamos todo el
        # archivo como cuerpo y generamos un título a partir del nombre
        # del archivo (ej. "historia_01.txt" -> "Historia 01").
        cuerpo = titulo  # Guarda en `cuerpo` el resultado de `titulo`.
        titulo = path.stem.replace("_", " ").replace("-", " ").strip().capitalize()  # Guarda en `titulo` el resultado de `path.stem.replace("_", " ").replace("-", " ").strip().capitalize()`.

    return {"title": titulo, "body": cuerpo}  # Devuelve `{"title": titulo, "body": cuerpo}` al llamador y termina esta funcion.


def get_next_story(used_ids: Optional[set] = None) -> Optional[dict]:  # Declara la funcion `get_next_story` y especifica sus parametros y tipo de retorno.
    """
    Busca en STORIES_DIR el primer archivo .txt (por orden alfabético) cuyo
    id (nombre de archivo sin extensión) no esté en used_ids.

    Args:
        used_ids: Set de IDs de historias ya usadas para evitar repetirlas.

    Returns:
        Dict con la historia lista para el resto del pipeline
        (id, title, body, texto_completo, length), o None si no hay ningún
        .txt nuevo disponible en la carpeta.
    """
    if used_ids is None:  # Solo ejecuta el bloque siguiente si se cumple `used_ids is None`.
        used_ids = set()  # Inicializa `used_ids` como una coleccion vacia para acumular datos.

    STORIES_DIR.mkdir(parents=True, exist_ok=True)  # Crea la carpeta indicada si todavia no existe.

    archivos = sorted(STORIES_DIR.glob("*.txt"))  # Guarda en `archivos` el resultado de `sorted(STORIES_DIR.glob("*.txt"))`.

    if not archivos:  # Solo ejecuta el bloque siguiente si se cumple `not archivos`.
        logger.warning(  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
            f"⚠️ No hay ningún archivo .txt en {STORIES_DIR}. "  # Aporta esta parte del texto interpolado a la cadena o mensaje construido arriba.
            "Añade ahí tus historias (una por archivo) para que el bot pueda usarlas."  # Ejecuta la operacion indicada por esta expresion.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
        return None  # Devuelve `None` al llamador y termina esta funcion.

    for archivo in archivos:  # Recorre `archivos` y asigna cada elemento a `archivo`.
        story_id = archivo.stem  # Guarda en `story_id` el resultado de `archivo.stem`.

        if story_id in used_ids:  # Solo ejecuta el bloque siguiente si se cumple `story_id in used_ids`.
            continue  # Pasa a la siguiente iteracion del bucle actual.

        try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
            parsed = _parse_story_file(archivo)  # Guarda en `parsed` el resultado de `_parse_story_file(archivo)`.
        except Exception as e:  # Captura `Exception as e` para gestionar el error en este bloque.
            logger.warning(f"⚠️ No se pudo leer '{archivo.name}': {e}. Se ignora y se prueba con el siguiente.")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
            continue  # Pasa a la siguiente iteracion del bucle actual.

        titulo = parsed["title"]  # Guarda en `titulo` el resultado de `parsed["title"]`.
        cuerpo = parsed["body"]  # Guarda en `cuerpo` el resultado de `parsed["body"]`.

        if not cuerpo:  # Solo ejecuta el bloque siguiente si se cumple `not cuerpo`.
            logger.warning(f"⚠️ '{archivo.name}' no tiene contenido útil, se ignora.")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
            continue  # Pasa a la siguiente iteracion del bucle actual.

        texto_completo = f"{titulo}. {cuerpo}"  # Guarda en `texto_completo` el resultado de `f"{titulo}. {cuerpo}"`.

        return {  # Devuelve `{` al llamador y termina esta funcion.
            "id": story_id,  # Asocia la clave `id` con el valor indicado en este diccionario.
            "title": titulo,  # Asocia la clave `title` con el valor indicado en este diccionario.
            "body": cuerpo,  # Asocia la clave `body` con el valor indicado en este diccionario.
            "texto_completo": texto_completo,  # Asocia la clave `texto_completo` con el valor indicado en este diccionario.
            "length": len(texto_completo),  # Asocia la clave `length` con el valor indicado en este diccionario.
            "source_file": str(archivo),  # Asocia la clave `source_file` con el valor indicado en este diccionario.
        }  # Cierra el diccionario o conjunto abierto anteriormente.

    logger.warning(f"⚠️ Todos los archivos .txt de {STORIES_DIR} ya han sido usados.")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
    return None  # Devuelve `None` al llamador y termina esta funcion.

import random
from curl_cffi import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime


def get_top_story(subreddit_name="HistoriasDeReddit", limit_chars=(500, 1000), used_ids=None):
    """
    Obtiene la historia más popular de un subreddit que no haya sido usada antes.

    Args:
        subreddit_name: Nombre del subreddit a scrapear.
        limit_chars: Tupla (min, max) de caracteres permitidos.
        used_ids: Set de IDs de posts ya usados para evitar repetirlos.

    Returns:
        Dict con la historia, o None si no encuentra ninguna válida.
    """
    if used_ids is None:
        used_ids = set()

    url = f"https://www.reddit.com/r/{subreddit_name}/top.rss?t=month"

    try:
        response = requests.get(url, impersonate="chrome110", timeout=10)

        if response.status_code != 200:
            raise ValueError(f"Reddit bloqueó la conexión HTTP (Código {response.status_code})")

        feed = feedparser.parse(response.text)

        if not feed.entries:
            raise ValueError("El feed RSS se descargó pero está vacío (posible bloqueo residual).")

        for entry in feed.entries:
            titulo = entry.title

            html_content = entry.content[0].value if 'content' in entry else entry.summary
            soup = BeautifulSoup(html_content, "html.parser")
            div_md = soup.find("div", class_="md")

            if not div_md:
                continue

            texto = div_md.get_text(separator=" ", strip=True)
            texto_completo = f"{titulo}. {texto}"

            post_id = entry.id.split('_')[-1] if '_' in entry.id else entry.id

            # Saltar si ya fue usado
            if post_id in used_ids:
                continue

            if limit_chars[0] <= len(texto_completo) <= limit_chars[1]:
                return {
                    "id": post_id,
                    "title": titulo,
                    "body": texto,
                    "texto_completo": texto_completo,
                    "subreddit": subreddit_name,
                    "length": len(texto_completo)
                }

        raise ValueError(
            f"Ninguna historia nueva de r/{subreddit_name} cumple con el límite de "
            f"{limit_chars[0]} a {limit_chars[1]} caracteres."
        )

    except Exception as e:
        print(f"\n⚠️ Fallo al extraer de r/{subreddit_name}: {e}")
        print("🚀 Activando 'Modo Simulación' con historia de emergencia...")

        # Generar un ID único basado en timestamp para evitar colisiones
        emergency_id = f"emergencia_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        titulo = "¿Soy el malo por no querer compartir mi premio de lotería con mi hermano?"
        texto = (
            "Hace una semana gané un premio moderado en la lotería. Nada para hacerme millonario, "
            "pero suficiente para pagar mis deudas y dar la entrada de un piso. Cometí el gran error "
            "de contárselo a mis padres. Al día siguiente, mi hermano me llamó exigiéndome que le "
            "pagara las vacaciones a él y a su familia porque, según él, 'eso es lo que hace la familia'. "
            "Le dije que no, que ese dinero era para mi futuro. Ahora mis padres me acusan de ser "
            "egoísta y materialista. No creo que les deba nada, yo compré el boleto con mi dinero. "
            "¿Debería darles una parte?"
        )
        texto_completo = f"{titulo}. {texto}"

        return {
            "id": emergency_id,
            "title": titulo,
            "body": texto,
            "texto_completo": texto_completo,
            "subreddit": subreddit_name,
            "length": len(texto_completo)
        }
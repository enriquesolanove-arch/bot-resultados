import os
import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
string_session = os.environ["TELEGRAM_STRING_SESSION"]
GITHUB_TOKEN = os.environ.get("TOKEN_GIST", "")

GIST_ID = "9fb0808d7249cbc473da64ac11ba88d1"
CANAL = 'pronosticosparahoy'

client = TelegramClient(StringSession(string_session), api_id, api_hash)


# ═══════════════════════════════════════════════════════════
#  LISTA DE ANIMALES DEL LOTTO ACTIVO
# ═══════════════════════════════════════════════════════════
ANIMALES = [
    'ballena', 'delfin', 'delfín', 'carnero', 'toro', 'ciempies', 'ciempiés',
    'alacran', 'alacrán', 'leon', 'león', 'rana', 'perico', 'raton', 'ratón',
    'aguila', 'águila', 'tigre', 'tigresa', 'gato', 'caballo', 'mono', 'paloma',
    'zorro', 'oso', 'pavo', 'burro', 'chivo', 'cochino', 'gallo', 'camello',
    'cebra', 'iguana', 'gallina', 'vaca', 'perro', 'zamuro', 'elefante',
    'caiman', 'caimán', 'lapa', 'ardilla', 'pescado', 'venado', 'jirafa',
    'culebra', 'ballenas', 'cachicamo', 'guacharito', 'guacharo', 'guácharo'
]

# Palabras que indican que el mensaje NO es un pronóstico (basura)
EXCLUIR = [
    # Otras agencias
    'rodacadiz', 'gogoroyal', 'gogo royal', 'elparcero', 'el parcero',
    'jugabet', 'juga bet', 'somos tu mejor opcion', 'somos tu mejor opción',
    'agencia de loteria', 'agencia de lotería', 'nuestra agencia',
    'nuestro canal', 'nuestro grupo', 'nuestra pagina', 'nuestra página',
    # Links promocionales
    'wa.me', 't.me/', 'bit.ly', 'http://', 'https://',
    'registrate', 'regístrate', 'activa tu bono', 'unete', 'únete',
    'unirse', 'unirte', 'comparte y gana', 'compartir y unirte',
    'dale like', 'comenta el animalito', 'menciona a tres',
    'pasos a seguir',
    # Deportes
    'copa libertadores', 'flamengo', 'estudiantes de la plata',
    'real madrid', 'vinicius', 'villareal', 'barquisimeto', 'cardenales',
    'tiburones', 'lvbp', 'liga ', 'partido de ida', 'semifinal',
    'goles', 'futbol', 'fútbol', 'beisbol', 'béisbol', 'mundial',
    'champions', 'premier', 'la liga', 'serie a',
    # Finanzas / otras cosas
    'binance', 'usdt', 'criptomoneda', 'bitcoin',
    # Mega pollas y publicidad
    'mega polla', 'mega-polla', 'sorteo especial', 'premio mayor',
    # Triples/Chance (ya que solo queremos animalitos)
    'triple zulia', 'triple tachira', 'triple táchira', 'triple zamorano',
    'triple caracas', 'triple carabobo', 'el ruco', 'la ruca', 'chance',
    'triple chance', 'triples y parleys'
]


def esc(texto):
    return texto.lower()


def es_basura(texto):
    """Verifica si el mensaje contiene palabras de exclusión."""
    t = texto.lower()
    for p in EXCLUIR:
        if p in t:
            return True
    return False


def contar_animales(texto):
    """Cuenta cuántos animales del listado aparecen en el texto."""
    t = texto.lower()
    # Reemplazar tildes para mejor matching
    t = t.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    count = 0
    encontrados = []
    for a in ANIMALES:
        a_limpio = a.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        # Buscar palabra completa
        patron = r'\b' + re.escape(a_limpio) + r'\b'
        if re.search(patron, t):
            count += 1
            encontrados.append(a)
    return count, encontrados


def es_pronostico(texto):
    """Determina si el mensaje es un pronóstico real de animalitos."""
    if es_basura(texto):
        return False

    t = texto.lower()

    # Verificar si menciona las ruletas objetivo
    menciona_ruleta = any(k in t for k in [
        'lotto activo', 'la granjita', 'guacharo', 'guácharo',
        'selva plus', 'lotto real', 'granjita plus'
    ])

    # Contar animales
    cant_animales, animales = contar_animales(texto)

    # Criterios:
    # 1. Al menos 3 animales mencionados → es un pronóstico
    # 2. O menciona ruleta + al menos 1 animal → es un pronóstico
    if cant_animales >= 3:
        return True
    if menciona_ruleta and cant_animales >= 1:
        return True

    return False


def subir_a_gist(lista):
    if not GITHUB_TOKEN:
        print("TOKEN_GIST no configurado")
        return False
    contenido = "window.PRONOSTICOS = " + json.dumps(lista, ensure_ascii=False) + ";"
    url = f"https://api.github.com/gists/{GIST_ID}"
    data = json.dumps({
        "files": {"pronosticos.js": {"content": contenido}}
    }).encode("utf-8")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "bot"
    }
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="PATCH")
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"Gist actualizado: {len(lista)} pronosticos")
            return True
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} - {e.read().decode()[:200]}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


async def extraer():
    ahora_ven = datetime.utcnow() - timedelta(hours=4)
    hoy = ahora_ven.strftime('%Y-%m-%d')

    print(f"Fecha hoy: {hoy}")

    pronosticos = []
    vistos = set()
    basura_count = 0
    examinados = 0

    async for msg in client.iter_messages(CANAL, limit=150):
        if not msg.text:
            continue

        texto = msg.text.strip()
        examinados += 1

        # Deduplicar por primeros 80 caracteres
        clave = texto[:80].lower()
        if clave in vistos:
            continue
        vistos.add(clave)

        # Filtrar por fecha (solo hoy)
        fecha_msg = (msg.date - timedelta(hours=4)).strftime('%Y-%m-%d')
        if fecha_msg != hoy:
            continue

        # Verificar si es pronóstico
        if not es_pronostico(texto):
            basura_count += 1
            continue

        # Cantidad de animales encontrados (para debug)
        cant, animales_encontrados = contar_animales(texto)

        pronosticos.append({
            "tipo": "animalitos",
            "texto": texto,
            "fecha": hoy,
            "hora_publicacion": (msg.date - timedelta(hours=4)).strftime('%H:%M'),
            "animales": cant
        })

    # Ordenar por hora descendente (más reciente primero)
    pronosticos.sort(key=lambda x: x['hora_publicacion'], reverse=True)
    # Máximo 40
    pronosticos = pronosticos[:40]

    print(f"Mensajes examinados: {examinados}")
    print(f"Mensajes descartados: {basura_count}")
    print(f"Pronosticos validos: {len(pronosticos)}")
    for p in pronosticos[:5]:
        print(f"  [{p['hora_publicacion']}] {p['animales']} animales: {p['texto'][:80]}")

    subir_a_gist(pronosticos)


async def main():
    async with client:
        print("Conectado a Telegram...")
        await extraer()


if __name__ == "__main__":
    client.loop.run_until_complete(main())

import os
import json
import re
import unicodedata
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
#  ANIMALES (sin duplicados por tildes - normalizados)
# ═══════════════════════════════════════════════════════════
ANIMALES = [
    'ballena', 'delfin', 'carnero', 'toro', 'ciempies', 'alacran',
    'leon', 'rana', 'perico', 'raton', 'aguila', 'tigre', 'tigresa',
    'gato', 'caballo', 'mono', 'paloma', 'zorro', 'oso', 'pavo',
    'burro', 'chivo', 'cochino', 'gallo', 'camello', 'cebra',
    'iguana', 'gallina', 'vaca', 'perro', 'zamuro', 'elefante',
    'caiman', 'lapa', 'ardilla', 'pescado', 'venado', 'jirafa',
    'culebra', 'cachicamo', 'guacharito', 'guacharo', 'morochos'
]

# Palabras que indican que NO es un pronóstico
EXCLUIR = [
    # Otras agencias
    'rodacadiz', 'gogoroyal', 'gogo royal', 'elparcero', 'el parcero',
    'jugabet', 'juga bet', 'somos tu mejor', 'agencia de loteria',
    'agencia de lotería',
    # Links promocionales
    'wa.me', 't.me/', 'bit.ly', 'http://', 'https://',
    'registrate', 'regístrate', 'activa tu bono', 'unirse', 'unirte',
    'comparte y gana', 'compartir y unirte', 'dale like',
    'comenta el animalito', 'menciona a tres', 'pasos a seguir',
    # Deportes
    'copa libertadores', 'flamengo', 'estudiantes de la plata',
    'real madrid', 'vinicius', 'villareal', 'barquisimeto', 'cardenales',
    'tiburones', 'lvbp', 'partido de ida', 'semifinal', 'goles',
    'futbol', 'fútbol', 'beisbol', 'béisbol', 'mundial', 'champions',
    'premier', 'la liga', 'serie a', 'copa ', 'goleada',
    'clasificación', 'clasificacion',
    # Finanzas
    'binance', 'usdt', 'bitcoin',
    # Mega pollas
    'mega polla', 'mega-polla', 'sorteo especial', 'premio mayor',
    # Triples/Chance (solo queremos animalitos)
    'triple zulia', 'triple tachira', 'triple táchira', 'triple zamorano',
    'triple caracas', 'triple carabobo', 'el ruco', 'la ruca',
    'triple chance', 'triples y parleys', 'terminales y parleys',
    # Ruletas NO objetivo
    'la ricachona', 'lotto gato', 'lotto pantera', 'gatazo',
    'chance animal', 'tropigana', 'fruitagana', 'granjazo',
    'panda plus', 'mega animal', 'monje millonario', 'zoologico activo'
]


def norm(texto):
    """Normaliza texto: minúsculas y sin tildes."""
    texto = texto.lower()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


def es_basura(texto):
    t = norm(texto)
    for p in EXCLUIR:
        if norm(p) in t:
            return True
    return False


def contar_animales(texto):
    """Cuenta animales únicos (sin duplicados por tildes)."""
    t = norm(texto)
    encontrados = set()
    for a in ANIMALES:
        a_norm = norm(a)
        patron = r'\b' + re.escape(a_norm) + r'\b'
        if re.search(patron, t):
            encontrados.add(a_norm)
    return len(encontrados), list(encontrados)


# Ruletas que SÍ queremos (todas sus variantes)
RULETAS_OK = [
    'lotto activo', 'lottoactivo', 'lotto activo rd', 'lotto activo r',
    'la granjita', 'lagranjita', 'granjita plus', 'granjita',
    'guacharo', 'guácharo', 'el guacharito', 'guacharito',
    'guacharito millonario',
    'selva plus', 'selvaplus', 'selva',
    'lotto real', 'lottoreal',
    'ruleta activa', 'ruletaactiva',
    'granja millonaria', 'granjamillonaria'
]


def menciona_ruleta_ok(texto):
    t = norm(texto)
    for r in RULETAS_OK:
        if norm(r) in t:
            return True
    return False


def es_pronostico(texto):
    """Determina si el mensaje es un pronóstico válido."""
    if es_basura(texto):
        return False

    cant_animales, lista = contar_animales(texto)
    tiene_ruleta = menciona_ruleta_ok(texto)

    # Reglas MÁS flexibles:
    # 1. Si menciona ruleta OK y tiene 1+ animales → válido
    # 2. Si tiene 2+ animales aunque no mencione ruleta → válido
    # 3. Si tiene 1 animal + algún número de 2 dígitos → válido
    if tiene_ruleta and cant_animales >= 1:
        return True
    if cant_animales >= 2:
        return True
    if cant_animales >= 1 and re.search(r'\b\d{2}\b', texto):
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

    # Últimos 3 días (hoy, ayer, antes de ayer)
    fechas_ok = []
    for i in range(3):
        d = ahora_ven - timedelta(days=i)
        fechas_ok.append(d.strftime('%Y-%m-%d'))
    print(f"Fechas aceptadas: {fechas_ok}")

    pronosticos = []
    vistos = set()
    basura_count = 0
    examinados = 0

    async for msg in client.iter_messages(CANAL, limit=200):
        if not msg.text:
            continue
        texto = msg.text.strip()
        examinados += 1

        # Deduplicar
        clave = norm(texto[:80])
        if clave in vistos:
            continue
        vistos.add(clave)

                # Últimos 3 días
        fecha_msg = (msg.date - timedelta(hours=4)).strftime('%Y-%m-%d')
        if fecha_msg not in fechas_ok:
            continue

        # Verificar pronóstico
        if not es_pronostico(texto):
            basura_count += 1
            continue

        cant, animales = contar_animales(texto)

        pronosticos.append({
            "tipo": "animalitos",
            "texto": texto,
            "fecha": hoy,
            "hora_publicacion": (msg.date - timedelta(hours=4)).strftime('%H:%M'),
            "animales": cant
        })

    pronosticos.sort(key=lambda x: x['hora_publicacion'], reverse=True)
    pronosticos = pronosticos[:40]

    print(f"Mensajes examinados: {examinados}")
    print(f"Mensajes descartados: {basura_count}")
    print(f"Pronosticos validos: {len(pronosticos)}")
    print("")
    print("--- Lista de pronosticos validos ---")
    for p in pronosticos:
        print(f"[{p['hora_publicacion']}] {p['animales']} animales: {p['texto'][:100]}")

    subir_a_gist(pronosticos)


async def main():
    async with client:
        print("Conectado a Telegram...")
        await extraer()


if __name__ == "__main__":
    client.loop.run_until_complete(main())

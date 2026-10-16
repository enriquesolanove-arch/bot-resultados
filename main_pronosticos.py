import os
import json
import re
import random
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


BLOQUES = [
    {'key': 'manana',   'limite': 6 * 60 + 30},   # 6:30 AM
    {'key': 'mediodia', 'limite': 12 * 60 + 30},  # 12:30 PM
    {'key': 'cierre',   'limite': 17 * 60 + 30}   # 5:30 PM
]

RULETAS = [
    {'key': 'Lotto Activo',    'max': 36, 'cantidad': 4, 'aliases': ['lotto activo', 'lottoactivo']},
    {'key': 'La Granjita',     'max': 36, 'cantidad': 4, 'aliases': ['la granjita', 'lagranjita', 'granjita']},
    {'key': 'Guacharo Activo', 'max': 75, 'cantidad': 5, 'aliases': ['guacharo', 'guácharo', 'guacharo activo', 'el guacharito']}
]

EXCLUIR = [
    'rodacadiz', 'gogoroyal', 'gogo royal', 'elparcero', 'el parcero',
    'jugabet', 'somos tu mejor', 'agencia de loteria', 'agencia de lotería',
    'wa.me', 't.me/', 'bit.ly', 'registrate', 'regístrate', 'activa tu bono',
    'unirse', 'unirte', 'dale like', 'comenta el animalito', 'menciona a tres',
    'instagram.com', 'youtube.com', 'youtu.be', 'facebook.com',
    'tasa bcv', 'tasa del bcv', 'bcv', 'dolar hoy', 'dólar hoy',
    'tasa de cambio', 'binance', 'usdt', 'bitcoin',
    'copa libertadores', 'real madrid', 'flamengo', 'lvbp', 'tiburones',
    'futbol', 'fútbol', 'beisbol', 'béisbol', 'champions',
    'mega polla', 'sorteo especial', 'comparte', 'reacciona', 'suscripte',
    'triple', 'triples', 'terminal', 'parley', 'chance'
]


def norm(texto):
    texto = str(texto).lower()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')


def es_basura(texto):
    t = norm(texto)
    for p in EXCLUIR:
        if norm(p) in t:
            return True
    return False


def detectar_ruleta(texto):
    t = norm(texto)
    for r in RULETAS:
        for alias in r['aliases']:
            if norm(alias) in t:
                return r
    return None


def extraer_numeros(texto, maximo):
    nums = []
    nums += re.findall(r'\*(\d{1,2})\*', texto)
    nums += re.findall(r'\*(\d{1,2})\s+[a-záéíóúñ]{3,}', norm(texto))
    nums += re.findall(r'\b(\d{1,2})\s+[a-záéíóúñ]{4,}\b', norm(texto))
    nums += re.findall(r'\b(\d{1,2})(?=[\-\/\.])', texto)

    validos = []
    vistos = set()
    for n in nums:
        try:
            num = int(n)
        except:
            continue
        if num < 0 or num > maximo:
            continue
        num_str = str(num).zfill(2)
        if num_str in vistos:
            continue
        vistos.add(num_str)
        validos.append(num_str)
    return validos


def clasificar_bloque(hora):
    h = hora.hour
    if 6 <= h < 12: return 'manana'
    if 12 <= h < 17: return 'mediodia'
    if 17 <= h < 20: return 'cierre'
    return None


def generar_aleatorios(maximo, cantidad):
    """Genera N números únicos aleatorios entre 0 y maximo."""
    pool = list(range(0, maximo + 1))
    random.shuffle(pool)
    elegidos = sorted(pool[:cantidad])
    return [str(n).zfill(2) for n in elegidos]


def descargar_gist():
    """Descarga el Gist actual."""
    url = f"https://api.github.com/gists/{GIST_ID}?t={int(datetime.utcnow().timestamp())}"
    headers = {"User-Agent": "bot"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
        content = data['files']['pronosticos.js']['content']
        # Extraer JSON
        match = re.search(r'window\.REGALOS\s*=\s*(\{.*\});', content, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except Exception as e:
        print(f"Error descargando Gist: {e}")
    return None


def subir_gist(data):
    if not GITHUB_TOKEN:
        print("TOKEN_GIST no configurado")
        return False
    contenido = "window.REGALOS = " + json.dumps(data, ensure_ascii=False) + ";"
    url = f"https://api.github.com/gists/{GIST_ID}"
    body = json.dumps({"files": {"pronosticos.js": {"content": contenido}}}).encode("utf-8")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "bot"
    }
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="PATCH")
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"Gist actualizado")
            return True
    except Exception as e:
        print(f"Error subiendo: {e}")
        return False


def inicializar_estructura():
    """Crea la estructura base."""
    est = {}
    for r in RULETAS:
        est[r['key']] = {}
        for b in BLOQUES:
            est[r['key']][b['key']] = {'nums': [], 'fuente': '', 'hora': ''}
    return est


async def extraer():
    ahora_ven = datetime.utcnow() - timedelta(hours=4)
    hoy = ahora_ven.strftime('%Y-%m-%d')
    min_ahora = ahora_ven.hour * 60 + ahora_ven.minute

    print(f"Fecha hoy: {hoy}")
    print(f"Hora actual (Venezuela): {ahora_ven.strftime('%H:%M')}")

    # Leer Gist actual
    data = descargar_gist()
    if not data or data.get('fecha') != hoy:
        data = {'fecha': hoy, 'bloques': inicializar_estructura()}
    if 'bloques' not in data:
        data['bloques'] = inicializar_estructura()

    # Asegurar estructura completa
    for r in RULETAS:
        if r['key'] not in data['bloques']:
            data['bloques'][r['key']] = {}
        for b in BLOQUES:
            if b['key'] not in data['bloques'][r['key']]:
                data['bloques'][r['key']][b['key']] = {'nums': [], 'fuente': '', 'hora': ''}

    # ═══════════════════════════════════════════════════════
    #  1. GENERAR ALEATORIOS si no hay manual
    # ═══════════════════════════════════════════════════════
    generados = 0
    for r in RULETAS:
        for b in BLOQUES:
            info = data['bloques'][r['key']][b['key']]
            if info['fuente'] == 'manual':
                continue  # respetar manual
            if min_ahora >= b['limite'] and not info['nums']:
                # Generar aleatorios
                info['nums'] = generar_aleatorios(r['max'], r['cantidad'])
                info['fuente'] = 'auto'
                info['hora'] = ahora_ven.strftime('%H:%M')
                generados += 1
                print(f"  🤖 Generados aleatorios para {r['key']} - {b['key']}: {info['nums']}")

    # ═══════════════════════════════════════════════════════
    #  2. CAPTURAR DE TELEGRAM
    # ═══════════════════════════════════════════════════════
    capturados_telegram = 0
    async for msg in client.iter_messages(CANAL, limit=100):
        if not msg.text:
            continue
        texto = msg.text.strip()
        if es_basura(texto):
            continue

        # Solo hoy
        fecha_msg = (msg.date - timedelta(hours=4)).strftime('%Y-%m-%d')
        if fecha_msg != hoy:
            continue

        ruleta = detectar_ruleta(texto)
        if not ruleta:
            continue

        nums = extraer_numeros(texto, ruleta['max'])
        if not nums:
            continue

        # Clasificar bloque
        hora_local = msg.date - timedelta(hours=4)
        bloque = clasificar_bloque(hora_local)
        if not bloque:
            continue

        # Solo usar telegram si no hay manual para ese bloque
        info = data['bloques'][ruleta['key']][bloque]
        if info['fuente'] == 'manual':
            continue  # el manual tiene prioridad

        # Si está vacío, usar telegram
        if not info['nums']:
            info['nums'] = nums[:ruleta['cantidad']]
            info['fuente'] = 'telegram'
            info['hora'] = hora_local.strftime('%H:%M')
            capturados_telegram += 1

    data['actualizado'] = ahora_ven.strftime('%d/%m/%Y %H:%M')

    print(f"")
    print(f"🤖 Generados aleatorios: {generados}")
    print(f"📡 Capturados de Telegram: {capturados_telegram}")

    # Mostrar resumen
    for r in RULETAS:
        print(f"\n{r['key']}:")
        for b in BLOQUES:
            info = data['bloques'][r['key']][b['key']]
            fuente = info['fuente'] or 'vacío'
            nums = ', '.join(info['nums']) if info['nums'] else '—'
            print(f"  {b['key']}: [{fuente}] {nums}")

    subir_gist(data)


async def main():
    async with client:
        print("Conectado a Telegram...")
        await extraer()


if __name__ == "__main__":
    client.loop.run_until_complete(main())

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
#  CATÁLOGO COMPLETO DE ANIMALES (1-75)
# ═══════════════════════════════════════════════════════════
ANIMALES = [
    # 0-36 Lotto Activo / La Granjita
    'ballena', 'delfin', 'carnero', 'toro', 'ciempies', 'alacran',
    'leon', 'rana', 'perico', 'raton', 'aguila', 'tigre', 'tigresa',
    'gato', 'caballo', 'mono', 'paloma', 'zorro', 'oso', 'pavo',
    'burro', 'chivo', 'cochino', 'gallo', 'camello', 'cebra',
    'iguana', 'gallina', 'vaca', 'perro', 'zamuro', 'elefante',
    'caiman', 'lapa', 'ardilla', 'pescado', 'venado', 'jirafa',
    'culebra', 'cachicamo', 'guacharito', 'guacharo', 'morochos',
    # 37-75 Granjazo / Granja Millonaria / otros
    'bufalo', 'pelicano', 'jabali', 'morza', 'morsa', 'hormiga',
    'comadreja', 'murcielago', 'tortuga', 'mariposa', 'panda', 'buho',
    'puercoespin', 'avestruz', 'conejo', 'canguro', 'koala', 'pinguino',
    'tiburon', 'ballenas', 'pulpo', 'cangrejo', 'langosta', 'foca',
    'lobo', 'hiena', 'pantera', 'leopardo', 'puma', 'rinoceronte',
    'hipopotamo', 'jaguar', 'cocodrilo', 'serpiente', 'aguila real',
    'halcon', 'cuervo', 'loro', 'guacamaya', 'tucan', 'flamenco',
    'pavo real', 'cisne', 'ganso', 'pato', 'gallito', 'faisan'
]

# ═══════════════════════════════════════════════════════════
#  RULETAS DE ANIMALITOS
# ═══════════════════════════════════════════════════════════
RULETAS_ANIMALES = [
    'lotto activo', 'lottoactivo', 'lotto activo rd', 'lotto activo r',
    'la granjita', 'lagranjita', 'granjita plus', 'granjita',
    'guacharo', 'guácharo', 'el guacharito', 'guacharito',
    'guacharito millonario',
    'selva plus', 'selvaplus', 'selva',
    'lotto real', 'lottoreal',
    'ruleta activa', 'ruletaactiva',
    'granja millonaria', 'granjamillonaria', 'granja millonaria',
    'granjazo', 'lotto rey', 'lottorey', 'lotto gato', 'lottogato',
    'lotto pantera', 'centena animal', 'centena plus',
    'mega animal', 'chance animal', 'tropigana', 'fruitagana',
    'panda plus', 'ricachona', 'la ricachona'
]

# ═══════════════════════════════════════════════════════════
#  RULETAS DE TRIPLES
# ═══════════════════════════════════════════════════════════
RULETAS_TRIPLES = [
    'triple zulia', 'triple tachira', 'triple táchira',
    'triple zamorano', 'triple caracas', 'triple carabobo',
    'triple maracay', 'triple guayana', 'triple nacional',
    'el ruco', 'la ruca', 'triple ruca',
    'chance', 'triple chance', 'terminal chance',
    'triple activo', 'triple millonario', 'tripletas'
]

# Palabras que indican que NO es un pronóstico (basura)
EXCLUIR = [
    # Otras agencias (que NO somos nosotros)
    'rodacadiz', 'gogoroyal', 'gogo royal', 'elparcero', 'el parcero',
    'jugabet', 'juga bet', 'somos tu mejor', 'agencia de loteria',
    'agencia de lotería', 'parcero_oficial', 'vip parcero',
    # Links promocionales
    'wa.me', 't.me/', 'bit.ly', 'http://', 'https://',
    'registrate', 'regístrate', 'activa tu bono', 'unirse', 'unirte',
    'comparte y gana', 'compartir y unirte', 'dale like',
    'comenta el animalito', 'menciona a tres', 'pasos a seguir',
    'instagram.com', 'youtube.com', 'youtu.be', 'facebook.com',
    # Deportes
    'copa libertadores', 'flamengo', 'estudiantes de la plata',
    'real madrid', 'vinicius', 'villareal', 'barquisimeto', 'cardenales',
    'tiburones', 'lvbp', 'partido de ida', 'semifinal', 'goles',
    'futbol', 'fútbol', 'beisbol', 'béisbol', 'mundial', 'champions',
    'premier', 'la liga', 'serie a', 'goleada',
    'clasificación', 'clasificacion',
    # Finanzas
    'binance', 'usdt', 'bitcoin', 'criptomoneda',
    # Mega pollas
    'mega polla', 'mega-polla', 'sorteo especial', 'premio mayor'
]


def norm(texto):
    """Normaliza texto: minúsculas y sin tildes."""
    texto = str(texto).lower()
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
    """Cuenta animales únicos."""
    t = norm(texto)
    encontrados = set()
    for a in ANIMALES:
        a_norm = norm(a)
        patron = r'\b' + re.escape(a_norm) + r'\b'
        if re.search(patron, t):
            encontrados.add(a_norm)
    return len(encontrados), list(encontrados)


def menciona_ruleta_animal(texto):
    t = norm(texto)
    for r in RULETAS_ANIMALES:
        if norm(r) in t:
            return True
    return False


def menciona_ruleta_triple(texto):
    t = norm(texto)
    for r in RULETAS_TRIPLES:
        if norm(r) in t:
            return True
    return False


def clasificar(texto):
    """
    Devuelve 'animalitos', 'triples' o None
    """
    if es_basura(texto):
        return None

    cant_animales, animales = contar_animales(texto)
    tiene_ruleta_animal = menciona_ruleta_animal(texto)
    tiene_ruleta_triple = menciona_ruleta_triple(texto)

    # Triple explícito → triples
    if tiene_ruleta_triple:
        return 'triples'

    # Animalitos (filtro muy flexible)
    if tiene_ruleta_animal:
        return 'animalitos'
    if cant_animales >= 1:
        return 'animalitos'
    # Formato tipo "*XX nombre*" → buscar número + animal
    if re.search(r'\d{1,2}\s+[a-z]{4,}', norm(texto)):
        return 'animalitos'
    # Formato "*XX*" solo → probable pronóstico si hay muchos
    if len(re.findall(r'\*\d{2}\*', texto)) >= 3:
        return 'animalitos'

    return None


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

    # Últimos 3 días
    fechas_ok = []
    for i in range(3):
        d = ahora_ven - timedelta(days=i)
        fechas_ok.append(d.strftime('%Y-%m-%d'))
    print(f"Fechas aceptadas: {fechas_ok}")

    pronosticos = []
    vistos = set()
    basura_count = 0
    examinados = 0
    count_animales = 0
    count_triples = 0

    async for msg in client.iter_messages(CANAL, limit=500):
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

        # Clasificar
        tipo = clasificar(texto)
        if not tipo:
            basura_count += 1
            continue

        if tipo == 'animalitos':
            count_animales += 1
            cant, animales = contar_animales(texto)
        else:
            count_triples += 1
            cant = 0

        # Limpiar texto: quitar "PRONÓSTICOS PARA HOY" del inicio
        texto_limpio = re.sub(r'^PRON[ÓO]STICOS\s+PARA\s+HOY\s*', '', texto, flags=re.IGNORECASE).strip()
        texto_limpio = re.sub(r'^PRONOSTICOS\s+PARA\s+HOY\s*', '', texto_limpio, flags=re.IGNORECASE).strip()

        pronosticos.append({
            "tipo": tipo,
            "texto": texto_limpio,
            "fecha": fecha_msg,
            "hora_publicacion": (msg.date - timedelta(hours=4)).strftime('%d/%m %H:%M'),
            "animales": cant
        })

    pronosticos.sort(key=lambda x: x['hora_publicacion'], reverse=True)
    pronosticos = pronosticos[:60]

    print(f"Mensajes examinados: {examinados}")
    print(f"Mensajes descartados: {basura_count}")
    print(f"Pronosticos validos: {len(pronosticos)}")
    print(f"  - Animalitos: {count_animales}")
    print(f"  - Triples: {count_triples}")
    print("")
    print("--- Lista de pronosticos validos ---")
    for p in pronosticos:
        print(f"[{p['tipo']}] [{p['hora_publicacion']}] {p['texto'][:100]}")

    subir_a_gist(pronosticos)


async def main():
    async with client:
        print("Conectado a Telegram...")
        await extraer()


if __name__ == "__main__":
    client.loop.run_until_complete(main())

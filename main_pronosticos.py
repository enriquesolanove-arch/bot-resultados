import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
string_session = os.environ["TELEGRAM_STRING_SESSION"]
GITHUB_TOKEN = os.environ.get("TOKEN_GIST", "")

# ⚠️ Gist ID de pronosticos
GIST_ID = "9fb0808d7249cbc473da64ac11ba88d1"

CANAL = 'pronosticosparahoy'

client = TelegramClient(StringSession(string_session), api_id, api_hash)


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


PALABRAS_EXCLUIR = [
    'mega polla', 'mega-polla', 'unete', 'unirse', 'unirte',
    'grupo de whatsapp', 'link de whatsapp', 'wa.me', 't.me',
    'sorteo especial', 'premio mayor acumulado',
    'canal de telegram', 'nuestro canal', 'nuestro grupo',
    'chance', 'triple zulia', 'triple tachira', 'triple zamorano',
    'triple caracas', 'el ruco', 'la ruca'
]


def es_valido(texto):
    t = texto.lower()
    for p in PALABRAS_EXCLUIR:
        if p in t:
            return False
    return True


def clasificar(texto):
    t = texto.lower()
    tiene_animal = any(k in t for k in ['animalito', 'lotto activo', 'lotto real',
                                          'granjita', 'guacharo', 'guácharo',
                                          'selva plus', 'centena', 'ricachona',
                                          'cachicamo', 'calamar', 'guacharito'])
    if tiene_animal:
        return 'animalitos'
    return None


async def extraer():
    ahora_ven = datetime.utcnow() - timedelta(hours=4)
    hoy = ahora_ven.strftime('%Y-%m-%d')

    pronosticos = []
    vistos = set()

    async for msg in client.iter_messages(CANAL, limit=80):
        if not msg.text:
            continue
        texto = msg.text.strip()
        clave = texto[:100].lower()
        if clave in vistos:
            continue
        vistos.add(clave)

        if not es_valido(texto):
            continue

        tipo = clasificar(texto)
        if not tipo:
            continue

        fecha_msg = (msg.date - timedelta(hours=4)).strftime('%Y-%m-%d')
        if fecha_msg != hoy:
            continue

        pronosticos.append({
            "tipo": tipo,
            "texto": texto,
            "fecha": hoy,
            "hora_publicacion": (msg.date - timedelta(hours=4)).strftime('%H:%M')
        })

    pronosticos.sort(key=lambda x: x['hora_publicacion'], reverse=True)
    pronosticos = pronosticos[:40]

    print(f"Encontrados {len(pronosticos)} pronosticos del dia")
    subir_a_gist(pronosticos)


async def main():
    async with client:
        print("Conectado a Telegram...")
        await extraer()


if __name__ == "__main__":
    client.loop.run_until_complete(main())

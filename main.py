import os
import json
import re
import requests
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession

# Credenciales desde los Secrets de GitHub Actions
api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
string_session = os.environ["TELEGRAM_STRING_SESSION"]

# ═══════════════════════════════════════════════════════════
#  ⚙️ CONFIGURACIÓN DEL GIST (para la web)
#  ─────────────────────────────────────────────────────────
#  GITHUB_TOKEN: créalo en github.com/settings/tokens
#                con permiso SOLO en "gist"
#  GIST_ID: el código largo de la URL del Gist
#           gist.github.com/usuario/5e2cc27bb9af46d52d83c660efb26742
#                                 └─── este es el GIST_ID ───┘
# ═══════════════════════════════════════════════════════════
GITHUB_TOKEN = os.environ.get("TOKEN_GIST", "")  # Secret de GitHub Actions
GIST_ID = "5e2cc27bb9af46d52d83c660efb26742"

CANAL_ORIGEN = 'resultadosagharoldjose'
CANAL_DESTINO = 'opdoradaresultados'

client = TelegramClient(StringSession(string_session), api_id, api_hash)


def subir_a_gist(lista_resultados):
    """Actualiza el archivo resultados.js dentro del Gist público."""
    if not GITHUB_TOKEN:
        print("⚠️ GITHUB_TOKEN_GIST no está configurado, se omite la subida al Gist.")
        return False

    contenido = "window.RESULTADOS = " + json.dumps(lista_resultados, ensure_ascii=False) + ";"

    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "files": {
            "resultados.js": {
                "content": contenido
            }
        }
    }

    try:
        r = requests.patch(url, headers=headers, json=data, timeout=15)
        if r.status_code == 200:
            print(f"✅ Gist actualizado: {len(lista_resultados)} resultados")
            return True
        else:
            print(f"❌ Error Gist: {r.status_code} - {r.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Excepción Gist: {e}")
        return False


async def extraer_y_publicar():
    resultados = []
    
    # Archivos de control
    enviados_path = 'enviados.json'
    fecha_archivo = 'fecha_ultima.txt'
    
    enviados = []
    es_primera_vez = False
    
    if os.path.exists(enviados_path):
        with open(enviados_path, 'r', encoding='utf-8') as f:
            try:
                enviados = json.load(f)
            except:
                enviados = []
    else:
        es_primera_vez = True

    # --- HORA LOCAL (Venezuela UTC-4) ---
    ahora_venezuela = datetime.utcnow() - timedelta(hours=4)
    fecha_hoy = ahora_venezuela.strftime('%Y-%m-%d')
    hora_actual_str = ahora_venezuela.strftime("%H:%M")

    # Control de cambio de día para limpiar resultados de la web automáticamente
    if os.path.exists(fecha_archivo):
        with open(fecha_archivo, 'r', encoding='utf-8') as f:
            ultima_fecha = f.read().strip()
    else:
        ultima_fecha = ""

    # Si es un nuevo día, limpiamos la lista web de la jornada anterior
    if ultima_fecha != fecha_hoy:
        print("🌅 ¡Nuevo día detectado! Reiniciando resultados para la web.")
        resultados = []
        with open(fecha_archivo, 'w', encoding='utf-8') as f:
            f.write(fecha_hoy)
    else:
        # Si ya existe el archivo resultados.json del día, cargamos lo que lleva
        if os.path.exists('resultados.json'):
            with open('resultados.json', 'r', encoding='utf-8') as f:
                try:
                    resultados = json.load(f)
                except:
                    resultados = []

    # Recoger mensajes del canal origen
    mensajes_recogidos = []
    async for message in client.iter_messages(CANAL_ORIGEN, limit=40):
        if message.text:
            mensajes_recogidos.append(message)

    # Invertimos la lista para procesar del más antiguo al más nuevo
    mensajes_recogidos.reverse()

    nuevos_enviados_en_esta_ejecucion = False

    # Patrón flexible para capturar diferentes formatos de resultados del canal
    pattern = r'(?:🎰|🎯)?\s*(?P<loteria>[A-ZÁÉÍÓÚÑ\s]+)\n+\s*(?:🕒)?\s*(?P<hora>\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\s+(?P<numero>\d{1,2})\s*[-:]?\s*(?P<animal>[A-Za-zÁÉÍÓÚáéíóúÑñ]+)'

    for message in mensajes_recogidos:
        texto = message.text.strip()
        match = re.search(pattern, texto)
        
        if match:
            datos = match.groupdict()
            loteria_nombre = datos["loteria"].replace("AGENCIA HAROLD JOSÉ", "").strip()
            
            if not loteria_nombre:
                continue

            item = {
                "loteria": loteria_nombre,
                "hora": datos["hora"].strip().upper(),
                "numero": datos["numero"].zfill(2),
                "animal": datos["animal"].strip().capitalize()
            }

            identificador = f"{item['loteria']}-{item['hora']}-{item['numero']}-{fecha_hoy}"
            
            # Evitar duplicados en la lista web y de enviados
            if not any(r['loteria'] == item['loteria'] and r['hora'] == item['hora'] for r in resultados):
                resultados.append(item)

            # Si es la primera vez que corre, registra sin saturar Telegram
            if es_primera_vez:
                if identificador not in enviados:
                    enviados.append(identificador)
                continue

            # Publicar nuevos resultados en vivo en tu canal
            if identificador not in enviados:
                mensaje_telegram = (
                    f"🎰 *RESULTADO EN VIVO* 🎰\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"📍 *{item['loteria']}* ({item['hora']})\n"
                    f"➡️ *#{item['numero']}* - *{item['animal']}*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"📲 Agencia Oportunidad Dorada"
                )
                
                try:
                    await client.send_message(CANAL_DESTINO, mensaje_telegram, parse_mode='markdown')
                    enviados.append(identificador)
                    nuevos_enviados_en_esta_ejecucion = True
                    print(f"📤 Publicado en Telegram: {item['loteria']} - {item['hora']}")
                except Exception as e:
                    print(f"⚠️ Error al publicar en Telegram: {e}")

    # Si era la primera ejecución, guardamos estado base
    if es_primera_vez:
        with open(enviados_path, 'w', encoding='utf-8') as f:
            json.dump(enviados[-300:], f, ensure_ascii=False, indent=2)
        print("🛡️ Historial inicializado correctamente.")

    # Guardar archivo JSON actualizado para la web de Neocities
    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    if not es_primera_vez:
        with open(enviados_path, 'w', encoding='utf-8') as f:
            json.dump(enviados[-300:], f, ensure_ascii=False, indent=2)

    # ═══════════════════════════════════════════════════════════
    #  📤 SUBIR AL GIST (para que la web lo lea en vivo)
    # ═══════════════════════════════════════════════════════════
    print(f"📤 Subiendo {len(resultados)} resultados al Gist...")
    subir_a_gist(resultados)

    # Mensaje de cierre de tanda tras publicar novedades
    id_cierre_tanda = f"cierre-tanda-{fecha_hoy}"
    if not es_primera_vez and nuevos_enviados_en_esta_ejecucion and id_cierre_tanda not in enviados:
        msg_tanda = (
            f"✅ *¡Listo los resultados a esta hora!* ⏰\n"
            f"La taquilla sigue activa 🎰. Escríbenos para realizar tu jugada 📲.\n\n"
            f"⚡ *Agencia Oportunidad Dorada*"
        )
        try:
            await client.send_message(CANAL_DESTINO, msg_tanda, parse_mode='markdown')
            enviados.append(id_cierre_tanda)
            with open(enviados_path, 'w', encoding='utf-8') as f:
                json.dump(enviados[-300:], f, ensure_ascii=False, indent=2)
            print("📤 Enviado mensaje de cierre de tanda.")
        except Exception as e:
            print(f"Error enviando cierre de tanda: {e}")

    # Mensaje de buenas noches a las 10:00 PM (22:00) hora de Venezuela
    id_buenas_noches = f"buenas-noches-{fecha_hoy}"
    if not es_primera_vez and hora_actual_str >= "22:00" and id_buenas_noches not in enviados:
        msg_noches = (
            f"🌙 *¡Buenas noches para todos!* ✨\n"
            f"Cerramos operaciones por el día de hoy. Mañana nos activamos nuevamente con más fuerza y mejores jugadas por *Agencia Oportunidad Dorada* 🎰🔥."
        )
        try:
            await client.send_message(CANAL_DESTINO, msg_noches, parse_mode='markdown')
            enviados.append(id_buenas_noches)
            with open(enviados_path, 'w', encoding='utf-8') as f:
                json.dump(enviados[-300:], f, ensure_ascii=False, indent=2)
            print("📤 Enviado mensaje de buenas noches.")
        except Exception as e:
            print(f"Error enviando buenas noches: {e}")

    print(f"✅ Proceso finalizado con éxito.")


async def main():
    async with client:
        print("🤖 Conectado a Telegram...")
        await extraer_y_publicar()


if __name__ == "__main__":
    client.loop.run_until_complete(main())

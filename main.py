import os
import json
import re
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession

# Credenciales desde los Secrets de GitHub Actions
api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
string_session = os.environ["TELEGRAM_STRING_SESSION"]

CANAL_ORIGEN = 'resultadosagharoldjose' 
CANAL_DESTINO = 'opdoradaresultados' 

client = TelegramClient(StringSession(string_session), api_id, api_hash)

async def extraer_y_publicar():
    resultados = []
    
    # Cargar enviados históricos o persistentes si existen
    enviados_path = 'enviados.json'
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

    # Recoger mensajes del canal origen
    mensajes_recogidos = []
    async for message in client.iter_messages(CANAL_ORIGEN, limit=40):
        if message.text:
            mensajes_recogidos.append(message)

    # Invertimos la lista para procesar del más antiguo al más nuevo
    mensajes_recogidos.reverse()

    nuevos_enviados_en_esta_ejecucion = False

    # Patrón ultra flexible para capturar cualquier formato de resultado
    pattern = r'(?:🎰|🎯)?\s*(?P<loteria>[A-ZÁÉÍÓÚÑ\s]+)\n+\s*(?:🕒)?\s*(?P<hora>\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\s+(?P<numero>\d{1,2})\s*[-:]?\s*(?P<animal>[A-Za-zÁÉÍÓÚáéíóúÑñ]+)'

    for message in mensajes_recogidos:
        texto = message.text.strip()
        
        match = re.search(pattern, texto)
        
        if match:
            datos = match.groupdict()
            loteria_nombre = datos["loteria"].replace("AGENCIA HAROLD JOSÉ", "").strip()
            
            # Si el texto extraído no es un nombre válido de lotería, saltar
            if not loteria_nombre:
                continue

            item = {
                "loteria": loteria_nombre,
                "hora": datos["hora"].strip().upper(),
                "numero": datos["numero"].zfill(2),
                "animal": datos["animal"].strip().capitalize()
            }
            resultados.append(item)

            identificador = f"{item['loteria']}-{item['hora']}-{item['numero']}"
            
            # Si es la primera vez que corre, registra sin publicar para no saturar
            if es_primera_vez:
                if identificador not in enviados:
                    enviados.append(identificador)
                continue

            # Publicar nuevos resultados en vivo
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

    # Si era la primera ejecución, guardamos el estado base
    if es_primera_vez:
        with open(enviados_path, 'w', encoding='utf-8') as f:
            json.dump(enviados[-300:], f, ensure_ascii=False, indent=2)
        print("🛡️ Historial inicializado correctamente.")

    # Guardar archivo JSON actualizado para la web
    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    if not es_primera_vez:
        with open(enviados_path, 'w', encoding='utf-8') as f:
            json.dump(enviados[-300:], f, ensure_ascii=False, indent=2)

    # --- HORA LOCAL (Venezuela UTC-4) ---
    ahora_venezuela = datetime.utcnow() - timedelta(hours=4)
    fecha_hoy = ahora_venezuela.strftime('%Y-%m-%d')
    hora_actual_str = ahora_venezuela.strftime("%H:%M")
    
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
    

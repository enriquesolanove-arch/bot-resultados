import os
import json
import re
from datetime import datetime
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
    if os.path.exists(enviados_path):
        with open(enviados_path, 'r', encoding='utf-8') as f:
            try:
                enviados = json.load(f)
            except:
                enviados = []

    nuevos_enviados_en_esta_ejecucion = False

    # Leemos los mensajes recientes del canal de origen
    async for message in client.iter_messages(CANAL_ORIGEN, limit=40):
        if not message.text:
            continue
            
        texto = message.text.strip()
        
        # Patrón para capturar el resultado
        pattern = r'🎰\s*(?P<loteria>[^\n]+)\n+🕒\s*(?P<hora>\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\s+(?P<numero>\d{1,2})\s*[-:]?\s*(?P<animal>[A-Za-zÁÉÍÓÚáéíóúÑñ]+)'
        match = re.search(pattern, texto)
        
        if match:
            datos = match.groupdict()
            item = {
                "loteria": datos["loteria"].strip(),
                "hora": datos["hora"].strip().upper(),
                "numero": datos["numero"].zfill(2),
                "animal": datos["animal"].strip().capitalize()
            }
            resultados.append(item)

            # Identificador único por sorteo, hora y número
            identificador = f"{item['loteria']}-{item['hora']}-{item['numero']}"
            
            # Si NO ha sido enviado antes, lo mandamos a Telegram
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

    # Guardar archivo JSON actualizado para la web
    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    # Guardar registro de enviados para que nunca se repitan (acumulamos hasta 200)
    with open(enviados_path, 'w', encoding='utf-8') as f:
        json.dump(enviados[-200:], f, ensure_ascii=False, indent=2)

    # --- MANEJO DE MENSAJES DE CIERRE AUTOMÁTICOS ---
    ahora = datetime.now()
    fecha_hoy = ahora.strftime('%Y-%m-%d')
    hora_actual_str = ahora.strftime("%H:%M")
    
    # Mensaje de cierre de tanda
    id_cierre_tanda = f"cierre-tanda-{fecha_hoy}"
    if nuevos_enviados_en_esta_ejecucion and id_cierre_tanda not in enviados:
        msg_tanda = (
            f"✅ *¡Listo los resultados a esta hora!* ⏰\n"
            f"La taquilla sigue activa 🎰. Escríbenos para realizar tu jugada 📲.\n\n"
            f"⚡ *Agencia Oportunidad Dorada*"
        )
        try:
            await client.send_message(CANAL_DESTINO, msg_tanda, parse_mode='markdown')
            enviados.append(id_cierre_tanda)
            print("📤 Enviado mensaje de cierre de tanda.")
        except Exception as e:
            print(f"Error enviando cierre de tanda: {e}")

    # Mensaje de buenas noches a partir de las 10:00 PM (22:00)
    id_buenas_noches = f"buenas-noches-{fecha_hoy}"
    if hora_actual_str >= "22:00" and id_buenas_noches not in enviados:
        msg_noches = (
            f"🌙 *¡Buenas noches para todos!* ✨\n"
            f"Cerramos operaciones por el día de hoy. Mañana nos activamos nuevamente con más fuerza y mejores jugadas por *Agencia Oportunidad Dorada* 🎰🔥."
        )
        try:
            await client.send_message(CANAL_DESTINO, msg_noches, parse_mode='markdown')
            enviados.append(id_buenas_noches)
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
    

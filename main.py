import os
import json
import re
from telethon import TelegramClient
from telethon.sessions import StringSession

# Credenciales desde los Secrets de GitHub Actions
api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
string_session = os.environ["TELEGRAM_STRING_SESSION"]

# 1. Canal de donde EXTRAES los resultados
CANAL_ORIGEN = 'resultadosagharoldjose' 

# 2. Tu canal de destino donde se publicarán los resultados
CANAL_DESTINO = 'opdoradaresultados' 

client = TelegramClient(StringSession(string_session), api_id, api_hash)

async def extraer_y_publicar():
    resultados = []
    
    # Cargar resultados previos para evitar repetir publicaciones en Telegram
    enviados_path = 'enviados.json'
    enviados = []
    if os.path.exists(enviados_path):
        with open(enviados_path, 'r', encoding='utf-8') as f:
            try:
                enviados = json.load(f)
            except:
                enviados = []

    # Aumentamos el límite a 150 mensajes para capturar todos los sorteos del día
    async for message in client.iter_messages(CANAL_ORIGEN, limit=150):
        if not message.text:
            continue
            
        texto = message.text.strip()
        
        # Patrón para extraer Lotería, Hora, Número y Animal
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

            # Identificador único para evitar duplicados en Telegram
            identificador = f"{item['loteria']}-{item['hora']}-{item['numero']}"
            
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
                    print(f"📤 Publicado en Telegram: {item['loteria']} - {item['hora']}")
                except Exception as e:
                    print(f"⚠️ Error al publicar en Telegram: {e}")

    # Guardar archivo JSON actualizado para la web
    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    # Guardar registro de enviados
    with open(enviados_path, 'w', encoding='utf-8') as f:
        json.dump(enviados[-100:], f, ensure_ascii=False, indent=2)
        
    print(f"✅ Proceso finalizado. {len(resultados)} resultados guardados en el JSON.")

async def main():
    async with client:
        print("🤖 Conectado a Telegram...")
        await extraer_y_publicar()

if __name__ == "__main__":
    client.loop.run_until_complete(main())
                

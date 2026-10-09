import os
import json
import re
from telethon import TelegramClient
from telethon.sessions import StringSession

# Credenciales desde los Secrets de GitHub Actions
api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
string_session = os.environ["TELEGRAM_STRING_SESSION"]

# 1. Canal de donde EXTRAES los resultados (ej: agenciaharoldjose)
CANAL_ORIGEN = 'resultadosagharoldjose' 

# 2. Canal donde VAS A PUBLICAR los resultados (ej: tu propio canal o grupo, ej: OportunidadDoradaResultados)
CANAL_DESTINO = 'opdoradaresultados' 

client = TelegramClient(StringSession(string_session), api_id, api_hash)

async def extraer_y_publicar():
    resultados = []
    
    # Intentar cargar resultados previos para no repetir publicaciones
    enviados_path = 'enviados.json'
    enviados = []
    if os.path.exists(enviados_path):
        with open(enviados_path, 'r', encoding='utf-8') as f:
            try:
                enviados = json.load(f)
            except:
                enviados = []

    async for message in client.iter_messages(CANAL_ORIGEN, limit=15):
        if not message.text:
            continue
            
        texto = message.text.strip()
        
        # Patrón adaptado a tus mensajes de Telegram
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

            # Identificador único para saber si ya se publicó este sorteo
            identificador = f"{item['loteria']}-{item['hora']}-{item['numero']}"
            
            if identificador not in enviados:
                # Mensaje atractivo para publicar en tu canal
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

    # Guardar registro de enviados para evitar duplicados
    with open(enviados_path, 'w', encoding='utf-8') as f:
        json.dump(enviados[-50:], f, ensure_ascii=False, indent=2)
        
    print(f"✅ Proceso finalizado. {len(resultados)} resultados guardados.")

async def main():
    async with client:
        print("🤖 Conectado a Telegram...")
        await extraer_y_publicar()

if __name__ == "__main__":
    client.loop.run_until_complete(main())
    

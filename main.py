import os
import json
import re
from telethon import TelegramClient
from telethon.sessions import StringSession

# 1. Cargar credenciales desde los Secrets de GitHub Actions
api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
string_session = os.environ["TELEGRAM_STRING_SESSION"]

# Nombre de usuario del canal de Telegram (sin @)
CANAL_TELEGRAM = 'LottoActivoOficial'  # Asegúrate de colocar el username real del canal

client = TelegramClient(StringSession(string_session), api_id, api_hash)

async def extraer_resultados():
    resultados = []
    
    # Obtener los últimos 30 mensajes del canal
    async for message in client.iter_messages(CANAL_TELEGRAM, limit=30):
        if not message.text:
            continue
            
        texto = message.text.strip()
        
        # Expresión regular ajustada para capturar:
        # Lotería (después de 🎰)
        # Hora, Número y Animal (después de 🕒)
        pattern = r'🎰\s*(?P<loteria>[^\n]+)\n+🕒\s*(?P<hora>\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\s+(?P<numero>\d{1,2})\s*[-:]?\s*(?P<animal>[A-Za-zÁÉÍÓÚáéíóúÑñ]+)'
        
        match = re.search(pattern, texto)
        
        if match:
            datos = match.groupdict()
            resultados.append({
                "loteria": datos["loteria"].strip(),
                "hora": datos["hora"].strip().upper(),
                "numero": datos["numero"].zfill(2), # Formato a 2 dígitos (ej: 05)
                "animal": datos["animal"].strip().capitalize()
            })

    # Guardar en resultados.json
    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Se procesaron y guardaron {len(resultados)} resultados exitosamente.")

async def main():
    async with client:
        print("🤖 Conectado a Telegram con StringSession...")
        await extraer_resultados()

if __name__ == "__main__":
    client.loop.run_until_complete(main())
    

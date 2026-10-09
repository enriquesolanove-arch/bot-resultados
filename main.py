import os
import json
import re
from telethon import TelegramClient
from telethon.sessions import StringSession

# 1. Cargar credenciales desde los Secrets de GitHub Actions
api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
string_session = os.environ["TELEGRAM_STRING_SESSION"]

# Canal o grupo de Telegram desde donde se leen los resultados (Nombre de usuario o ID)
# Cambia 'tu_canal_resultados' por el username real del canal sin @
CANAL_TELEGRAM = 'tu_canal_resultados' 

client = TelegramClient(StringSession(string_session), api_id, api_hash)

async def extraer_resultados():
    resultados = []
    
    # Obtener los últimos 30 mensajes del canal
    async for message in client.iter_messages(CANAL_TELEGRAM, limit=30):
        if not message.text:
            continue
            
        texto = message.text.strip()
        
        # Expresión regular orientada a loterías de animalitos / triples
        # Ejemplo esperado: "Lotto Activo 10:00 AM - 25 Gallina"
        # Adapta este patrón según la estructura de texto exacta del canal
        patron = r'(?P<loteria>[A-Za-z\s]+)\s+(?P<hora>\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\s*[-:]?\s*(?P<numero>\d{1,2})\s*[-:]?\s*(?P<animal>[A-Za-z]+)'
        coincidencia = re.search(patron, texto)
        
        if coincidencia:
            datos = coincidencia.groupdict()
            resultados.append({
                "loteria": datos["loteria"].strip(),
                "hora": datos["hora"].strip().upper(),
                "numero": datos["numero"].zfill(2), # Formato a 2 dígitos (ej: 05)
                "animal": datos["animal"].strip().capitalize()
            })
        else:
            # Procesamiento alternativo simple por líneas si no coincide con el patrón estricto
            lineas = texto.split('\n')
            for linea in lineas:
                if any(k in linea.lower() for k in ['activo', 'granjita', 'selva', 'guacharo', 'dato']):
                    resultados.append({
                        "loteria": "Sorteo",
                        "hora": "En vivo",
                        "numero": "00",
                        "animal": linea.strip()
                    })

    # Guardar en archivo resultados.json
    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Se procesaron y guardaron {len(resultados)} resultados exitosamente.")

async def main():
    async with client:
        print("🤖 Conectado a Telegram con StringSession...")
        await extraer_resultados()

if __name__ == "__main__":
    client.loop.run_until_complete(main())
    

import os
from telethon import TelegramClient
from telethon.sessions import StringSession

# Leer credenciales desde las variables de entorno de GitHub
api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
string_session = os.environ["TELEGRAM_STRING_SESSION"]

# Iniciar el cliente usando StringSession
client = TelegramClient(StringSession(string_session), api_id, api_hash)

async function main():
    async with client:
        # Aquí va el resto de tu código de extracción/publicación
        pass

if __name__ == "__main__":
    client.loop.run_until_complete(main())
    

import os
import json
import re
import requests
import asyncio
from threading import Thread
from flask import Flask
from requests.auth import HTTPBasicAuth
from telethon import TelegramClient, events

# --- SERVIDOR WEB DUMMY PARA ENGAÑAR A RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de resultados activo 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURACIÓN DE ACCESOS ---
API_ID = 30070257
API_HASH = 'f276b94bb1b88422bf44ad842995c3e0' 
CANAL_ORIGEN = '@resultadosagharoldjose'   # Nombre de usuario o enlace del canal

NEOCITIES_USER = 'agenciaopdorada'
NEOCITIES_PASS = 'abc123' 

client = TelegramClient('sesion_resultados', API_ID, API_HASH)
lista_resultados = []

def extraer_resultado(texto):
    patron = r"🎰\s*([A-Za-zÁÉÍÓÚáéíóúñÑ\s]+)[\r\n]+\s*🕒\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\s+(\d{1,2})\s*-\s*([A-Za-zÁÉÍÓÚáéíóúñÑ]+)"
    match = re.search(patron, texto)
    if match:
        return {
            "loteria": match.group(1).strip(),
            "hora": match.group(2).strip(),
            "numero": match.group(3).strip(),
            "animal": match.group(4).strip()
        }
    return None

def subir_a_neocities(datos_json):
    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(datos_json, f, ensure_ascii=False, indent=2)
    
    url = 'https://neocities.org/api/upload'
    with open('resultados.json', 'rb') as f:
        files = {'resultados.json': f}
        try:
            response = requests.post(url, auth=HTTPBasicAuth(NEOCITIES_USER, NEOCITIES_PASS), files=files)
            if response.status_code == 200:
                print("🚀 ¡Resultados actualizados en Neocities!")
            else:
                print("⚠️ Error Neocities:", response.text)
        except Exception as e:
            print("❌ Error de red:", e)

@client.on(events.NewMessage(chats=CANAL_ORIGEN))
async def handler_nuevo_mensaje(event):
    texto = event.raw_text
    res = extraer_resultado(texto)
    
    if res:
        print(f"✨ Resultado: {res['loteria']} | {res['hora']} -> {res['numero']} - {res['animal']}")
        lista_resultados.insert(0, res)
        if len(lista_resultados) > 30:
            lista_resultados.pop()
        subir_a_neocities(lista_resultados)

if __name__ == '__main__':
    # Inicia Flask en un hilo secundario para responder a Render
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

    print("🤖 Bot activo...")
    client.start()
    client.run_until_disconnected()
    

import json
import re
import requests
from requests.auth import HTTPBasicAuth
from telethon import TelegramClient, events

# --- CONFIGURACIÓN DE ACCESOS ---
API_ID = 30070257
API_HASH = 'f276b94bb1b88422bf44ad842995c3e0'
CANAL_ORIGEN = '@resultadosagharoldjose'  

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

print("🤖 Bot activo...")
client.start()
client.run_until_disconnected()

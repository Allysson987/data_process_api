import requests
import json
import os
from dotenv import load_dotenv
load_dotenv('.env')
api_key=os.getenv('API_KEY')
url = "https://api-publica.datajud.cnj.jus.br/api_publica_trf1/_search"

payload = json.dumps({
  "query": {
    "match": {
      "numeroProcesso": "00008323520184013202"
    }
  }
})

#Substituir <API Key> pela Chave Pública
headers = {
  'Authorization': rf'ApiKey {api_key}',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
import json
import requests
from app.core.config import Settings
from app.core.court_classifier import CourtClassifier

class DataJudService:
    def __init__(self):
        self.court_classifier = CourtClassifier()
        self.settings = Settings()
        self.base_url = "https://api-publica.datajud.cnj.jus.br/"

    def build_url(self, number_process: str) -> str:
        """
        Constrói a URL completa para consultar informações sobre um processo judicial no DataJud.
        """
        # Executa a classificação
        process_info = self.court_classifier.classify(number_process)
        
        if not process_info or "state_name" not in process_info:
            raise ValueError("Número do processo inválido ou estado não identificado.")
        
        # Usando a chave que você ajustou para refletir o nome/sigla de forma semântica
        state_name = process_info["state_name"].lower()
        
        search_url = f"{self.base_url}api_publica_tj{state_name}/_search"
        return search_url

    def get_process_info(self, number_process: str) -> dict:
        """
        Consulta informações sobre um processo judicial usando a API DataJud.
        """
        url = self.build_url(number_process)
        
        payload = json.dumps({
            "query": {
                "match": {
                    "numeroProcesso": number_process
                }
            }
        })
        
        headers = {
            'Authorization': f'ApiKey {self.settings.DATA_JUD_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=payload)
        
        if response.status_code != 200:
            raise Exception(f"Erro ao consultar a API DataJud: {response.status_code} - {response.text}")
            
        return response.json()
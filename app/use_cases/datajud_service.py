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
        number_process=process_info['number_process']
        return search_url, number_process

    def get_process_info(self, number_process: str) -> dict:
       

        search_url, number_process = self.build_url(number_process)

        print("PROCESSO:", number_process)
        print("URL:", search_url)

        payload = {
            "query": {
                "match": {
                    "numeroProcesso": number_process
                }
            }
        }

        print("PAYLOAD:", payload)
        headers = {
            'Authorization': f'ApiKey {self.settings.DATA_JUD_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            search_url,
            headers=headers,
            json=payload
        )

        print("STATUS:", response.status_code)
        print("RESPOSTA:", response.text)

        return response.json()

    
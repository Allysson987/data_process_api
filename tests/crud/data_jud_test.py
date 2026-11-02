from pathlib import Path
import sys
from unittest.mock import patch

ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.services.datajud_service import DataJudService

@patch("app.services.datajud_service.requests.post")
@patch("app.services.datajud_service.CourtClassifier")  # Isola o classificador para o teste do serviço focar na API
def test_datajud_service_get_process_info(mock_classifier_class, mock_post):
    # 1. Simula o retorno do CourtClassifier baseando-se nas chaves que você definiu (`state_name`)
    mock_classifier_instance = mock_classifier_class.return_value
    mock_classifier_instance.classify.return_value = {
        "number_process": "12345678920268260100",
        "segment_name": "Justiça Estadual",
        "state_name": "SP"
    }

    # 2. Configura a resposta falsa da requisição POST para o DataJud
    mock_response_data = {
        "took": 5,
        "timed_out": False,
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_index": "api_publica_tjsp",
                    "_source": {"numeroProcesso": "12345678920268260100"}
                }
            ]
        }
    }
    
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = mock_response_data

    # 3. Executa o serviço
    service = DataJudService()
    resultado = service.get_process_info("1234567-89.2026.8.26.0100")

    # 4. Validações
    assert isinstance(resultado, dict)
    assert "hits" in resultado
    assert resultado["hits"]["total"]["value"] == 1
    mock_post.assert_called_once()
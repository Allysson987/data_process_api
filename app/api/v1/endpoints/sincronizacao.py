from fastapi import APIRouter, HTTPException
from app.core.court_classifier import CourtClassifier

# Cria o roteador específico para este arquivo
router = APIRouter()

# Instancia o classificador que criamos antes
classifier = CourtClassifier()

@router.get("/{numero_processo}")
def get_process_info(numero_processo: str):
    """
    Endpoint para analisar o número do processo judicial.
    """
    try:
        # Chama a função/classe que faz o trabalho pesado
        resultado = classifier.classify(numero_processo)
        
        return {
            "status": "sucesso",
            "info": resultado
        }
        
    except ValueError as e:
        # Se der erro (ex: tamanho errado), devolve um erro HTTP 400 (Bad Request)
        raise HTTPException(status_code=400, detail=str(e))



from fastapi import APIRouter, HTTPException
from app.controllers.controller_execution import ControllerExecutionDataJud

# Cria o roteador específico para este arquivo
router = APIRouter()

# Instancia o classificador que criamos antes
consult = ControllerExecutionDataJud()
@router.get('/diary/{uf}')
def get_diary_info(uf: str):
    result = consult.consult_diary_rules(uf)
    return {
            'status': 'sucesso',
            'info': result
    }
@router.get("/consult_case/{number_case}")
def get_process_info(number_case: str):
    """
    Endpoint para analisar o número do processo judicial.
    """
    try:
        # Chama a função/classe que faz o trabalho pesado
        result = consult.consult_diary_rules(number_case=number_case)

        return {
            "status": "sucesso",
            "info": result
        }
        
    except ValueError as e:
        # Se der erro (ex: tamanho errado), devolve um erro HTTP 400 (Bad Request)
        raise HTTPException(status_code=400, detail=str(e))



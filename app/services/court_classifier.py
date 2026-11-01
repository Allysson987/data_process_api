
from pathlib import Path
import sys


ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.utils.segment_mapping import SegmentMapping
from app.utils.state_mapping import MappingStates
class CourtClassifier:
    def __init__(self):
        self.segment_mapping = SegmentMapping()
        self.state_mapping = MappingStates()

    def classify(self, number_process: str) -> dict:
        '''
        Realiza a identificação do tribunal e segmento a partir do número do processo (Padrão CNJ).
        '''
        number_process = self.clear_process(number_process)
        
        if len(number_process) != 20:
            raise ValueError("O número do processo não está no formato CNJ (deve conter 20 dígitos após a limpeza).")
        
        # Extração correta baseada no padrão CNJ de 20 dígitos
        segment = number_process[13:14]       # Posição 14 (índice 13)
        court_code = number_process[14:16] # Posições 15 e 16 (índices 14 e 15)
        
        # Mapeamento do segmento
        segment_name = self.segment_mapping.get_segment(segment)
        # Mapeamento do estado
        state_name = self.state_mapping.state_mapping(court_code)

        return {
            "segment": segment_name,
            "state": state_name
        }

    def clear_process(self, number_process: str) -> str:
        try:
            if not isinstance(number_process, str):
                raise ValueError("O número do processo deve ser uma string.")
            
            # Limpa pontos, hífens, barras e também espaços em branco extras
            number_process = number_process.replace('.', '').replace('-', '').replace('/', '').strip()
            return number_process
            
        except Exception as e:
            raise ValueError(f"Erro ao limpar o número do processo: {e}")
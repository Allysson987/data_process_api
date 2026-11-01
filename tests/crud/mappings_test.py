from pathlib import Path
import sys

# Sobe 2 níveis: de tests/crud/ para a raiz do projeto (data_process_api)
ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.utils.state_mapping import MappingStates

def test_state_mapping():
    mapping = MappingStates()
    
    # Test valid state codes
    assert mapping.state_mapping('01') == 'AC'
    assert mapping.state_mapping('26') == 'SP'
    
    # Test invalid state code
    assert mapping.state_mapping('99') == ''
    
    # Test empty state code
    assert mapping.state_mapping('') == ''
    
    # Test None as state code
    assert mapping.state_mapping(None) == ''
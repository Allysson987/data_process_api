from pathlib import Path
import sys

ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.core.court_classifier import CourtClassifier  # Ou ajuste o caminho de onde você salvou

def test_court_classifier_valid():
    classifier = CourtClassifier()
    
    # Exemplo fictício com formato CNJ (supondo Justiça Estadual = 8, Tribunal SP = 26)
    # NNNNNNN-DD.AAAA.J.TR.OOOO -> 1234567-89.2026.8.26.0100
    processo = "1234567-89.2026.8.26.0100"
    
    resultado = classifier.classify(processo)
    
    # Valida se retornou um dicionário com as chaves corretas
    assert isinstance(resultado, dict)
    assert "segment_name" in resultado
    assert "state_name" in resultado
    assert resultado["state_name"] == "SP"

def test_court_classifier_invalid_length():
    classifier = CourtClassifier()
    
    # Processo com tamanho errado
    import pytest
    with pytest.raises(ValueError, match="não está no formato CNJ"):
        classifier.classify("12345")
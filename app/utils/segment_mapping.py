

class SegmentMapping:
    def dict_mapping(self) -> dict:
        '''
        Código de mapeamento dos segmentos do processo com seus respectivos códigos.
        1 - Cível, 2 - Criminal, 3 - Fazenda Pública, 4 - Trabalho, 5 - Eleitoral, 6 - Militar.
        '''
        return {
            '1': 'Cível',
            '2': 'Criminal',
            '3': 'Fazenda Pública',
            '4': 'Trabalho',
            '5': 'Eleitoral',
            '6': 'Militar'
        }
    def get_segment(self, segment_code: str) -> str: 
        try:
            segments_dict = self.dict_mapping()
            return segments_dict.get(segment_code, "")
        except Exception as e:
            return f"Erro ao mapear o segmento: {e}"
    
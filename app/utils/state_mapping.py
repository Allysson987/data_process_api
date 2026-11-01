

class MappingStates:
    def dict_state(self) -> dict:

        '''
        Código de mapeamento dos estados brasileiros com seus respectivos códigos.
        TJAC 01, TJAL 02, TJAP 03, TJAM 04, TJBA 05, TJCE 06, TJDF 07, TJES 08, TJGO 09, TJMA 10, TJMT 11, TJMS 12, TJMG 13, TJPA 14, TJPB 15, TJPR 16, TJPE 17, TJPI 18, TJRJ 19, TJRN 20, TJRS 21, TJRO 22, TJRR 23, TJSC 24, TJSE 25, TJSP 26, TJTO 27.
        '''
        return{
            '01':'AC',
            '02':'AL',
            '03':'AP',
            '04':'AM',
            '05':'BA',
            '06':'CE',
            '07':'DF',
            '08':'ES',
            '09':'GO',
            '10':'MA',
            '11':'MT',
            '12':'MS',
            '13':'MG',
            '14':'PA',
            '15':'PB',
            '16':'PR',
            '17':'PE',
            '18':'PI',
            '19':'RJ',
            '20':'RN',
            '21':'RS',
            '22':'RO',
            '23':'RR',
            '24':'SC',
            '25':'SE',
            '26':'SP',
            '27':'TO'
        }
    def state_mapping(self, code_state: str) -> str:
        try:
            states_dict = self.dict_state()
            return states_dict.get(code_state, "")
        except Exception as e:
            return f"Erro ao mapear o estado: {e}"

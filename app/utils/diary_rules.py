
from app.use_cases.diary_office.office_diary_pe import (
    DjePeGetData
)

from app.use_cases.diary_office.office_diary_ac import (
    DjeAcGetData
)

from app.use_cases.diary_office.office_diary_al import (
    DjeAlGetData
)

from app.use_cases.diary_office.office_diary_ap import (
    DjeApGetData
)

from app.use_cases.diary_office.office_diary_am import (
    DjeAmGetData
)

from app.use_cases.diary_office.office_diary_ba import (
    DjeBaGetData
)

from app.use_cases.diary_office.office_diary_nation import (
    ComunicaPjeService
)


class RulesDiary:

    def __init__(self):

        self.providers = {
            "pe": DjePeGetData(),
            "ac": DjeAcGetData(),
            "al": DjeAlGetData(),
            "ap": DjeApGetData(),
            "am": DjeAmGetData(),
            "ba": DjeBaGetData(),

            "nacional": ComunicaPjeService()
        }

    def get_provider(self, uf: str):

        provider = self.providers.get(
            uf.lower()
        )

        if not provider:
            raise ValueError(
                f"UF não suportada: {uf}"
            )

        return provider

    def get_available_states(self) -> list[str]:

        return sorted(
            uf.upper()
            for uf in self.providers.keys()
            if uf != "nacional"
        )

    def get_available_providers(self) -> list[str]:

        return sorted(
            self.providers.keys()
        )


from datetime import datetime
from typing import Any


class ComunicaPjeMapper:
    """
    Converte uma comunicação do Comunica PJe
    para o formato normalizado da tabela Diary.
    """

    DJEN_URL = "https://comunica.pje.jus.br/"

    @classmethod
    def build_diary(
        cls,
        communication: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Converte uma única comunicação em um único registro Diary.
        """

        communication_id = communication.get("id")
        tribunal = communication.get("siglaTribunal")
        available_date = communication.get("data_disponibilizacao")

        if not communication_id:
            raise ValueError("Comunicação sem identificador (id).")

        if not tribunal:
            raise ValueError("Comunicação sem siglaTribunal.")

        if not available_date:
            raise ValueError(
                f"Comunicação {communication_id} sem data de disponibilização."
            )

        process_number = (
            communication.get("numeroprocessocommascara")
            or communication.get("numero_processo")
            or "Processo não informado"
        )

        communication_type = (
            communication.get("tipoComunicacao")
            or "Comunicação processual"
        )

        court_unit = (
            communication.get("nomeOrgao")
            or "Órgão não informado"
        )

        title = (
            f"{communication_type} | "
            f"{process_number} | "
            f"{court_unit}"
        )

        content = communication.get("texto") or ""

        if not isinstance(content, str):
            content = str(content)

        return {
            "source": tribunal.upper(),
            "source_id": str(communication_id),
            "publication_date": available_date,
            "available_date": available_date,
            "update_date": datetime.now(),
            "title": title,
            "content": content,
            "pdf_url": cls.DJEN_URL,
        }

from datetime import datetime

from app.models.models_diary import Diary
import io


import requests
import pdfplumber
from pathlib import Path


class DjePeGetData:

    BASE_URL = "https://dje-publico.svc.tjpe.jus.br"

    def get_last_diary(self):

        response = requests.get(
            f"{self.BASE_URL}/api/diario-eletronicos/recentes"
        )

        response.raise_for_status()

        return response.json()[0]

    def extract_pdf(
    self,
    pdf_bytes: bytes
) -> str:

        text = ""

        with pdfplumber.open(
            io.BytesIO(pdf_bytes)
        ) as pdf:

            for page in pdf.pages:
                text += page.extract_text() or ""

        return text

    def build_diary(self):

        diary = self.get_last_diary()

        response = requests.get(
            f"{self.BASE_URL}/api/diario-eletronicos/{diary['id']}/download"
        )

        text = self.extract_pdf(
            response.content
        )

        return {
            "source": "TJPE",
            "source_id": str(diary["id"]),
            "publication_date": diary["dataPublicacao"],
            "available_date": diary["dataPublicacao"],
            "update_date": diary["dataHoraModificacao"],
            "title": f"Diário {diary['numero']}/{diary['ano']}",
            "content": text,
            "pdf_url": f"{self.BASE_URL}/api/diario-eletronicos/{diary['id']}/download",
    }

import io
import requests
import pdfplumber


class DjePeGetData:

    BASE_URL = "https://dje-publico.svc.tjpe.jus.br"

    def get_last_diary(self) -> dict:

        response = requests.get(
            f"{self.BASE_URL}/api/diario-eletronicos/recentes",
            timeout=30
        )

        response.raise_for_status()

        diaries = response.json()

        if not diaries:
            raise ValueError(
                "Nenhum diário recente encontrado no TJPE."
            )

        return diaries[0]

    def extract_pdf(
        self,
        pdf_bytes: bytes
    ) -> str:

        text = ""

        with pdfplumber.open(
            io.BytesIO(pdf_bytes)
        ) as pdf:

            for page in pdf.pages:

                text += (
                    page.extract_text()
                    or ""
                )

        return text

    def build_diary(self):

        diary = self.get_last_diary()

        pdf_url = (
            f"{self.BASE_URL}/api/diario-eletronicos/"
            f"{diary['id']}/download"
        )

        response = requests.get(
            pdf_url,
            timeout=60
        )

        response.raise_for_status()

        text = self.extract_pdf(
            response.content
        )

        yield {
            "source": "TJPE",

            "source_id": str(diary["id"]),

            "publication_date": diary["dataPublicacao"],

            "available_date": diary["dataPublicacao"],

            "update_date": diary["dataHoraModificacao"],

            "title": (
                f"Diário {diary['numero']}/{diary['ano']}"
            ),

            "content": text,

            "pdf_url": pdf_url
        }


import io
import requests
import pdfplumber


class DjeApGetData:

    BASE_URL = "https://tucujuris.tjap.jus.br"

    def get_last_diary(self) -> dict:

        response = requests.get(
            f"{self.BASE_URL}/api/dje/buscar-ultimos-diarios",
            headers={
                "Accept": "application/json",
                "Referer": f"{self.BASE_URL}/dje/consulta",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/157.0.0.0 Safari/537.36"
                )
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        diaries = data.get("dados", [])

        if not diaries:
            raise ValueError(
                "Nenhum diário recente encontrado no TJAP."
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

                text += "\n"

        return text.strip()

    def build_diary(self):

        diary = self.get_last_diary()

        pdf_url = (
            f"{self.BASE_URL}/api/publico/download-diario"
        )

        response = requests.get(
            pdf_url,
            params={
                "id": diary["id"],
                "numeroDiario": diary["num_diario"],
                "captcha": "null"
            },
            headers={
                "Accept": "application/pdf",
                "Referer": f"{self.BASE_URL}/dje/consulta",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/157.0.0.0 Safari/537.36"
                )
            },
            timeout=60
        )

        response.raise_for_status()

        if not response.content.startswith(b"%PDF"):
            raise ValueError(
                "O download do TJAP não retornou um PDF válido. "
                f"Content-Type: {response.headers.get('Content-Type')}"
            )

        text = self.extract_pdf(
            response.content
        )

        yield {
            "source": "TJAP",

            "source_id": str(diary["id"]),

            "publication_date": diary["dt_publicacao"],

            "available_date": diary["dt_divulgacao"],

            "update_date": diary["dtatu"],

            "title": f"Diário {diary['num_diario']}",

            "content": text,

            "pdf_url": response.url
        }

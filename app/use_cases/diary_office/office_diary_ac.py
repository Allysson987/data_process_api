
import io
import requests
import pdfplumber

from bs4 import BeautifulSoup

from app.utils.date_convert import DateConvert

class DjeAcGetData:

    BASE_URL = "https://diario.tjac.jus.br"

    def get_last_diary(self) -> dict:

        response = requests.get(
            f"{self.BASE_URL}/edicoes.php",
            timeout=30
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        download_link = soup.select_one(
            'a[href*="PDF="]'
        )

        date_link = soup.select_one(
            'a[href*="Diario="]'
        )

        if not download_link:
            raise ValueError(
                "Link do diário não encontrado."
            )

        return {
            "publication_date": (
                date_link.get_text(strip=True)
                if date_link
                else None
            ),
            "pdf_url": (
                f"{self.BASE_URL}/"
                + download_link["href"]
            )
        }

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

        response = requests.get(
            diary["pdf_url"],
            timeout=60
        )

        response.raise_for_status()

        text = self.extract_pdf(
            response.content
        )

        yield {
            "source": "TJAC",

            "source_id": diary["pdf_url"],

            "publication_date": DateConvert.parse(
                diary["publication_date"]
            ),

            "available_date": None,

            "update_date": None,

            "title": diary["publication_date"],

            "content": text,

            "pdf_url": diary["pdf_url"]
        }

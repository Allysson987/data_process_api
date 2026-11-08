import io
import requests
import pdfplumber

from bs4 import BeautifulSoup


class DjeAcGetData:

    BASE_URL = "https://diario.tjac.jus.br"

    def get_last_diary(self):

        response = requests.get(
            f"{self.BASE_URL}/edicoes.php"
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
            diary["pdf_url"]
        )

        response.raise_for_status()

        text = self.extract_pdf(
            response.content
        )

        return {
            "source": "TJAC",

            "source_id":
                diary["pdf_url"],

            "publication_date":
                None,

            "available_date":
                None,

            "update_date":
                None,

            "title":
                diary["publication_date"],

            "content":
                text,

            "pdf_url":
                diary["pdf_url"]
        }
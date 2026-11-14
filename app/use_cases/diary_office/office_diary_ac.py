
import requests

from bs4 import BeautifulSoup

from app.utils.date_convert import DateConvert
from app.utils.extract_pdfs import ExtractPdf


class DjeAcGetData:

    BASE_URL = "https://diario.tjac.jus.br"

    def __init__(self):

        self.session = requests.Session()

        self.pdf_extractor = ExtractPdf()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/130.0.0.0 Safari/537.36"
            )
        })

    def get_last_diary(self) -> dict:

        response = self.session.get(
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

    def download_diary(self, pdf_url: str) -> bytes:

        print(
            "[TJAC] Iniciando download do diário",
            flush=True
        )

        response = self.session.get(
            pdf_url,
            timeout=(15, 90),
            stream=True
        )

        try:

            response.raise_for_status()

            pdf_bytes = bytearray()

            for chunk in response.iter_content(
                chunk_size=64 * 1024
            ):

                if chunk:
                    pdf_bytes.extend(chunk)

            if not pdf_bytes.startswith(b"%PDF-"):
                raise ValueError(
                    "O conteúdo recebido não é um PDF válido."
                )

        finally:
            response.close()

        print(
            f"[TJAC] Download concluído: "
            f"{len(pdf_bytes) / 1024:.2f} KB",
            flush=True
        )

        return bytes(pdf_bytes)

    def build_diary(self):

        diary = self.get_last_diary()

        print(
            "[TJAC] Diário localizado. Iniciando processamento.",
            flush=True
        )

        pdf_bytes = self.download_diary(
            diary["pdf_url"]
        )

        content = self.pdf_extractor.extract_full_pages(
            pdf_bytes=pdf_bytes,
            uf="AC"
        )

        del pdf_bytes

        publication_date = diary["publication_date"]

        diary_data = {

            "source": "TJAC",

            "source_id": diary["pdf_url"],

            "publication_date": (
                DateConvert.parse(publication_date)
                if publication_date
                else None
            ),

            "available_date": None,

            "update_date": None,

            "title": publication_date,

            "content": content,

            "pdf_url": diary["pdf_url"]

        }

        print(
            "[TJAC] Entregando diário ao Controller",
            flush=True
        )

        yield diary_data


import re
import requests

from bs4 import BeautifulSoup
from datetime import datetime, date
from html import unescape
from urllib.parse import urljoin

from app.utils.extract_pdfs import ExtractPdf


class DjeBaGetData:

    BASE_URL = "https://diario.tjba.jus.br/diario/internet"

    MONTHS = {
        "janeiro": 1,
        "fevereiro": 2,
        "março": 3,
        "marco": 3,
        "abril": 4,
        "maio": 5,
        "junho": 6,
        "julho": 7,
        "agosto": 8,
        "setembro": 9,
        "outubro": 10,
        "novembro": 11,
        "dezembro": 12,
    }

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

    def initialize_session(self) -> str:

        response = self.session.get(
            f"{self.BASE_URL}/pesquisar.wsp",
            timeout=(15, 30)
        )

        response.raise_for_status()

        print(
            "[TJBA] Sessão inicializada",
            flush=True
        )

        return response.text

    def parse_publication_date(
        self,
        text: str
    ) -> date | None:

        normalized = unescape(text).lower()

        pattern = re.search(
            r"(\d{1,2})\s+de\s+"
            r"([a-zçãõ]+)\s+de\s+(\d{4})",
            normalized
        )

        if pattern:

            day = int(pattern.group(1))
            month_name = pattern.group(2)
            year = int(pattern.group(3))

            month = self.MONTHS.get(month_name)

            if month:

                try:
                    return date(year, month, day)

                except ValueError:
                    return None

        numeric_date = re.search(
            r"\b(\d{2})/(\d{2})/(\d{4})\b",
            normalized
        )

        if numeric_date:

            try:
                return datetime.strptime(
                    numeric_date.group(0),
                    "%d/%m/%Y"
                ).date()

            except ValueError:
                return None

        return None

    def get_latest_edition(
        self,
        html: str
    ) -> dict:

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        editions = []

        for anchor in soup.find_all("a"):

            reference = (
                anchor.get("href", "")
                + " "
                + anchor.get("onclick", "")
            )

            match = re.search(
                r"\bver\s*\(\s*['\"]?(\d+)",
                reference,
                re.IGNORECASE
            )

            if not match:
                continue

            edition_number = match.group(1)

            context = anchor.get_text(
                " ",
                strip=True
            )

            parent = anchor.parent

            for _ in range(4):

                if parent is None:
                    break

                context += " " + parent.get_text(
                    " ",
                    strip=True
                )

                parent = parent.parent

            publication_date = self.parse_publication_date(
                context
            )

            if publication_date is None:
                continue

            editions.append({
                "edition": edition_number,
                "publication_date": publication_date,
                "title": context.strip()
            })

        if not editions:

            raise ValueError(
                "[TJBA] Não foi possível identificar "
                "edições com suas respectivas datas."
            )

        latest = max(
            editions,
            key=lambda item: (
                item["publication_date"],
                int(item["edition"])
            )
        )

        print(
            f"[TJBA] Última edição encontrada: "
            f"{latest['edition']} | "
            f"Data: {latest['publication_date']}",
            flush=True
        )

        return latest

    def get_menu(
        self,
        edition: str
    ) -> tuple[str, BeautifulSoup]:

        menu_url = f"{self.BASE_URL}/menu.wsp"

        response = self.session.get(
            menu_url,
            params={
                "tmp.diario.nu_edicao": edition
            },
            headers={
                "Referer": (
                    f"{self.BASE_URL}/pesquisar.wsp"
                )
            },
            timeout=(15, 30)
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        return response.url, soup

    def download_full_diary(
        self,
        edition: str
    ) -> tuple[bytes, str]:

        print(
            f"[TJBA] Preparando download da edição "
            f"{edition}",
            flush=True
        )

        menu_url, soup = self.get_menu(edition)

        form = soup.find(
            "form",
            attrs={"name": "fmMenu"}
        )

        if form is None:

            raise ValueError(
                "[TJBA] Formulário fmMenu não encontrado "
                "no menu da edição."
            )

        payload = {}

        for field in form.find_all(
            "input",
            attrs={"type": "hidden"}
        ):

            name = field.get("name")

            if name:
                payload[name] = field.get("value", "")

        payload["tmp.diario.nu_edicao"] = edition

        download_url = urljoin(
            menu_url,
            "download.wsp"
        )

        response = self.session.post(
            download_url,
            data=payload,
            headers={
                "Referer": menu_url,
                "Origin": "https://diario.tjba.jus.br",
                "Content-Type": (
                    "application/x-www-form-urlencoded"
                )
            },
            timeout=(15, 120),
            stream=True
        )

        try:

            print(
                f"[TJBA] HTTP: {response.status_code}",
                flush=True
            )

            response.raise_for_status()

            pdf_bytes = bytearray()

            for chunk in response.iter_content(
                chunk_size=64 * 1024
            ):

                if chunk:
                    pdf_bytes.extend(chunk)

            if not pdf_bytes.startswith(b"%PDF-"):

                raise ValueError(
                    "[TJBA] A resposta não é um PDF. "
                    f"Content-Type: "
                    f"{response.headers.get('Content-Type')}. "
                    f"Resposta: {bytes(pdf_bytes[:300])!r}"
                )

            pdf_url = response.url

            print(
                f"[TJBA] PDF completo baixado: "
                f"{len(pdf_bytes) / 1024:.2f} KB",
                flush=True
            )

            return bytes(pdf_bytes), pdf_url

        finally:
            response.close()

    def build_diary(self):

        html = self.initialize_session()

        edition_data = self.get_latest_edition(html)

        edition = edition_data["edition"]

        publication_date = edition_data["publication_date"]

        try:

            pdf_bytes, pdf_url = self.download_full_diary(
                edition
            )

            content = self.pdf_extractor.extract_full_pages(
                pdf_bytes=pdf_bytes,
                uf="BA"
            )

            del pdf_bytes

            if not content.strip():

                raise ValueError(
                    "O PDF foi baixado, mas não "
                    "foi possível extrair texto."
                )

            diary_data = {
                "source": "TJBA",

                "source_id": edition,

                "publication_date": publication_date,

                "available_date": publication_date,

                "update_date": datetime.now(),

                "title": (
                    f"Diário de Justiça do Estado da Bahia "
                    f"- Edição {edition}"
                ),

                "pdf_url": pdf_url,

                "content": content
            }

            print(
                "[TJBA] Diário entregue ao Controller",
                flush=True
            )

            yield diary_data

        except Exception as error:

            print(
                f"[TJBA] Erro ao processar edição "
                f"{edition}: {error}",
                flush=True
            )

            raise


if __name__ == "__main__":

    provider = DjeBaGetData()

    for diary in provider.build_diary():

        print("\n" + "=" * 60)
        print("DIÁRIO EXTRAÍDO")
        print("=" * 60)

        print("Fonte:", diary["source"])
        print("ID:", diary["source_id"])
        print("Título:", diary["title"])
        print("Publicação:", diary["publication_date"])
        print("Caracteres:", len(diary["content"]))

        filename = f"TJBA_{diary['source_id']}.txt"

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(diary["content"])

        print("Arquivo salvo:", filename)

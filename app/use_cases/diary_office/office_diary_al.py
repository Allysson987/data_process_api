
import io
import re
import requests
import pdfplumber

from datetime import datetime, timedelta


class DjeAlGetData:

    BASE_URL = "https://www2.tjal.jus.br/cdje"

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/130.0.0.0 Safari/537.36"
            )
        })

    def get_last_date(self):

        return (
            datetime.now().date() - timedelta(days=1)
        )

    def get_cadernos(
        self,
        dt_diario: str
    ) -> list[dict]:

        response = self.session.get(
            f"{self.BASE_URL}/getListaDeCadernos.do",
            params={
                "dtDiario": dt_diario
            },
            headers={
                "Referer": f"{self.BASE_URL}/index.do",
                "X-Requested-With": "XMLHttpRequest"
            },
            timeout=(15, 30)
        )

        response.raise_for_status()

        pattern = re.compile(
            r"\{\s*"
            r"cdVolume:\s*(\d+)\s*,\s*"
            r"nuDiario:\s*(\d+)\s*,\s*"
            r"cdCaderno:\s*(\d+)\s*,\s*"
            r"nmCaderno:\s*'((?:\\.|[^'])*)'"
            r"\s*\}"
        )

        matches = pattern.findall(response.text)

        cadernos = []

        for match in matches:

            cd_volume, nu_diario, cd_caderno, nm_caderno = match

            cadernos.append({
                "cdVolume": int(cd_volume),
                "nuDiario": int(nu_diario),
                "cdCaderno": int(cd_caderno),
                "nmCaderno": nm_caderno
            })

        return cadernos

    def get_last_available_diary(
        self,
        days_back: int = 15
    ):

        date = self.get_last_date()

        for _ in range(days_back):

            dt_diario = date.strftime("%d/%m/%Y")

            try:

                cadernos = self.get_cadernos(dt_diario)

                print(
                    f"[TJAL] Consultando {dt_diario} | "
                    f"Cadernos: {len(cadernos)}",
                    flush=True
                )

                if cadernos:
                    return dt_diario, cadernos

            except requests.exceptions.HTTPError as error:

                print(
                    f"[TJAL] Erro HTTP em {dt_diario}: {error}",
                    flush=True
                )

            date -= timedelta(days=1)

        raise ValueError(
            f"Nenhuma edição encontrada nos últimos {days_back} dias."
        )

    def download_caderno(
        self,
        dt_diario: str,
        caderno: dict
    ) -> bytes:

        print(
            f"[TJAL] Iniciando download: "
            f"{caderno['nmCaderno']}",
            flush=True
        )

        response = self.session.get(
            f"{self.BASE_URL}/downloadCaderno.do",
            params={
                "dtDiario": dt_diario,
                "cdCaderno": caderno["cdCaderno"],
                "tpDownload": "D"
            },
            headers={
                "Referer": f"{self.BASE_URL}/index.do"
            },
            timeout=(15, 90),
            stream=True
        )

        print(
            f"[TJAL] Status HTTP: {response.status_code}",
            flush=True
        )

        response.raise_for_status()

        pdf_bytes = bytearray()

        try:

            for chunk in response.iter_content(
                chunk_size=64 * 1024
            ):

                if chunk:

                    pdf_bytes.extend(chunk)

                    print(
                        f"[TJAL] Baixados: "
                        f"{len(pdf_bytes) / 1024:.2f} KB",
                        flush=True
                    )

        finally:

            response.close()

        if not pdf_bytes.startswith(b"%PDF-"):

            raise ValueError(
                f"Resposta não é PDF. "
                f"Conteúdo recebido: {bytes(pdf_bytes[:100])!r}"
            )

        print(
            f"[TJAL] Download concluído: "
            f"{len(pdf_bytes) / 1024:.2f} KB",
            flush=True
        )

        return bytes(pdf_bytes)

    def extract_pdf(
        self,
        pdf_bytes: bytes
    ) -> str:

        print(
            "[TJAL] Iniciando extração do PDF",
            flush=True
        )

        pages_text = []

        with pdfplumber.open(
            io.BytesIO(pdf_bytes)
        ) as pdf:

            total_pages = len(pdf.pages)

            print(
                f"[TJAL] Total de páginas: {total_pages}",
                flush=True
            )

            for index, page in enumerate(
                pdf.pages,
                start=1
            ):

                print(
                    f"[TJAL] Extraindo página "
                    f"{index}/{total_pages}",
                    flush=True
                )

                page_text = page.extract_text()

                if page_text:
                    pages_text.append(page_text)

        content = "\n".join(pages_text)

        print(
            f"[TJAL] Extração concluída: "
            f"{len(content)} caracteres",
            flush=True
        )

        return content

    def build_diary(self):

        dt_diario, cadernos = (
            self.get_last_available_diary()
        )

        publication_date = datetime.strptime(
            dt_diario,
            "%d/%m/%Y"
        ).date()

        for caderno in cadernos:

            try:

                print(
                    f"\n[TJAL] Processando: "
                    f"{caderno['nmCaderno']}",
                    flush=True
                )

                pdf_bytes = self.download_caderno(
                    dt_diario,
                    caderno
                )

                content = self.extract_pdf(
                    pdf_bytes
                )

                diary_data = {

                    "source": "TJAL",

                    "source_id": (
                        f"{caderno['nuDiario']}_"
                        f"{caderno['cdCaderno']}"
                    ),

                    "publication_date": publication_date,

                    "available_date": publication_date,

                    "update_date": datetime.now(),

                    "title": caderno["nmCaderno"],

                    "pdf_url": (
                        f"{self.BASE_URL}/downloadCaderno.do"
                        f"?dtDiario={dt_diario}"
                        f"&cdCaderno={caderno['cdCaderno']}"
                        "&tpDownload=D"
                    ),

                    "content": content

                }

                print(
                    "[TJAL] Entregando diário ao Controller",
                    flush=True
                )

                yield diary_data

            except Exception as error:

                print(
                    f"[TJAL] Erro no caderno "
                    f"{caderno['cdCaderno']}: {error}",
                    flush=True
                )

                continue

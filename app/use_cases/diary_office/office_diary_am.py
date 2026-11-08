
import io
import re
import requests
import pdfplumber

from datetime import datetime


class DjeAmGetData:

    BASE_URL = "https://consultasaj.tjam.jus.br/cdje"

    TARGET_DATE = datetime.now().strftime('dd/mm/yyyy')

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/130.0.0.0 Safari/537.36"
            )
        })

    def initialize_session(self):

        response = self.session.get(
            f"{self.BASE_URL}/index.do",
            headers={
                "Referer": "https://www.tjam.jus.br/"
            },
            timeout=(15, 30)
        )

        response.raise_for_status()

        print(
            "[TJAM] Sessão inicializada",
            flush=True
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
                "X-Requested-With": "XMLHttpRequest",
                "X-Prototype-Version": "1.6.0.3",
                "Accept": (
                    "text/javascript, text/html, "
                    "application/xml, text/xml, */*"
                )
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

        print(
            f"[TJAM] Data: {dt_diario} | "
            f"Cadernos encontrados: {len(cadernos)}",
            flush=True
        )

        if not cadernos:
            print(
                "[TJAM] Resposta recebida:",
                response.text[:3000],
                flush=True
            )
        print("\n[TJAM] RESPOSTA DE getListaDeCadernos.do:")
        print(response.text)
        
        return cadernos

    def get_secoes(
        self,
        caderno: dict
    ) -> str:

        response = self.session.get(
            f"{self.BASE_URL}/getListaDeSecoes.do",
            params={
                "cdVolume": caderno["cdVolume"],
                "nuDiario": caderno["nuDiario"],
                "cdCaderno": caderno["cdCaderno"]
            },
            headers={
                "Referer": f"{self.BASE_URL}/index.do",
                "X-Requested-With": "XMLHttpRequest",
                "X-Prototype-Version": "1.6.0.3",
                "Accept": (
                    "text/javascript, text/html, "
                    "application/xml, text/xml, */*"
                )
            },
            timeout=(15, 30)
        )

        response.raise_for_status()

        return response.text

    def download_caderno(
        self,
        dt_diario: str,
        caderno: dict
    ) -> bytes:

        print(
            f"[TJAM] Tentando download: "
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

        try:

            print(
                f"[TJAM] HTTP: {response.status_code}",
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
                    "Resposta não é PDF. "
                    f"Content-Type: "
                    f"{response.headers.get('Content-Type')}. "
                    f"Conteúdo: {bytes(pdf_bytes[:300])!r}"
                )

            print(
                f"[TJAM] PDF baixado: "
                f"{len(pdf_bytes) / 1024:.2f} KB",
                flush=True
            )

            return bytes(pdf_bytes)

        finally:
            response.close()

    def extract_pdf(
        self,
        pdf_bytes: bytes
    ) -> str:

        pages_text = []

        with pdfplumber.open(
            io.BytesIO(pdf_bytes)
        ) as pdf:

            print(
                f"[TJAM] Total de páginas: {len(pdf.pages)}",
                flush=True
            )

            for index, page in enumerate(
                pdf.pages,
                start=1
            ):

                print(
                    f"[TJAM] Extraindo página "
                    f"{index}/{len(pdf.pages)}",
                    flush=True
                )

                page_text = page.extract_text()

                if page_text:
                    pages_text.append(page_text)

        content = "\n".join(pages_text)

        print(
            f"[TJAM] Texto extraído: "
            f"{len(content)} caracteres",
            flush=True
        )

        return content

    def build_diary(self):

        self.initialize_session()

        dt_diario = self.TARGET_DATE

        cadernos = self.get_cadernos(
            dt_diario
        )

        if not cadernos:
            raise ValueError(
                f"Nenhum caderno encontrado em {dt_diario}"
            )

        publication_date = datetime.strptime(
            dt_diario,
            "%d/%m/%Y"
        ).date()

        for caderno in cadernos:

            try:

                print(
                    f"\n[TJAM] Processando "
                    f"{caderno['nmCaderno']}",
                    flush=True
                )

                secoes = self.get_secoes(
                    caderno
                )

                print(
                    "[TJAM] Seções retornadas:",
                    flush=True
                )

                print(
                    secoes[:3000],
                    flush=True
                )

                pdf_bytes = self.download_caderno(
                    dt_diario,
                    caderno
                )

                content = self.extract_pdf(
                    pdf_bytes
                )

                if not content:
                    raise ValueError(
                        "PDF sem texto extraído."
                    )

                yield {
                    "source": "TJAM",

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

            except Exception as error:

                print(
                    f"[TJAM] Erro no caderno "
                    f"{caderno['cdCaderno']}: {error}",
                    flush=True
                )

                continue


if __name__ == "__main__":

    provider = DjeAmGetData()

    for diary in provider.build_diary():

        print("\n" + "=" * 60)
        print("DIÁRIO EXTRAÍDO")
        print("=" * 60)

        print("Fonte:", diary["source"])
        print("ID:", diary["source_id"])
        print("Título:", diary["title"])
        print("Publicação:", diary["publication_date"])
        print("Caracteres:", len(diary["content"]))

        filename = (
            f"TJAM_{diary['source_id']}.txt"
        )

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(diary["content"])

        print("Arquivo salvo:", filename)


import re
import requests

from datetime import datetime

from app.utils.extract_pdfs import ExtractPdf


class DjeAmGetData:

    BASE_URL = "https://consultasaj.tjam.jus.br/cdje"

    TARGET_DATE = datetime.now().strftime("%d/%m/%Y")

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

    def initialize_session(self) -> None:

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
                "[TJAM] Nenhum caderno identificado. "
                "Resposta recebida:",
                response.text[:3000],
                flush=True
            )

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

    def build_diary(self):

        self.initialize_session()

        dt_diario = self.TARGET_DATE

        cadernos = self.get_cadernos(dt_diario)

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

                secoes = self.get_secoes(caderno)

                print(
                    f"[TJAM] Seções retornadas: {len(secoes)} caracteres",
                    flush=True
                )

                pdf_bytes = self.download_caderno(
                    dt_diario,
                    caderno
                )

                content = self.pdf_extractor.extract_full_pages(
                    pdf_bytes=pdf_bytes,
                    uf="AM"
                )

                del pdf_bytes

                if not content.strip():
                    raise ValueError(
                        "PDF sem texto extraído."
                    )

                pdf_url = (
                    f"{self.BASE_URL}/downloadCaderno.do"
                    f"?dtDiario={dt_diario}"
                    f"&cdCaderno={caderno['cdCaderno']}"
                    "&tpDownload=D"
                )

                diary_data = {
                    "source": "TJAM",

                    "source_id": (
                        f"{caderno['nuDiario']}_"
                        f"{caderno['cdCaderno']}"
                    ),

                    "publication_date": publication_date,

                    "available_date": publication_date,

                    "update_date": datetime.now(),

                    "title": caderno["nmCaderno"],

                    "pdf_url": pdf_url,

                    "content": content
                }

                print(
                    "[TJAM] Diário entregue ao Controller",
                    flush=True
                )

                yield diary_data

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

        filename = f"TJAM_{diary['source_id']}.txt"

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(diary["content"])

        print("Arquivo salvo:", filename)

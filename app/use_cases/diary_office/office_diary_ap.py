
import requests

from app.utils.extract_pdfs import ExtractPdf


class DjeApGetData:

    BASE_URL = "https://tucujuris.tjap.jus.br"

    def __init__(self):

        self.session = requests.Session()
        self.pdf_extractor = ExtractPdf()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/157.0.0.0 Safari/537.36"
            )
        })

    def get_last_diary(self) -> dict:

        response = self.session.get(
            f"{self.BASE_URL}/api/dje/buscar-ultimos-diarios",
            headers={
                "Accept": "application/json",
                "Referer": f"{self.BASE_URL}/dje/consulta"
            },
            timeout=(15, 30)
        )

        response.raise_for_status()

        data = response.json()

        diaries = data.get("dados", [])

        if not diaries:
            raise ValueError(
                "Nenhum diário recente encontrado no TJAP."
            )

        diary = diaries[0]

        print(
            f"[TJAP] Diário localizado: "
            f"{diary.get('num_diario')}",
            flush=True
        )

        return diary

    def download_diary(
        self,
        diary: dict
    ) -> tuple[bytes, str]:

        pdf_url = (
            f"{self.BASE_URL}/api/publico/download-diario"
        )

        print(
            f"[TJAP] Iniciando download do diário "
            f"{diary['num_diario']}",
            flush=True
        )

        response = self.session.get(
            pdf_url,
            params={
                "id": diary["id"],
                "numeroDiario": diary["num_diario"],
                "captcha": "null"
            },
            headers={
                "Accept": "application/pdf",
                "Referer": f"{self.BASE_URL}/dje/consulta"
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
                    "O download do TJAP não retornou "
                    "um PDF válido. "
                    f"Content-Type: "
                    f"{response.headers.get('Content-Type')}"
                )

            final_url = response.url

            print(
                f"[TJAP] Download concluído: "
                f"{len(pdf_bytes) / 1024:.2f} KB",
                flush=True
            )

            return bytes(pdf_bytes), final_url

        finally:
            response.close()

    def build_diary(self):

        diary = self.get_last_diary()

        pdf_bytes, pdf_url = self.download_diary(diary)

        content = self.pdf_extractor.extract_full_pages(
            pdf_bytes=pdf_bytes,
            uf="AP"
        )

        del pdf_bytes

        if not content.strip():
            raise ValueError(
                "PDF do TJAP sem texto extraído."
            )

        diary_data = {
            "source": "TJAP",

            "source_id": str(diary["id"]),

            "publication_date": diary["dt_publicacao"],

            "available_date": diary["dt_divulgacao"],

            "update_date": diary["dtatu"],

            "title": f"Diário {diary['num_diario']}",

            "content": content,

            "pdf_url": pdf_url
        }

        print(
            "[TJAP] Diário entregue ao Controller",
            flush=True
        )

        yield diary_data


if __name__ == "__main__":

    provider = DjeApGetData()

    for diary in provider.build_diary():

        print("\n" + "=" * 60)
        print("DIÁRIO EXTRAÍDO")
        print("=" * 60)

        print("Fonte:", diary["source"])
        print("ID:", diary["source_id"])
        print("Título:", diary["title"])
        print("Publicação:", diary["publication_date"])
        print("Caracteres:", len(diary["content"]))

        filename = f"TJAP_{diary['source_id']}.txt"

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(diary["content"])

        print("Arquivo salvo:", filename)

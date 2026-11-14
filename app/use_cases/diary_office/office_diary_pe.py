
import requests

from app.utils.extract_pdfs import ExtractPdf


class DjePeGetData:

    BASE_URL = "https://dje-publico.svc.tjpe.jus.br"

    def __init__(self):

        self.session = requests.Session()
        self.pdf_extractor = ExtractPdf()

        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/130.0.0.0 Safari/537.36"
            )
        })

    def get_last_diary(self) -> dict:

        response = self.session.get(
            f"{self.BASE_URL}/api/diario-eletronicos/recentes",
            timeout=(15, 30)
        )

        response.raise_for_status()

        diaries = response.json()

        if not isinstance(diaries, list):
            raise ValueError(
                "[TJPE] A API não retornou uma lista de diários."
            )

        if not diaries:
            raise ValueError(
                "[TJPE] Nenhum diário recente encontrado."
            )

        diary = diaries[0]

        print(
            f"[TJPE] Diário localizado: "
            f"{diary.get('numero')}/{diary.get('ano')}",
            flush=True
        )

        return diary

    def download_diary(
        self,
        diary_id: str | int
    ) -> tuple[bytes, str]:

        pdf_url = (
            f"{self.BASE_URL}/api/diario-eletronicos/"
            f"{diary_id}/download"
        )

        print(
            f"[TJPE] Iniciando download do diário {diary_id}",
            flush=True
        )

        response = self.session.get(
            pdf_url,
            headers={
                "Accept": "application/pdf"
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
                    "[TJPE] O download não retornou um PDF válido. "
                    f"Content-Type: "
                    f"{response.headers.get('Content-Type')}. "
                    f"Resposta: {bytes(pdf_bytes[:300])!r}"
                )

            final_url = response.url

            print(
                f"[TJPE] Download concluído: "
                f"{len(pdf_bytes) / 1024:.2f} KB",
                flush=True
            )

            return bytes(pdf_bytes), final_url

        finally:
            response.close()

    def build_diary(self):

        diary = self.get_last_diary()

        pdf_bytes, pdf_url = self.download_diary(
            diary_id=diary["id"]
        )

        content = self.pdf_extractor.extract_full_pages(
            pdf_bytes=pdf_bytes,
            uf="PE"
        )

        del pdf_bytes

        if not content.strip():

            raise ValueError(
                "[TJPE] PDF baixado, mas sem texto extraído."
            )

        diary_data = {
            "source": "TJPE",

            "source_id": str(diary["id"]),

            "publication_date": diary["dataPublicacao"],

            "available_date": diary["dataPublicacao"],

            "update_date": diary["dataHoraModificacao"],

            "title": (
                f"Diário {diary['numero']}/{diary['ano']}"
            ),

            "content": content,

            "pdf_url": pdf_url
        }

        print(
            "[TJPE] Diário entregue ao Controller",
            flush=True
        )

        yield diary_data


if __name__ == "__main__":

    provider = DjePeGetData()

    for diary in provider.build_diary():

        print("\n" + "=" * 60)
        print("DIÁRIO EXTRAÍDO")
        print("=" * 60)

        print("Fonte:", diary["source"])
        print("ID:", diary["source_id"])
        print("Título:", diary["title"])
        print("Publicação:", diary["publication_date"])
        print("Caracteres:", len(diary["content"]))

        filename = f"TJPE_{diary['source_id']}.txt"

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(diary["content"])

        print("Arquivo salvo:", filename)

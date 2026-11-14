
import io
import gc
import pdfplumber


class ExtractPdf:

    def open_pdf(self, pdf_bytes: bytes) -> pdfplumber.PDF:
        return pdfplumber.open(io.BytesIO(pdf_bytes))

    def total_pages(self, pdf: pdfplumber.PDF) -> int:
        return len(pdf.pages)

    def init_buffer(self) -> io.StringIO:
        return io.StringIO()

    def extract_full_pages(self, pdf_bytes: bytes, uf: str) -> str:

        print(f'[TJ{uf}] Iniciando extração do PDF', flush=True)

        buffer = self.init_buffer()

        try:
            with self.open_pdf(pdf_bytes) as pdf:

                pages: int = self.total_pages(pdf)

                print(
                    f'[TJ{uf}] Total de páginas: {pages}',
                    flush=True
                )

                for index, page in enumerate(pdf.pages, start=1):

                    print(
                        f'[TJ{uf}] Extraindo página {index}/{pages}',
                        flush=True
                    )

                    text: str | None = page.extract_text()

                    if text:
                        buffer.write(text)
                        buffer.write('\n')

                    del text

                    if index % 20 == 0:
                        gc.collect()

            content: str = buffer.getvalue()

            print(
                f'[TJ{uf}] Extração concluída: '
                f'{len(content)} caracteres',
                flush=True
            )

            return content

        finally:
            buffer.close()

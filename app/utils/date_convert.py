
import re
import unicodedata

from datetime import date, datetime


class DateConvert:

    MONTHS = {
        "janeiro": 1,
        "fevereiro": 2,
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

    @staticmethod
    def normalize(value: str) -> str:
        value = unicodedata.normalize("NFKD", value)
        value = "".join(
            char for char in value
            if not unicodedata.combining(char)
        )
        return value.lower().strip()

    @classmethod
    def parse(cls, value: str | date | datetime | None) -> date | None:

        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if not isinstance(value, str):
            raise TypeError(
                f"Tipo de data inválido: {type(value).__name__}"
            )

        value = cls.normalize(value)

        # Formatos numéricos: 06/11/2026 ou 2026-11-06
        for date_format in (
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
        ):
            try:
                return datetime.strptime(
                    value,
                    date_format
                ).date()
            except ValueError:
                continue

        # Formato por extenso: 6 de novembro de 2026
        match = re.search(
            r"(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})",
            value
        )

        if match:
            day = int(match.group(1))
            month_name = match.group(2)
            year = int(match.group(3))

            month = cls.MONTHS.get(month_name)

            if month is None:
                raise ValueError(
                    f"Mês não reconhecido: {month_name}"
                )

            return date(year, month, day)

        raise ValueError(
            f"Formato de data não reconhecido: {value}"
        )

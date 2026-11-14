
from collections.abc import Iterator
from datetime import date
from typing import Any
from urllib.parse import quote

import requests


class ComunicaPjeService:
    """
    Cliente da API pública Comunica PJe / DJEN do CNJ.

    Documentação:
        https://comunicaapi.pje.jus.br/swagger/index.html

    API:
        https://comunicaapi.pje.jus.br/api/v1
    """

    BASE_URL = "https://comunicaapi.pje.jus.br/api/v1"

    STATE_COURTS = {
        "AC": "TJAC",
        "AL": "TJAL",
        "AP": "TJAP",
        "AM": "TJAM",
        "BA": "TJBA",
        "CE": "TJCE",
        "DF": "TJDFT",
        "ES": "TJES",
        "GO": "TJGO",
        "MA": "TJMA",
        "MT": "TJMT",
        "MS": "TJMS",
        "MG": "TJMG",
        "PA": "TJPA",
        "PB": "TJPB",
        "PR": "TJPR",
        "PE": "TJPE",
        "PI": "TJPI",
        "RJ": "TJRJ",
        "RN": "TJRN",
        "RS": "TJRS",
        "RO": "TJRO",
        "RR": "TJRR",
        "SC": "TJSC",
        "SP": "TJSP",
        "SE": "TJSE",
        "TO": "TJTO",
    }

    VALID_MEDIA = {"D", "E"}

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()

        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        })

    def _get(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> Any:
        """Executa GET e retorna a resposta JSON."""

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        response = self.session.get(
            url,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        try:
            return response.json()

        except requests.exceptions.JSONDecodeError as error:
            raise ValueError(
                f"A API retornou uma resposta que não é JSON. "
                f"Endpoint: {endpoint}. "
                f"Resposta: {response.text[:500]}"
            ) from error

    def get_tribunals(self) -> Any:
        """
        Consulta os tribunais cadastrados na API.

        GET /comunicacao/tribunal
        """

        return self._get("comunicacao/tribunal")

    def get_state_courts(self) -> dict[str, str]:
        """Retorna o mapeamento dos tribunais por UF."""

        return self.STATE_COURTS.copy()

    def extract_tribunal_siglas(
        self,
        response: Any,
    ) -> list[str]:
        """
        Extrai somente siglas encontradas em campos conhecidos.

        Não considera textos genéricos do JSON como siglas.
        """

        siglas = set()
        known_courts = set(self.STATE_COURTS.values())

        def search(data: Any) -> None:

            if isinstance(data, dict):

                for key in ("siglaTribunal", "sigla"):
                    value = data.get(key)

                    if isinstance(value, str):
                        normalized = value.strip().upper()

                        if normalized in known_courts:
                            siglas.add(normalized)

                for value in data.values():
                    if isinstance(value, (dict, list)):
                        search(value)

            elif isinstance(data, list):

                for item in data:
                    search(item)

        search(response)

        return sorted(siglas)

    def get_available_state_courts(self) -> list[str]:
        """Retorna os tribunais identificados na API."""

        response = self.get_tribunals()

        return self.extract_tribunal_siglas(response)

    def get_communications(
        self,
        *,
        tribunal: str | None = None,
        process_number: str | None = None,
        lawyer_name: str | None = None,
        lawyer_oab: str | None = None,
        lawyer_uf: str | None = None,
        party_name: str | None = None,
        text: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        medium: str | None = None,
        page: int = 1,
        items_per_page: int = 50,
    ) -> dict[str, Any]:
        """
        Consulta comunicações processuais.

        GET /comunicacao

        Meio:
            D = Diário de Justiça Eletrônico Nacional
            E = Plataforma Nacional de Editais
        """

        if page < 1:
            raise ValueError("A página deve ser maior ou igual a 1.")

        if items_per_page < 1:
            raise ValueError("items_per_page deve ser maior que zero.")

        if medium and medium.upper() not in self.VALID_MEDIA:
            raise ValueError("Meio inválido. Utilize D ou E.")

        params = {
            "siglaTribunal": tribunal.upper() if tribunal else None,
            "numeroProcesso": process_number,
            "nomeAdvogado": lawyer_name,
            "numeroOab": lawyer_oab,
            "ufOab": lawyer_uf.upper() if lawyer_uf else None,
            "nomeParte": party_name,
            "texto": text,
            "dataDisponibilizacaoInicio": date_start,
            "dataDisponibilizacaoFim": date_end,
            "meio": medium.upper() if medium else None,
            "pagina": page,
            "itensPorPagina": items_per_page,
        }

        params = {
            key: value
            for key, value in params.items()
            if value is not None
        }

        response = self._get(
            "comunicacao",
            params=params,
        )

        if not isinstance(response, dict):
            raise ValueError(
                "A API de comunicações não retornou um objeto JSON."
            )

        return response

    def iter_communications(
        self,
        *,
        max_pages: int | None = None,
        **filters: Any,
    ) -> Iterator[dict[str, Any]]:
        """
        Percorre as páginas e entrega uma comunicação por vez.
        """

        page = 1
        items_per_page = filters.get("items_per_page", 50)

        while max_pages is None or page <= max_pages:

            response = self.get_communications(
                page=page,
                **filters,
            )

            items = response.get("items")

            if items is None:
                raise ValueError(
                    "A resposta da API não contém o campo 'items'. "
                    f"Campos recebidos: {list(response.keys())}"
                )

            if not isinstance(items, list):
                raise ValueError(
                    "O campo 'items' da API não retornou uma lista."
                )

            if not items:
                break

            yield from items

            if len(items) < items_per_page:
                break

            page += 1

    def search_process(
        self,
        process_number: str,
        tribunal: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Busca comunicações de um processo."""

        normalized_number = "".join(
            char
            for char in process_number
            if char.isdigit()
        )

        if not normalized_number:
            raise ValueError("Número de processo inválido.")

        return self.iter_communications(
            tribunal=tribunal,
            process_number=normalized_number,
            date_start=date_start,
            date_end=date_end,
        )

    def download_caderno(
        self,
        tribunal: str,
        publication_date: str,
        medium: str = "D",
    ) -> bytes:
        """
        Consulta e baixa o caderno de um tribunal.

        GET /caderno/{sigla_tribunal}/{data}/{meio}

        Args:
            tribunal:
                Sigla do tribunal, exemplo TJPE.

            publication_date:
                Data no formato YYYY-MM-DD.

            medium:
                D = Diário de Justiça Eletrônico Nacional.
                E = Plataforma Nacional de Editais.

        Returns:
            Conteúdo binário retornado pelo endpoint.
        """

        tribunal = tribunal.strip().upper()
        medium = medium.strip().upper()

        if not tribunal:
            raise ValueError("A sigla do tribunal é obrigatória.")

        if medium not in self.VALID_MEDIA:
            raise ValueError("Meio inválido. Utilize D ou E.")

        try:
            date.fromisoformat(publication_date)
        except ValueError as error:
            raise ValueError(
                "Data inválida. Utilize o formato YYYY-MM-DD."
            ) from error

        endpoint = (
            f"caderno/{quote(tribunal, safe='')}/"
            f"{quote(publication_date, safe='')}/"
            f"{quote(medium, safe='')}"
        )

        url = f"{self.BASE_URL}/{endpoint}"

        response = self.session.get(
            url,
            timeout=self.timeout,
            headers={"Accept": "application/pdf, application/octet-stream"},
        )

        response.raise_for_status()

        if not response.content:
            raise ValueError(
                f"O caderno do tribunal {tribunal} "
                f"não possui conteúdo para {publication_date}."
            )

        content_type = response.headers.get("Content-Type", "").lower()

        if "application/json" in content_type:
            raise ValueError(
                "A API retornou JSON em vez do conteúdo do caderno. "
                f"Resposta: {response.text[:500]}"
            )

        return response.content

    def close(self) -> None:
        """Encerra a sessão HTTP."""

        self.session.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.close()

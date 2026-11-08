
from collections.abc import Iterator
from typing import Any

import requests


class ComunicaPjeService:
    """
    Cliente da API pública Comunica PJe / DJEN do CNJ.

    Documentação:
        https://hcomunicaapi.cnj.jus.br/swagger/index.html

    API de produção:
        https://comunicaapi.pje.jus.br/api/v1
    """

    BASE_URL = "https://comunicaapi.pje.jus.br/api/v1"

    # Tribunais de Justiça estaduais e Distrito Federal.
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
        """
        Executa uma requisição GET na API.

        Retorna o JSON original, sem presumir que a resposta
        será necessariamente um dicionário.

        Isso é importante porque /comunicacao/tribunal
        pode retornar uma estrutura diferente de /comunicacao.
        """

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
        Retorna os tribunais cadastrados na API.

        Endpoint:
            GET /comunicacao/tribunal

        A resposta é mantida em seu formato original,
        pois não se deve presumir que seja um dict.
        """

        return self._get("comunicacao/tribunal")

    def get_state_courts(self) -> dict[str, str]:
        """
        Retorna o mapeamento dos TJs estaduais e do TJDFT.

        Essa lista representa os tribunais conhecidos.
        Não significa que todos estejam necessariamente
        cadastrados ou ativos na API.
        """

        return self.STATE_COURTS.copy()

    def extract_tribunal_siglas(
        self,
        response: Any,
    ) -> list[str]:
        """
        Extrai siglas de tribunais de uma resposta JSON.

        Aceita estruturas aninhadas em listas e dicionários.
        """

        siglas = set()

        def search(data: Any):

            if isinstance(data, dict):

                sigla = (
                    data.get("siglaTribunal")
                    or data.get("sigla")
                )

                if isinstance(sigla, str):
                    siglas.add(sigla.upper().strip())

                for value in data.values():

                    if isinstance(value, (dict, list)):
                        search(value)

            elif isinstance(data, list):

                for item in data:
                    search(item)

            elif isinstance(data, str):

                siglas.add(data.upper().strip())

        search(response)

        # Considera apenas os tribunais conhecidos no mapeamento.
        known_courts = set(self.STATE_COURTS.values())

        return sorted(
            sigla
            for sigla in siglas
            if sigla in known_courts
        )

    def get_available_state_courts(self) -> list[str]:
        """
        Retorna os tribunais estaduais identificados
        na listagem disponibilizada pela API.
        """

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

        Datas:
            YYYY-MM-DD

        Meio:
            D = Diário de Justiça Eletrônico Nacional
            E = Plataforma Nacional de Editais
        """

        if page < 1:
            raise ValueError(
                "A página deve ser maior ou igual a 1."
            )

        if items_per_page < 1:
            raise ValueError(
                "items_per_page deve ser maior que zero."
            )

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

        max_pages:
            Limita a quantidade de páginas consultadas.

        Sem max_pages:
            Continua até encontrar uma página vazia
            ou uma página com menos itens que o limite.
        """

        page = 1
        items_per_page = filters.get("items_per_page", 50)

        while max_pages is None or page <= max_pages:

            response = self.get_communications(
                page=page,
                **filters,
            )

            items = response.get("items", [])

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
        """
        Atalho para buscar comunicações de um processo.
        """

        normalized_number = "".join(
            char
            for char in process_number
            if char.isdigit()
        )

        if not normalized_number:
            raise ValueError(
                "Número de processo inválido."
            )

        return self.iter_communications(
            tribunal=tribunal,
            process_number=normalized_number,
            date_start=date_start,
            date_end=date_end,
        )

    def close(self) -> None:
        """
        Encerra a sessão HTTP.
        """

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

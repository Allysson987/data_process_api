import json
import time

from datetime import date, timedelta
from pathlib import Path

from app.use_cases.diary_office.office_diary_nation import (
    ComunicaPjeService
)


def test_consultar_notificacoes_por_estado():

    service = ComunicaPjeService()

    # Últimos 7 dias
    data_fim = date.today()
    data_inicio = data_fim - timedelta(days=7)

    output_dir = Path("outputs/comunica_pje")
    output_dir.mkdir(parents=True, exist_ok=True)

    resultados = {}
    estados_com_notificacoes = []

    try:

        # 1. Buscar tribunais disponíveis
        tribunais_response = service.get_tribunals()

        siglas = service.extract_tribunal_siglas(
            tribunais_response
        )

        assert siglas, "Nenhum tribunal foi identificado na API."

        print(f"\nTribunais encontrados: {len(siglas)}")

        # 2. Consultar cada Tribunal de Justiça
        for tribunal in siglas:

            print(f"\nConsultando {tribunal}...")

            try:

                response = service.get_communications(
                    tribunal=tribunal,
                    date_start=data_inicio,
                    date_end=data_fim,
                    page=1,
                    items_per_page=50
                )

                items = response.get("items", [])

                resultados[tribunal] = {
                    "count": response.get("count", 0),
                    "quantidade_recebida": len(items),
                    "items": items
                }

                if items:
                    estados_com_notificacoes.append(tribunal)

                    print(
                        f"[COM PUBLICAÇÕES] {tribunal}: "
                        f"{len(items)} registros recebidos"
                    )

                else:
                    print(f"[SEM PUBLICAÇÕES] {tribunal}")

            except Exception as error:

                print(f"[ERRO] {tribunal}: {error}")

            # Evita disparar várias requisições em sequência
            time.sleep(0.3)

        # 3. Salvar dados completos
        arquivo = output_dir / "notificacoes.json"

        with arquivo.open("w", encoding="utf-8") as file:
            json.dump(
                resultados,
                file,
                ensure_ascii=False,
                indent=4
            )

        # 4. Gerar relatório de estados
        relatorio = {
            "periodo": {
                "inicio": data_inicio.isoformat(),
                "fim": data_fim.isoformat()
            },
            "estados_com_notificacoes": estados_com_notificacoes,
            "total_estados": len(estados_com_notificacoes)
        }

        relatorio_path = output_dir / "relatorio_estados.json"

        with relatorio_path.open("w", encoding="utf-8") as file:
            json.dump(
                relatorio,
                file,
                ensure_ascii=False,
                indent=4
            )

        print("\n========== RESULTADO ==========")

        print("Período:", data_inicio, "até", data_fim)

        print(
            "Estados com publicações:",
            estados_com_notificacoes
        )

        print(
            "Total de estados:",
            len(estados_com_notificacoes)
        )

        print("\nArquivos gerados:")
        print(arquivo)
        print(relatorio_path)

    finally:
        service.close()
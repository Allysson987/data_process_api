import requests

url = (
    "https://dje-publico.svc.tjpe.jus.br"
    "/api/diario-eletronicos/recentes"
)

diarios = requests.get(url).json()

for diario in diarios:

    diario_id = diario["id"]

    pdf = requests.get(
        f"https://dje-publico.svc.tjpe.jus.br"
        f"/api/diario-eletronicos/{diario_id}/download"
    )

    with open(
        f"dje_{diario_id}.pdf",
        "wb"
    ) as file:
        file.write(pdf.content)
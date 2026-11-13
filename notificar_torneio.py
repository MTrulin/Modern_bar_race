import csv
import io
import json
import os
import urllib.request

SPREADSHEET_ID = "1BjaihYOGkMi5TJyt8fOigRs7er7e0XbHoNbsaU48yy4"
ABA = "Pontos_ate_semana"
NTFY_TOPICO = "rank-modern-bora-2026-x9k2"  # <-- Coloque o MESMO nome do app ntfy
SITE_URL = ""  # <-- Opcional: cole o link https:// do seu site no GitHub Pages
ARQUIVO_ESTADO = "ultima_data.txt"


def enviar_ntfy(titulo, mensagem):
    dados = {
        "topic": NTFY_TOPICO.strip(),
        "title": titulo,
        "message": mensagem,
        "priority": 4,
        "tags": ["trophy", "sparkles"],
    }
    if SITE_URL.startswith("http"):
        dados["click"] = SITE_URL

    req = urllib.request.Request(
        "https://ntfy.sh",
        data=json.dumps(dados).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        print("Status ntfy:", resp.status, resp.read().decode("utf-8", errors="ignore"))


def ler_planilha():
    url = (
        f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq"
        f"?tqx=out:csv&sheet={ABA}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        texto = resp.read().decode("utf-8")
    return list(csv.reader(io.StringIO(texto)))


def main():
    if os.environ.get("MODO_TESTE") == "true":
        enviar_ntfy(
            "Teste Rank Modern",
            "Conexão do GitHub Actions com o ntfy funcionando! Você será avisado quando entrar um novo torneio.",
        )
        return

    linhas = ler_planilha()
    if len(linhas) < 2 or len(linhas[0]) < 3:
        print("Planilha vazia ou formato inesperado.")
        return

    cabecalho = linhas[0]
    ultima_data = ""
    for i in range(len(cabecalho) - 1, 1, -1):
        val = cabecalho[i].strip()
        if val:
            ultima_data = val
            break

    if not ultima_data:
        print("Nenhuma data encontrada.")
        return

    data_salva = ""
    if os.path.exists(ARQUIVO_ESTADO):
        with open(ARQUIVO_ESTADO, "r", encoding="utf-8") as f:
            data_salva = f.read().strip()

    if not data_salva:
        with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
            f.write(ultima_data)
        print("Primeira execução: memorizada a data atual:", ultima_data)
        return

    if ultima_data == data_salva:
        print("Nenhuma novidade. Última data continua sendo:", ultima_data)
        return

    enviar_ntfy(
        f"Novo Torneio Modern ({ultima_data})",
        f"Um novo torneio ({ultima_data}) foi inserido na planilha.",
    )

    with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
        f.write(ultima_data)


if __name__ == "__main__":
    main()

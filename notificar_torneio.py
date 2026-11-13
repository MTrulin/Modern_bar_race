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
    ultima_col = -1
    ultima_data = ""
    for i in range(len(cabecalho) - 1, 1, -1):
        val = cabecalho[i].strip()
        if val:
            ultima_col = i
            ultima_data = val
            break

    if ultima_col == -1 or not ultima_data:
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

    col_ant = ultima_col - 1 if ultima_col > 2 else -1
    ranking = []
    max_ganho = 0
    mvps = []

    for linha in linhas[1:]:
        if len(linha) <= ultima_col:
            continue
        nome = linha[0].strip()
        if not nome:
            continue
        try:
            atual = float(linha[ultima_col].replace(",", ".") or 0)
        except ValueError:
            atual = 0.0
        anterior = 0.0
        if col_ant >= 2 and len(linha) > col_ant:
            try:
                anterior = float(linha[col_ant].replace(",", ".") or 0)
            except ValueError:
                anterior = 0.0

        ganho = round(atual - anterior)
        ranking.append((atual, nome))
        if ganho > max_ganho:
            max_ganho = ganho
            mvps = [nome]
        elif ganho > 0 and ganho == max_ganho:
            mvps.append(nome)

    ranking.sort(reverse=True)

    msg = f"Nova data registrada na planilha: {ultima_data}\n"
    if max_ganho > 0 and mvps:
        msg += f"🔥 MVP da semana: {' & '.join(mvps)} (+{max_ganho} pts)\n"
    if len(ranking) >= 3:
        msg += (
            f"🏆 Top 3: 1º {ranking[0][1]} ({int(ranking[0][0])}) | "
            f"2º {ranking[1][1]} ({int(ranking[1][0])}) | "
            f"3º {ranking[2][1]} ({int(ranking[2][0])})"
        )

    enviar_ntfy(f"Novo Torneio Modern ({ultima_data})", msg)

    with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
        f.write(ultima_data)


if __name__ == "__main__":
    main()

"""
Lucro vs. caixa operacional: do arquivo no formato da CVM ate a tabela pronta para o Power BI.

Etapas (as mesmas do artigo):
  1. carregar os dados no formato ITR/DFP (valores ACUMULADOS no ano);
  2. desacumular: obter o valor isolado de cada trimestre;
  3. conferir: a soma dos 4 trimestres tem de bater com a DFP anual;
  4. calcular o gap (caixa operacional - lucro) e os testes;
  5. exportar o Excel em esquema estrela (Calendario + Fato_Trimestral) e os graficos.

Uso:  python gerar_dados_ficticios.py   (uma vez, cria a pasta dados/)
      python analise_lucro_caixa.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

AQUI = Path(__file__).resolve().parent
DADOS, SAIDA = AQUI / "dados", AQUI / "saida"

RESULTADO = ["receita_liquida", "resultado_bruto", "resultado_antes_financeiro_tributos",
             "resultado_financeiro", "resultado_antes_tributos", "lucro_liquido"]            # DRE
FLUXO = ["caixa_operacional", "caixa_investimento", "caixa_financiamento"]                   # DFC
SALDO = ["divida_bruta", "divida_liquida", "caixa_e_equivalentes"]                           # balanco

CINZA, VERDE, VERMELHO = "#595959", "#007E7A", "#991310"


# ---------------------------------------------------------------------------------------------------
# 1. Carga
# ---------------------------------------------------------------------------------------------------
def carregar():
    df = pd.read_csv(DADOS / "resultados_itr_dfp.csv", parse_dates=["periodo_inicio", "periodo_fim"])
    df["ano"] = df["periodo_fim"].dt.year
    df["mes_inicio"] = df["periodo_inicio"].dt.month
    df["mes_fim"] = df["periodo_fim"].dt.month
    return df


# ---------------------------------------------------------------------------------------------------
# 2. Desacumular: do acumulado no ano (YTD) para o trimestre isolado
# ---------------------------------------------------------------------------------------------------
def desacumular(df):
    """Fluxos (DRE e DFC) viram valor isolado = acumulado ate o trimestre - acumulado ate o anterior.
    Saldos de balanco NAO sao desacumulados: sao a posicao no fim do periodo."""
    ytd = df[df["mes_inicio"] == 1].set_index(["ano", "mes_fim"]).sort_index()   # so as linhas que comecam em janeiro
    linhas = []
    for (ano, mes_fim), atual in ytd.iterrows():
        tri = mes_fim // 3
        linha = {"trimestre": f"{ano}-Q{tri}", "ano": ano, "numero_trimestre": tri}
        anterior = ytd.loc[(ano, mes_fim - 3)] if tri > 1 else None
        for col in RESULTADO + FLUXO:
            linha[col] = atual[col] - (anterior[col] if anterior is not None else 0)
        for col in SALDO:
            linha[col] = atual[col]
        linhas.append(linha)
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------------------------------
# 3. Conferencia: soma dos 4 trimestres x DFP anual
# ---------------------------------------------------------------------------------------------------
def conferir(df, tri):
    dfp = df[df["tipo_relatorio"] == "DFP"].set_index("ano")
    soma = tri[tri["ano"].isin(dfp.index)].groupby("ano")[RESULTADO + FLUXO].sum()
    diferenca = (soma - dfp[RESULTADO + FLUXO]).abs().max().max()
    assert diferenca < 1, f"a soma dos trimestres nao bate com a DFP (maior diferenca: {diferenca})"
    return diferenca


# ---------------------------------------------------------------------------------------------------
# 4. Metricas e testes
# ---------------------------------------------------------------------------------------------------
def metricas(tri):
    ponte = pd.read_csv(DADOS / "conciliacao_dfc.csv")
    m = tri.merge(ponte.drop(columns="caixa_operacional"), on="trimestre", how="left")
    m["gap"] = m["caixa_operacional"] - m["lucro_liquido"]                 # > 0: caixa acima do lucro
    m["prejuizo_com_caixa_positivo"] = (m["lucro_liquido"] < 0) & (m["caixa_operacional"] > 0)
    m["rotulo"] = m["numero_trimestre"].astype(str) + "T" + (m["ano"] % 100).astype(str)
    return m


def testes(m):
    r, p = stats.pearsonr(m["lucro_liquido"], m["caixa_operacional"])
    sem = m[~m["prejuizo_com_caixa_positivo"]]
    r_sem, p_sem = stats.pearsonr(sem["lucro_liquido"], sem["caixa_operacional"])
    abaixo = m[m["gap"] < 0]                                              # trimestres com caixa abaixo do lucro
    r_giro, p_giro = stats.pearsonr(abaixo["gap"], abaixo["variacao_capital_giro"])
    return dict(
        n=len(m), n_prejuizo_caixa_positivo=int(m["prejuizo_com_caixa_positivo"].sum()),
        r=r, p=p, r_sem_prejuizos=r_sem, p_sem_prejuizos=p_sem,
        n_caixa_abaixo=len(abaixo), em_2t_3t=int(abaixo["numero_trimestre"].isin([2, 3]).sum()),
        r_giro=r_giro, p_giro=p_giro,
        gap_medio_por_posicao=(m.groupby("numero_trimestre")["gap"].mean() / 1e6).round(2).to_dict(),
    )


# ---------------------------------------------------------------------------------------------------
# 5. Saidas: Excel em esquema estrela + graficos
# ---------------------------------------------------------------------------------------------------
def exportar_excel(m):
    calendario = m[["trimestre", "ano", "numero_trimestre", "rotulo"]].copy()
    calendario["ordem"] = range(1, len(calendario) + 1)
    calendario["posicao"] = calendario["numero_trimestre"].astype(str) + "T"
    fato = m.drop(columns=["ano", "numero_trimestre", "rotulo"])
    caminho = SAIDA / "lucro_caixa_tratado.xlsx"
    with pd.ExcelWriter(caminho, engine="openpyxl") as xl:
        calendario.to_excel(xl, sheet_name="Calendario", index=False)
        fato.to_excel(xl, sheet_name="Fato_Trimestral", index=False)
    return caminho


def bi(serie):
    return serie / 1e6          # R$ mil -> R$ bilhoes


def grafico_acumulado_x_isolado(df, m, ano=2024):
    """A pegadinha em uma figura: o que o arquivo traz (acumulado) x o que a analise precisa (isolado)."""
    ytd = df[(df["mes_inicio"] == 1) & (df["ano"] == ano)].sort_values("mes_fim")
    iso = m[m["ano"] == ano]
    fig, ax = plt.subplots(figsize=(10, 4.6), dpi=200)
    x = range(4)
    ax.bar([i - 0.2 for i in x], bi(ytd["caixa_operacional"]), width=0.4, color="#B8C4C4", label="Acumulado no ano (como vem no arquivo)")
    ax.bar([i + 0.2 for i in x], bi(iso["caixa_operacional"]), width=0.4, color=VERDE, label="Isolado no trimestre (o que a análise precisa)")
    for i, (a, b) in enumerate(zip(bi(ytd["caixa_operacional"]), bi(iso["caixa_operacional"]))):
        ax.text(i - 0.2, a + 0.15, f"{a:.1f}".replace(".", ","), ha="center", fontsize=10, color="#555")
        ax.text(i + 0.2, b + 0.15, f"{b:.1f}".replace(".", ","), ha="center", fontsize=10, color=VERDE, fontweight="bold")
    ax.set_xticks(list(x), [f"{q}T{ano % 100}" for q in range(1, 5)])
    ax.set_title(f"Caixa operacional em {ano}: acumulado x isolado (R$ bilhões)", loc="left", fontsize=12, fontweight="bold")
    ax.legend(frameon=False, loc="upper left")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(left=False, labelleft=False)
    ax.set_ylim(0, bi(ytd["caixa_operacional"]).max() * 1.25)
    fig.tight_layout()
    fig.savefig(SAIDA / "acumulado_x_isolado.png")
    plt.close(fig)


def grafico_dispersao(m, t):
    """Lucro x caixa por trimestre, com os dois trimestres de prejuizo em destaque."""
    fig, ax = plt.subplots(figsize=(10, 5.4), dpi=200)
    normal, prej = m[~m["prejuizo_com_caixa_positivo"]], m[m["prejuizo_com_caixa_positivo"]]
    ax.scatter(bi(normal["lucro_liquido"]), bi(normal["caixa_operacional"]), s=90, color=VERDE, zorder=3, label="Trimestres com lucro")
    ax.scatter(bi(prej["lucro_liquido"]), bi(prej["caixa_operacional"]), s=130, color=VERMELHO, zorder=3, label="Prejuízo contábil com caixa positivo")
    for i, l in m.iterrows():
        ax.annotate(l["rotulo"], (bi(l["lucro_liquido"]), bi(l["caixa_operacional"])), textcoords="offset points",
                    xytext=(8, 6) if i % 2 == 0 else (8, -13), fontsize=9, color="#444")   # alterna para nao sobrepor
    ax.axvline(0, color="#999", lw=0.8)
    lim = [0, bi(m[["lucro_liquido", "caixa_operacional"]]).max().max() * 1.1]
    ax.plot(lim, lim, ls="--", color="#999", lw=1, label="Caixa = lucro")
    ax.set_xlabel("Lucro líquido do trimestre (R$ bilhões)")
    ax.set_ylabel("Caixa operacional do trimestre (R$ bilhões)")
    f = lambda v: f"{v:+.2f}".replace(".", ",")
    ax.set_title(f"Lucro x caixa em {t['n']} trimestres: r = {f(t['r'])} (todos) e r = {f(t['r_sem_prejuizos'])} (sem os dois prejuízos)",
                 loc="left", fontsize=12, fontweight="bold")
    ax.legend(frameon=False, loc="lower left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(color="#eee", zorder=0)
    fig.tight_layout()
    fig.savefig(SAIDA / "dispersao_lucro_caixa.png")
    plt.close(fig)


def main():
    SAIDA.mkdir(exist_ok=True)
    df = carregar()
    tri = desacumular(df)
    diferenca = conferir(df, tri)
    m = metricas(tri)
    t = testes(m)
    caminho = exportar_excel(m)
    grafico_acumulado_x_isolado(df, m)
    grafico_dispersao(m, t)

    print(f"Trimestres isolados: {len(tri)}  |  maior diferença contra a DFP: R$ {diferenca:.0f} mil")
    print(f"Prejuízo contábil com caixa operacional positivo: {t['n_prejuizo_caixa_positivo']} de {t['n']} trimestres")
    print(f"Correlação lucro x caixa: r = {t['r']:+.2f} (p = {t['p']:.2f})")
    print(f"  sem os trimestres de prejuízo: r = {t['r_sem_prejuizos']:+.2f} (p = {t['p_sem_prejuizos']:.2f})")
    print(f"Caixa abaixo do lucro em {t['n_caixa_abaixo']} trimestres, {t['em_2t_3t']} deles no 2T ou 3T")
    print(f"  gap x capital de giro nesses trimestres: r = {t['r_giro']:+.2f} (p = {t['p_giro']:.2f})")
    print(f"Gap médio por posição do trimestre (R$ bi): {t['gap_medio_por_posicao']}")
    print(f"Excel para o Power BI: {caminho}")
    return m, t


if __name__ == "__main__":
    main()

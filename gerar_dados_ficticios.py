"""
Gera os dados FICTICIOS da "Mineradora Pedra Clara S.A." usados no artigo.

A empresa nao existe. Os numeros foram escritos a mao (nao ha sorteio) para reproduzir, em escala
menor, o tipo de padrao que aparece em demonstracoes reais: dois trimestres de prejuizo contabil
causados por baixa de ativos (lancamento sem saida de caixa) e um caixa operacional que segue firme.

Saidas, no mesmo formato em que a CVM publica (dados.cvm.gov.br, ITR e DFP):

  dados/resultados_itr_dfp.csv   linhas ITR ACUMULADAS no ano (YTD) + linha DFP do ano fechado
  dados/conciliacao_dfc.csv      ponte lucro -> caixa operacional (DFC, metodo indireto), por trimestre

Valores monetarios em R$ mil, como nos arquivos da CVM.

Uso:  python gerar_dados_ficticios.py
"""

from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
DADOS = AQUI / "dados"

TRIMESTRES = [f"{ano}-Q{q}" for ano in (2023, 2024, 2025) for q in (1, 2, 3, 4)] + ["2026-Q1", "2026-Q2"]

# ---- premissas por trimestre, em R$ bilhoes (1T23 ... 2T26) ----------------------------------------
RECEITA    = [11.2, 12.6, 13.4, 14.1, 10.8, 12.9, 13.8, 13.6, 10.5, 12.4, 13.1, 13.9, 11.0, 12.8]
MARGEM     = [0.41, 0.40, 0.42, 0.43, 0.39, 0.41, 0.40, 0.38, 0.37, 0.39, 0.40, 0.37, 0.39, 0.41]
DESPESAS   = [-1.3, -1.4, -1.4, -1.6, -1.3, -1.4, -1.5, -1.9, -1.3, -1.4, -1.5, -2.2, -1.3, -1.4]
BAIXAS     = [0.02, 0.05, 0.04, 0.10, 0.03, 0.06, 0.05, 3.90, 0.04, 0.05, 0.08, 7.40, 0.03, 0.05]   # sem saida de caixa
FINANCEIRO = [-0.5, -0.3, -0.6, -0.4, -0.7, -0.2, -0.6, -1.9, -0.5, -0.4, -0.6, -1.2, -0.4, -0.5]
EVENTO     = [-0.05, -0.08, -0.06, -0.20, -0.04, -0.07, -0.05, -0.25, -0.05, -0.06, -0.05, -0.22, -0.04, -0.06]
ALIQUOTA   = 0.26                              # tributos sobre o resultado positivo
CREDITO_TRIBUTARIO = {7: 0.50, 11: 1.30}       # nos dois trimestres de prejuizo (indices de 4T24 e 4T25)

# ponte lucro -> caixa operacional (DFC, metodo indireto)
OUTROS_AJUSTES = [1.55, 1.60, 1.65, 1.70, 1.60, 1.65, 1.70, 1.75, 1.65, 1.70, 1.75, 1.85, 1.70, 1.75]   # depreciacao etc.
CONTAS_RECEBER = [1.10, -0.90, -0.60, 0.30, 0.90, -1.10, -1.40, 0.50, -0.70, -0.80, -0.50, 0.40, 0.80, -0.20]
ESTOQUES       = [-0.30, -0.40, -0.10, 0.20, -0.20, -0.50, -0.10, 0.20, -0.30, -0.40, 0.10, 0.10, -0.20, -0.30]
FORNECEDORES   = [-0.10, 0.20, 0.10, 0.10, -0.20, 0.30, 0.20, -0.10, -0.10, 0.20, 0.10, -0.10, -0.10, 0.20]
OUTROS_GIRO    = [0.10, -0.20, 0.10, -0.10, 0.10, -0.20, 0.10, 0.00, -0.10, -0.10, 0.10, -0.10, 0.00, -0.10]
OUTROS_ITENS   = [-1.00, -1.25, -1.10, -1.05, -1.00, -1.30, -1.15, -0.90, -1.35, -1.45, -1.05, -1.20, -1.00, -1.25]  # juros e tributos pagos

INVESTIMENTO  = [-1.6, -1.8, -1.9, -2.3, -1.5, -1.7, -2.0, -2.4, -1.6, -1.8, -1.9, -2.2, -1.5, -1.8]
FINANCIAMENTO = [-1.6, -0.3, -1.0, -1.4, -1.7, 1.1, -1.0, -0.6, -1.0, 0.9, -1.0, -1.3, -1.5, -0.2]
DIVIDA_BRUTA  = [14.0, 14.6, 14.4, 14.2, 14.1, 16.0, 15.8, 16.3, 16.0, 17.2, 17.0, 16.8, 16.5, 16.9]   # saldo no fim do trimestre
APLICACOES    = [0.30, 0.28, 0.31, 0.30, 0.29, 0.33, 0.30, 0.31, 0.28, 0.30, 0.32, 0.30, 0.29, 0.31]
PASSIVO_TOTAL = [58.0, 58.6, 58.9, 59.4, 59.0, 61.2, 61.0, 62.5, 62.1, 63.4, 63.1, 64.0, 63.6, 64.1]
PROVISAO      = [3.40, 3.36, 3.31, 3.30, 3.24, 3.20, 3.15, 3.22, 3.16, 3.10, 3.05, 3.12, 3.06, 3.00]
CAIXA_INICIAL = 6.0


def mil(v):
    """R$ bilhoes -> R$ mil, arredondado ao milhar (como nos arquivos da CVM)."""
    return float(round(v * 1e6 / 1000) * 1000)


def trimestres_isolados():
    """Uma linha por trimestre com o valor ISOLADO (so daquele trimestre), em R$ bilhoes."""
    linhas, caixa = [], CAIXA_INICIAL
    for i, tri in enumerate(TRIMESTRES):
        bruto = RECEITA[i] * MARGEM[i]
        ebit = bruto + DESPESAS[i] - BAIXAS[i]
        rat = ebit + FINANCEIRO[i]
        tributos = CREDITO_TRIBUTARIO.get(i, -ALIQUOTA * rat)
        lucro = rat + tributos
        giro = CONTAS_RECEBER[i] + ESTOQUES[i] + FORNECEDORES[i] + OUTROS_GIRO[i]
        caixa_gerado = lucro + BAIXAS[i] + OUTROS_AJUSTES[i]
        fco = caixa_gerado + giro + OUTROS_ITENS[i]
        caixa += fco + INVESTIMENTO[i] + FINANCIAMENTO[i]
        linhas.append(dict(
            trimestre=tri, receita_liquida=RECEITA[i], resultado_bruto=bruto, evento_extraordinario=EVENTO[i],
            resultado_antes_financeiro_tributos=ebit, resultado_financeiro=FINANCEIRO[i],
            resultado_antes_tributos=rat, lucro_liquido=lucro,
            caixa_operacional=fco, caixa_investimento=INVESTIMENTO[i], caixa_financiamento=FINANCIAMENTO[i],
            passivo_total=PASSIVO_TOTAL[i], divida_bruta=DIVIDA_BRUTA[i],
            divida_liquida=DIVIDA_BRUTA[i] - caixa - APLICACOES[i], provisao_total=PROVISAO[i],
            caixa_e_equivalentes=caixa, aplicacoes_financeiras=APLICACOES[i],
            caixa_gerado_operacoes=caixa_gerado, baixa_ativos=BAIXAS[i], variacao_capital_giro=giro,
            variacao_contas_a_receber=CONTAS_RECEBER[i], variacao_estoques=ESTOQUES[i],
            variacao_fornecedores=FORNECEDORES[i], variacao_outros=OUTROS_GIRO[i], outros_itens_operacionais=OUTROS_ITENS[i],
        ))
    df = pd.DataFrame(linhas)
    for c in df.columns.drop("trimestre"):
        df[c] = df[c].map(mil)
    # depois do arredondamento, refaz as somas para as identidades fecharem exatamente em R$ mil
    df["resultado_antes_tributos"] = df["resultado_antes_financeiro_tributos"] + df["resultado_financeiro"]
    df["variacao_capital_giro"] = df[["variacao_contas_a_receber", "variacao_estoques",
                                      "variacao_fornecedores", "variacao_outros"]].sum(axis=1)
    df["caixa_gerado_operacoes"] = df["caixa_operacional"] - df["variacao_capital_giro"] - df["outros_itens_operacionais"]
    df["divida_liquida"] = df["divida_bruta"] - df["caixa_e_equivalentes"] - df["aplicacoes_financeiras"]
    return df


RESULTADO = ["receita_liquida", "resultado_bruto", "evento_extraordinario", "resultado_antes_financeiro_tributos",
             "resultado_financeiro", "resultado_antes_tributos", "lucro_liquido"]
FLUXO = ["caixa_operacional", "caixa_investimento", "caixa_financiamento"]
SALDO = ["passivo_total", "divida_bruta", "divida_liquida", "provisao_total", "caixa_e_equivalentes", "aplicacoes_financeiras"]


def formato_cvm(iso):
    """Reescreve os trimestres isolados no formato de publicacao: ITR acumulado no ano + DFP anual.

    Por ano: 1T (jan-mar), 6 meses (jan-jun), 2T isolado so com a DRE (abr-jun), 9 meses (jan-set),
    3T isolado so com a DRE (jul-set) e a DFP do ano inteiro. O 4T NAO e publicado sozinho.
    """
    iso = iso.assign(ano=iso["trimestre"].str[:4].astype(int), q=iso["trimestre"].str[-1].astype(int))
    fim = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}
    inicio = {1: "01-01", 2: "04-01", 3: "07-01"}
    linhas = []
    for ano, g in iso.groupby("ano"):
        g = g.set_index("q")
        for q in g.index:
            ytd = g.loc[:q]
            base = dict(tipo_relatorio="DFP" if q == 4 else "ITR", periodo_inicio=f"{ano}-01-01",
                        periodo_fim=f"{ano}-{fim[q]}")
            base.update({c: ytd[c].sum() for c in RESULTADO + FLUXO})     # acumulado desde janeiro
            base.update({c: g.loc[q, c] for c in SALDO})                  # saldo: posicao no fim do periodo
            linhas.append(base)
            if q in (2, 3):                                               # coluna "trimestre atual" do ITR: so a DRE
                so_dre = dict(tipo_relatorio="ITR", periodo_inicio=f"{ano}-{inicio[q]}", periodo_fim=f"{ano}-{fim[q]}")
                so_dre.update({c: g.loc[q, c] for c in RESULTADO + SALDO})
                linhas.append(so_dre)
    colunas = ["tipo_relatorio", "periodo_inicio", "periodo_fim"] + RESULTADO + SALDO + FLUXO
    return pd.DataFrame(linhas)[colunas].sort_values(["periodo_fim", "periodo_inicio"]).reset_index(drop=True)


def main():
    DADOS.mkdir(exist_ok=True)
    iso = trimestres_isolados()
    formato_cvm(iso).to_csv(DADOS / "resultados_itr_dfp.csv", index=False)
    iso[["trimestre", "caixa_operacional", "caixa_gerado_operacoes", "baixa_ativos", "variacao_capital_giro",
         "variacao_contas_a_receber", "variacao_estoques", "variacao_fornecedores", "variacao_outros",
         "outros_itens_operacionais"]].to_csv(DADOS / "conciliacao_dfc.csv", index=False)
    print(f"2 arquivos gravados em {DADOS}")
    return iso


if __name__ == "__main__":
    main()

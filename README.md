# Lucro vs. caixa: do formato da CVM ao Power BI

Código de apoio do artigo "Python + Power BI + dados da CVM: como testar se o lucro vira caixa".

A empresa do exemplo (Mineradora Pedra Clara S.A.) **não existe**: os dados são fictícios e foram escritos no mesmo
formato em que a CVM publica o ITR e a DFP.

## Passo a passo em notebook

[`passo_a_passo.ipynb`](passo_a_passo.ipynb) percorre as etapas em Python do artigo, com o código e o resultado de cada uma.
Dá para ler aqui mesmo no GitHub ou executar no navegador:

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Rodrigo-Antonio-Silva/caixa-lucro/blob/main/passo_a_passo.ipynb)

## Como rodar

```
pip install -r requirements.txt
python gerar_dados_ficticios.py
python analise_lucro_caixa.py
```

Saída esperada:

```
Trimestres isolados: 14  |  maior diferença contra a DFP: R$ 0 mil
Prejuízo contábil com caixa operacional positivo: 2 de 14 trimestres
Correlação lucro x caixa: r = -0.40 (p = 0.16)
  sem os trimestres de prejuízo: r = +0.28 (p = 0.37)
Caixa abaixo do lucro em 5 trimestres, 4 deles no 2T ou 3T
  gap x capital de giro nesses trimestres: r = +0.76 (p = 0.13)
```

## Arquivos

| Arquivo | O que é |
|---|---|
| `gerar_dados_ficticios.py` | Cria `dados/resultados_itr_dfp.csv` (acumulado no ano, como na CVM) e `dados/conciliacao_dfc.csv` |
| `analise_lucro_caixa.py` | Desacumula os trimestres, confere contra a DFP, calcula o gap e os testes, exporta o Excel e os gráficos |
| `passo_a_passo.ipynb` | As mesmas etapas do script, célula por célula, com tabelas e gráficos; termina conferindo os números do artigo |
| `saida/lucro_caixa_tratado.xlsx` | Abas `Calendario` e `Fato_Trimestral`, prontas para o Power BI |

Valores monetários em R$ mil.

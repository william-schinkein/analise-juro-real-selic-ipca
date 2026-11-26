# Pergunta: Quem deixou o dinheiro parado rendendo 100% da Selic nos últimos 5 anos realmente ganhou poder de compra acima da inflação, ou em alguns momentos perdeu dinheiro em termos reais?

import pandas as pd
import matplotlib.pyplot as plt

# 1. Coleta desde 11/2020 (1 ano extra para alimentar a janela de 12 meses)
url_selic = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.4390/dados?formato=json&dataInicial=25/11/2020&dataFinal=25/11/2026"
url_ipca = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial=25/11/2020&dataFinal=25/11/2026"

df_selic = pd.read_json(url_selic)
df_ipca = pd.read_json(url_ipca)

# 2. Limpeza e junção das bases
df = pd.merge(df_selic, df_ipca, on="data", suffixes=("_selic", "_ipca"))
df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
df = df.sort_values("data").reset_index(drop=True)

# 3. Cálculo do acumulado em 12 meses (usando o ano extra de 2020/2021)
df["selic_12m"] = ((1 + df["valor_selic"] / 100).rolling(12).apply(lambda x: x.prod()) - 1) * 100
df["ipca_12m"] = ((1 + df["valor_ipca"] / 100).rolling(12).apply(lambda x: x.prod()) - 1) * 100
df = df[df["data"] >= "2021-11-01"].reset_index(drop=True) # filtro para começar em 2021

# 4. Taxa Real ex-post (Equação de Fisher)
df["juro_real_12m"] = (((1 + df["selic_12m"] / 100) / (1 + df["ipca_12m"] / 100)) - 1) * 100

# 5. Simulação de R$ 1.000 investidos no início do período
df["capital_nominal"] = 1000 * (1 + df["valor_selic"] / 100).cumprod()
df["fator_inflacao"] = (1 + df["valor_ipca"] / 100).cumprod()
df["capital_real"] = df["capital_nominal"] / df["fator_inflacao"]

# Resumo executivo final
resumo = df.dropna().iloc[-1]
print(f"Período analisado: {df['data'].min().strftime('%m/%Y')} até {df['data'].max().strftime('%m/%Y')}")
print(f"Selic acumulada (últimos 12m): {resumo['selic_12m']:.2f}%")
print(f"IPCA acumulado (últimos 12m): {resumo['ipca_12m']:.2f}%")
print(f"Juro Real atual (12m): {resumo['juro_real_12m']:.2f}%")
print(f"R$ 1.000 viraram R$ {resumo['capital_nominal']:.2f} (nominal) ou R$ {resumo['capital_real']:.2f} (poder de compra real)")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)

# Gráfico 1: Selic vs IPCA (Acumulado 12m)
ax1.plot(df["data"], df["selic_12m"], label="Selic (12m %)", color="#1f77b4", linewidth=2.5)
ax1.plot(df["data"], df["ipca_12m"], label="IPCA (12m %)", color="#d62728", linewidth=2.5)
ax1.fill_between(df["data"], df["selic_12m"], df["ipca_12m"],
                 where=(df["selic_12m"] >= df["ipca_12m"]), color="#2ca02c", alpha=0.15, label="Ganho Real")
ax1.fill_between(df["data"], df["selic_12m"], df["ipca_12m"],
                 where=(df["selic_12m"] < df["ipca_12m"]), color="#d62728", alpha=0.15, label="Perda Real")
ax1.set_title("Selic vs. Inflação (Acumulado 12 Meses)", fontsize=13, fontweight="bold")
ax1.set_ylabel("% ao ano")
ax1.legend(loc="upper left")
ax1.grid(True, linestyle="--", alpha=0.5)

# Gráfico 2: Evolução de R$ 1.000 (Nominal vs. Poder de Compra Real)
ax2.plot(df["data"], df["capital_nominal"], label="Saldo Nominal (R$)", color="#1f77b4", linewidth=2.5)
ax2.plot(df["data"], df["capital_real"], label="Poder de Compra Real (R$ descontado IPCA)", color="#2ca02c", linewidth=2.5)
ax2.set_title("Evolução de R$ 1.000 Investidos: Ilusão Nominal vs. Ganho Real", fontsize=13, fontweight="bold")
ax2.set_ylabel("Valor em R$")
ax2.legend(loc="upper left")
ax2.grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
plt.savefig("resultado_selic_ipca.png", dpi=300)
plt.show()

import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
import locale

# Ajustar locale para português (Brasil)
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')

# Configurações da página
st.set_page_config(page_title="Extrator de Extratos Bancários", layout="wide")
st.title("📄 Extrator de Extratos Sicoob - Dashboard Moderno")

# Função para extrair transações
def extrair_transacoes(texto):
    linhas = texto.split('\n')
    transacoes = []
    i = 0

    while i < len(linhas) - 2:
        linha_data = linhas[i].strip()
        linha_hist = linhas[i + 1].strip()
        linha_valor = linhas[i + 2].strip()

        if re.match(r'^\d{2}/\d{2}$', linha_data) and \
           re.match(r'.+', linha_hist) and \
           re.match(r'^[\d.,]+[DC]$', linha_valor):

            data = linha_data
            historico = linha_hist
            valor_bruto = linha_valor[:-1].replace('.', '').replace(',', '.')
            tipo = linha_valor[-1]
            valor = float(valor_bruto) * (-1 if tipo == 'D' else 1)

            descricao_longa = []
            i += 3
            while i < len(linhas) and not re.match(r'^\d{2}/\d{2}$', linhas[i]):
                if linhas[i].strip():
                    descricao_longa.append(linhas[i].strip())
                i += 1
            i -= 1

            transacoes.append([data, historico, valor, " | ".join(descricao_longa)])
        i += 1

    return transacoes

# Upload de arquivos
uploaded_files = st.file_uploader("📎 Selecione os arquivos PDF dos extratos", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    todas_transacoes = []

    for arquivo in uploaded_files:
        st.info(f"🔍 Processando: **{arquivo.name}**")
        try:
            with fitz.open(stream=arquivo.read(), filetype="pdf") as doc:
                texto_completo = "".join(pagina.get_text() for pagina in doc)

            transacoes = extrair_transacoes(texto_completo)

            if transacoes:
                for linha in transacoes:
                    linha.append(arquivo.name)
                    todas_transacoes.append(linha)
            else:
                st.warning(f"⚠️ Nenhuma transação reconhecida em **{arquivo.name}**.")
        except Exception as e:
            st.error(f"Erro ao processar {arquivo.name}: {e}")

    if todas_transacoes:
        df = pd.DataFrame(todas_transacoes, columns=["Data", "Histórico", "Valor", "Descrição", "Arquivo"])
        df["Data"] = pd.to_datetime(df["Data"] + "/2024", dayfirst=True, errors='coerce')
        df = df.sort_values("Data")
        df["Tipo"] = df["Valor"].apply(lambda x: "Entrada" if x > 0 else "Saída")
        df["Saldo Acumulado"] = df["Valor"].cumsum()

        st.success(f"✅ **{len(df)}** transações extraídas.")
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        st.header("📊 Dashboard Financeiro")

        # 📈 Gráfico de saldo acumulado
        st.subheader("Saldo Acumulado")
        fig1 = px.area(df, x="Data", y="Saldo Acumulado", markers=True, title="Saldo Acumulado ao Longo do Tempo")
        fig1.update_layout(xaxis_title="Data", yaxis_title="Saldo (R$)", template="plotly_dark", height=400)
        st.plotly_chart(fig1, use_container_width=True)

        # 📉 Entradas e saídas por mês
        st.subheader("Entradas e Saídas Mensais")
        df["AnoMes"] = df["Data"].dt.strftime('%m/%Y')
        resumo = df.groupby(["AnoMes", "Tipo"])["Valor"].sum().reset_index()
        fig2 = px.bar(resumo, x="AnoMes", y="Valor", color="Tipo", barmode="group",
                      title="Entradas vs Saídas Mensais")
        fig2.update_layout(xaxis_title="Mês/Ano", yaxis_title="Valor (R$)", template="plotly_dark", height=400)
        st.plotly_chart(fig2, use_container_width=True)

        # 🥧 Gráfico Donut (filtrando < 1%)
        st.subheader("Categorias das Despesas")
        categorias = df[df["Tipo"] == "Saída"].groupby("Histórico")["Valor"].sum().reset_index()
        categorias["Valor"] = -categorias["Valor"]
        categorias = categorias[categorias["Valor"] > 0]
        total = categorias["Valor"].sum()
        categorias = categorias[categorias["Valor"] / total >= 0.01]  # >= 1%

        fig3 = px.pie(categorias, names="Histórico", values="Valor", hole=0.6,
                      title="Distribuição das Despesas")
        fig3.update_traces(textinfo='percent', textposition='inside', pull=[0.05]*len(categorias))
        fig3.update_layout(template="plotly_dark", showlegend=True, height=400)
        st.plotly_chart(fig3, use_container_width=True)

        # Exportação
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="📥 Baixar Excel com Dados",
            data=buffer,
            file_name="extrato_detalhado_sicoob.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ Nenhuma transação identificada em nenhum dos PDFs.")

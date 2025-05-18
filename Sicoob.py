import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import locale

# Ajuste de localização
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')

# Configuração da página
st.set_page_config(page_title="Dashboard Financeiro Unificado", layout="wide")
st.title("📊 Dashboard Financeiro - PDF e Excel")
st.markdown("---")

# Seletor de fonte de dados
fonte_dados = st.sidebar.radio("Escolha a fonte de dados:", ["📄 PDF", "📊 Excel"])
tipo_filtro = st.sidebar.selectbox("🔎 Filtrar por tipo:", ["Todos", "Entradas", "Saídas"])
saldo_inicial = st.sidebar.number_input("💰 Informe o saldo inicial (opcional):", value=0.0, step=100.0)

palavras_saldo = ["saldo", "saldo anterior", "saldo atual", "saldo final", "saldo inicial"]

def contem_palavra_saldo(texto):
    if isinstance(texto, str):
        texto = texto.lower()
        return any(p in texto for p in palavras_saldo)
    return False

if fonte_dados == "📄 PDF":
    import fitz
    import re

    uploaded_files = st.sidebar.file_uploader("📎 Selecione os arquivos PDF dos extratos", type=["pdf"], accept_multiple_files=True)
    ano_padrao = st.sidebar.number_input("📅 Ano dos extratos (se faltar data)", 2000, 2100, 2024)

    def extrair_transacoes(texto, ano_padrao=None):
        linhas = texto.split('\n')
        transacoes = []
        i = 0
        padrao_data = re.compile(r'^\d{2}[-/]\d{2}([-/]\d{4})?$')
        padrao_valor = re.compile(r'^[\d\.,]+[DC]?$')
        while i < len(linhas):
            linha = linhas[i].strip()
            if padrao_data.match(linha):
                data = linha
                if len(data.split('/')) == 2 and ano_padrao:
                    data = f"{data}/{ano_padrao}"
                historico, descricao, valor, tipo = "", [], None, None
                i += 1
                while i < len(linhas):
                    linha2 = linhas[i].strip()
                    if padrao_data.match(linha2):
                        break
                    if padrao_valor.match(linha2) and valor is None:
                        tipo = 'C' if linha2.endswith('C') else ('D' if linha2.endswith('D') else None)
                        valor_str = linha2.rstrip('DC').replace('.', '').replace(',', '.')
                        try:
                            valor = float(valor_str)
                            if tipo == 'D': valor = -valor
                        except:
                            valor = None
                    else:
                        if not historico and not padrao_valor.match(linha2):
                            historico = linha2
                        elif not padrao_valor.match(linha2):
                            descricao.append(linha2)
                    i += 1
                if valor is not None and historico:
                    transacoes.append([data, historico, valor, " | ".join(descricao)])
            else:
                i += 1
        return transacoes

    if uploaded_files:
        todas_transacoes = []
        for arquivo in uploaded_files:
            with fitz.open(stream=arquivo.read(), filetype="pdf") as doc:
                texto_completo = "".join(p.get_text("text") for p in doc)
            transacoes = extrair_transacoes(texto_completo, ano_padrao)
            for linha in transacoes:
                linha.append(arquivo.name)
                todas_transacoes.append(linha)

        if todas_transacoes:
            df = pd.DataFrame(todas_transacoes, columns=["Data", "Histórico", "Valor", "Descrição", "Arquivo"])
            df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors='coerce')
            df = df.dropna(subset=["Data"]).sort_values("Data")
            df["AnoMes"] = df["Data"].dt.to_period("M")
            df["Tipo"] = df["Valor"].apply(lambda x: "Entrada" if x > 0 else "Saída")
            df["Saldo Anterior"] = df["Histórico"].apply(lambda h: df["Valor"] if contem_palavra_saldo(h) else None)

            if tipo_filtro != "Todos":
                df = df[df["Tipo"] == tipo_filtro[:-1]]

            st.success(f"✅ {len(df)} transações extraídas.")

else:
    uploaded_files = st.sidebar.file_uploader("📎 Selecione as planilhas Excel", type=["xlsx"], accept_multiple_files=True)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.header(f"📁 Arquivo: {uploaded_file.name}")
            xls = pd.ExcelFile(uploaded_file)
            aba = st.selectbox(f"Selecione a aba de {uploaded_file.name}", xls.sheet_names, key=uploaded_file.name)
            df = xls.parse(aba)
            if all(col in df.columns for col in ["Data", "Valor", "Tipo"]):
                df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
                df = df.dropna(subset=["Data"]).sort_values("Data")
                df["AnoMes"] = df["Data"].dt.to_period("M")
                if "Histórico" in df.columns:
                    df["Saldo Anterior"] = df.apply(lambda r: r["Valor"] if r["Tipo"] == "Saldo" or contem_palavra_saldo(r["Histórico"]) else None, axis=1)
                else:
                    df["Saldo Anterior"] = None
                if tipo_filtro != "Todos":
                    df = df[df["Tipo"] == tipo_filtro[:-1]]
                st.success(f"✅ {len(df)} transações carregadas.")

# Se houver dados carregados, exibir dashboards
if 'df' in locals() and not df.empty:
    st.dataframe(df, use_container_width=True)
    st.markdown("---")
    st.subheader("📈 Saldo Final de Cada Mês")
    df_saldo = df[df["Saldo Anterior"].notnull()]
    fig1 = px.line(df_saldo, x="Data", y="Saldo Anterior", markers=True)
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("📉 Entradas vs Saídas")
    df_mov = df[df["Tipo"].isin(["Entrada", "Saída"])]
    if "Histórico" in df.columns:
        df_mov = df_mov[~df_mov["Histórico"].apply(contem_palavra_saldo)]
    df_mov["AnoMes"] = df_mov["Data"].dt.strftime('%m/%Y')
    resumo = df_mov.groupby(["AnoMes", "Tipo"])["Valor"].sum().reset_index()
    fig2 = px.bar(resumo, x="AnoMes", y="Valor", color="Tipo", barmode="group")
    st.plotly_chart(fig2, use_container_width=True)

    if "Histórico" in df.columns:
        st.subheader("🥧 Distribuição das Despesas")
        categorias = df[df["Tipo"] == "Saída"].groupby("Histórico")["Valor"].sum().reset_index()
        categorias["Valor"] = -categorias["Valor"]
        total = categorias["Valor"].sum()
        categorias = categorias[categorias["Valor"] / total >= 0.01]
        fig3 = px.pie(categorias, names="Histórico", values="Valor", hole=0.6)
        st.plotly_chart(fig3, use_container_width=True)

    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button(
        label="📥 Baixar Excel com Dados",
        data=buffer,
        file_name="dados_dashboard.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

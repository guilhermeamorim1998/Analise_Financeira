import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import locale
import platform

# ✅ Configuração da página - DEVE SER A PRIMEIRA INSTRUÇÃO DO STREAMLIT
st.set_page_config(page_title="Dashboard Financeiro Unificado", layout="wide")

# Ajuste de localização multiplataforma
try:
    if platform.system() == "Windows":
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
    else:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    st.warning("⚠️ Locale pt_BR.UTF-8 ou equivalente não disponível no sistema.")

st.title("📊 Dashboard Financeiro - Excel")
st.markdown("---")

# Filtros e configurações
saldo_inicial = st.sidebar.number_input("💰 Informe o saldo inicial (opcional):", value=0.0, step=100.0)
tipo_filtro = st.sidebar.selectbox("🔎 Filtrar por tipo:", ["Todos", "Entradas", "Saídas"])

palavras_saldo = ["saldo", "saldo anterior", "saldo atual", "saldo final", "saldo inicial"]

def contem_palavra_saldo(texto):
    if isinstance(texto, str):
        texto = texto.lower()
        return any(p in texto for p in palavras_saldo)
    return False

# Upload de planilhas Excel
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
                file_name=f"dados_dashboard_{uploaded_file.name}",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("❌ A aba selecionada precisa conter as colunas: Data, Valor, Tipo.")
else:
    st.info("📎 Faça o upload de planilhas Excel para iniciar a análise.")

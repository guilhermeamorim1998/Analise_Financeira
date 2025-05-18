import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import locale
import platform

# ✅ Configuração da página - DEVE SER A PRIMEIRA INSTRUÇÃO DO STREAMLIT
st.set_page_config(page_title="Dashboard Financeiro - Planilhas", layout="wide")

# Ajuste de localização multiplataforma
try:
    if platform.system() == "Windows":
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
    else:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    st.warning("⚠️ Locale pt_BR.UTF-8 ou equivalente não disponível no sistema.")

st.title("📊 Dashboard Financeiro - Estrutura Robusta com Planilhas Excel")
st.markdown("---")

# 📎 Upload de arquivos Excel com múltiplas abas
with st.sidebar:
    uploaded_files = st.file_uploader("📎 Selecione as planilhas Excel", type=["xlsx"], accept_multiple_files=True)
    tipo_filtro = st.selectbox("🔎 Filtrar por tipo:", ["Todos", "Entradas", "Saídas"])
    saldo_inicial = st.number_input("💰 Informe o saldo inicial (opcional):", value=0.0, step=100.0)

# 🔍 Palavras que indicam saldo
palavras_saldo = ["saldo", "saldo anterior", "saldo atual", "saldo final", "saldo inicial"]

def contem_palavra_saldo(texto):
    if isinstance(texto, str):
        texto = texto.lower()
        return any(p in texto for p in palavras_saldo)
    return False

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.header(f"📁 Arquivo: {uploaded_file.name}")
        xls = pd.ExcelFile(uploaded_file)
        abas = xls.sheet_names
        aba_selecionada = st.selectbox(f"Selecione a aba de {uploaded_file.name}", abas, key=uploaded_file.name)

        df = xls.parse(aba_selecionada)

        if all(col in df.columns for col in ["Data", "Valor", "Tipo"]):
            df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
            df = df.dropna(subset=["Data"])
            df = df.sort_values("Data")
            df["AnoMes"] = df["Data"].dt.to_period("M")

            # Classifica saldo por histórico se necessário
            if "Histórico" in df.columns:
                df["É Saldo?"] = df["Histórico"].apply(contem_palavra_saldo)
            else:
                df["É Saldo?"] = False

            # Saldo anterior para linha marcada como saldo
            df["Saldo Anterior"] = df.apply(lambda row: row["Valor"] if row["Tipo"] == "Saldo" or row["É Saldo?"] else None, axis=1)
            df["Saldo Anterior"] = pd.to_numeric(df["Saldo Anterior"], errors="coerce")

            # Filtro de tipo
            if tipo_filtro != "Todos":
                df = df[df["Tipo"] == tipo_filtro[:-1]]

            st.success(f"✅ {len(df)} transações carregadas.")
            st.dataframe(df, use_container_width=True)

            st.markdown("---")
            st.header("📊 Dashboard Financeiro")

            # 📈 Saldo Final Mensal
            st.subheader("📈 Saldo Final de Cada Mês")
            df_saldo_mensal = df[df["Saldo Anterior"].notnull()]
            fig1 = px.line(df_saldo_mensal, x="Data", y="Saldo Anterior", markers=True, title="Saldo Final Mensal")
            fig1.update_layout(xaxis_title="Data", yaxis_title="Saldo (R$)", template="plotly_dark", height=400)
            st.plotly_chart(fig1, use_container_width=True)

            # 📈 Saldo Acumulado
            st.subheader("📈 Evolução do Saldo Acumulado")
            df_sorted = df.sort_values("Data").copy()
            df_sorted["Saldo Acumulado"] = df_sorted["Valor"].cumsum() + saldo_inicial
            fig2 = px.line(df_sorted, x="Data", y="Saldo Acumulado", title="Evolução do Saldo Acumulado")
            fig2.update_layout(xaxis_title="Data", yaxis_title="Saldo Acumulado (R$)", template="plotly_dark", height=400)
            st.plotly_chart(fig2, use_container_width=True)

            # 📅 Tabela de saldos mensais
            st.subheader("📅 Tabela de Saldos Mensais")
            resumo_saldos = df_saldo_mensal[["AnoMes", "Saldo Anterior"]].copy()
            resumo_saldos["AnoMes"] = resumo_saldos["AnoMes"].astype(str)
            st.dataframe(resumo_saldos.rename(columns={"AnoMes": "Mês", "Saldo Anterior": "Saldo Final"}), use_container_width=True)

            # 📉 Entradas vs Saídas
            st.subheader("📉 Entradas vs Saídas Mensais")
            df_mov = df[df["Tipo"].isin(["Entrada", "Saída"])]
            if "Histórico" in df_mov.columns:
                df_mov = df_mov[~df_mov["Histórico"].apply(contem_palavra_saldo)]
            df_mov["AnoMes"] = df_mov["Data"].dt.strftime('%m/%Y')
            resumo = df_mov.groupby(["AnoMes", "Tipo"])["Valor"].sum().reset_index()
            fig3 = px.bar(resumo, x="AnoMes", y="Valor", color="Tipo", barmode="group", title="Entradas vs Saídas")
            fig3.update_layout(xaxis_title="Mês/Ano", yaxis_title="Valor (R$)", template="plotly_dark", height=400)
            st.plotly_chart(fig3, use_container_width=True)

            # 🥧 Donut de Despesas
            if "Histórico" in df.columns:
                st.subheader("🥧 Categorias das Despesas")
                categorias = df[df["Tipo"] == "Saída"].groupby("Histórico")["Valor"].sum().reset_index()
                categorias["Valor"] = -categorias["Valor"]
                total = categorias["Valor"].sum()
                categorias = categorias[categorias["Valor"] / total >= 0.01]
                fig4 = px.pie(categorias, names="Histórico", values="Valor", hole=0.6, title="Distribuição das Despesas")
                fig4.update_traces(textinfo='percent+label', textposition='inside', pull=[0.05]*len(categorias))
                fig4.update_layout(template="plotly_dark", height=400)
                st.plotly_chart(fig4, use_container_width=True)

            # 📥 Exportar Excel
            buffer = BytesIO()
            df.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                label="📥 Baixar Excel com Dados",
                data=buffer,
                file_name=f"dashboard_{uploaded_file.name.replace('.xlsx','')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("❌ A aba selecionada precisa conter as colunas: Data, Valor, Tipo.")
else:
    st.info("📎 Faça o upload de planilhas Excel com colunas padrão: Data, Tipo, Valor (e opcionalmente Histórico, Saldo Anterior).")

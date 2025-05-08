import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Dashboard Financeiro", layout="wide")
st.title("📄 Dashboard Financeiro - Análise de Transações")

# Upload de planilha
uploaded_file = st.file_uploader("📎 Selecione a planilha de extratos (Excel)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if "Data" in df.columns and "Valor" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors='coerce')
        df = df.dropna(subset=["Data"])
        df = df.sort_values("Data")

        # Tipo de transação
        df["Tipo"] = df["Valor"].apply(lambda x: "Entrada" if x > 0 else "Saída")

        # Saldo acumulado
        df["Saldo Acumulado"] = df["Valor"].cumsum()

        st.success(f"✅ **{len(df)}** transações carregadas.")
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        st.header("📊 Dashboard Financeiro")

        # 📈 Saldo acumulado
        st.subheader("Saldo Acumulado")
        fig1 = px.area(df, x="Data", y="Saldo Acumulado", markers=True, title="Saldo Acumulado ao Longo do Tempo")
        fig1.update_layout(xaxis_title="Data", yaxis_title="Saldo (R$)", template="plotly_dark", height=400)
        st.plotly_chart(fig1, use_container_width=True)

        # 📉 Entradas e saídas por mês
        st.subheader("Entradas e Saídas Mensais")
        df["AnoMes"] = df["Data"].dt.to_period("M")
        resumo = df.groupby(["AnoMes", "Tipo"])["Valor"].sum().reset_index()
        resumo["AnoMes"] = resumo["AnoMes"].astype(str)
        fig2 = px.bar(resumo, x="AnoMes", y="Valor", color="Tipo", barmode="group",
                      title="Entradas vs Saídas Mensais")
        fig2.update_layout(xaxis_title="Mês/Ano", yaxis_title="Valor (R$)", template="plotly_dark", height=400)
        st.plotly_chart(fig2, use_container_width=True)

        # 🥧 Donut de despesas (se coluna existir)
        if "Histórico" in df.columns:
            st.subheader("Categorias das Despesas")
            categorias = df[df["Tipo"] == "Saída"].groupby("Histórico")["Valor"].sum().reset_index()
            categorias["Valor"] = -categorias["Valor"]
            categorias = categorias[categorias["Valor"] > 0]
            total = categorias["Valor"].sum()
            categorias = categorias[categorias["Valor"] / total >= 0.01]

            if not categorias.empty:
                fig3 = px.pie(categorias, names="Histórico", values="Valor", hole=0.6,
                              title="Distribuição das Despesas")
                fig3.update_traces(textinfo='percent', textposition='inside', pull=[0.05]*len(categorias))
                fig3.update_layout(template="plotly_dark", showlegend=True, height=400)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("ℹ️ Nenhuma despesa acima de 1% encontrada.")
        else:
            st.warning("⚠️ A coluna 'Histórico' não está presente para gerar o gráfico de despesas.")

        # 📥 Exportar para Excel
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="📥 Baixar Excel com Dados",
            data=buffer,
            file_name="extrato_detalhado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ A planilha precisa conter as colunas 'Data' e 'Valor'.")
else:
    st.info("📎 Faça o upload de uma planilha para gerar os gráficos.")

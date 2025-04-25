import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import locale
from io import BytesIO

# Ajuste de locale para português (Brasil) de maneira mais segura
try:
    # Tentar usar um local mais genérico
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    st.warning("⚠️ Não foi possível configurar o local para português. A formatação de datas pode não estar no formato brasileiro.")

# Configurações da página
st.set_page_config(page_title="Dashboard Financeiro", layout="wide")
st.title("📄 Dashboard Financeiro - Análise de Transações")

# Upload de planilha
uploaded_file = st.file_uploader("📎 Selecione a planilha de extratos (Excel)", type=["xlsx"])

if uploaded_file:
    # Leitura da planilha
    df = pd.read_excel(uploaded_file)
    
    # Garantir que os dados necessários estão presentes
    if "Data" in df.columns and "Valor" in df.columns:
        # Convertendo a coluna 'Data' para o formato datetime
        df["Data"] = pd.to_datetime(df["Data"], errors='coerce')
        df = df.sort_values("Data")
        
        # Classificando as transações em 'Entrada' e 'Saída'
        df["Tipo"] = df["Valor"].apply(lambda x: "Entrada" if x > 0 else "Saída")
        
        # Calculando o saldo acumulado
        df["Saldo Acumulado"] = df["Valor"].cumsum()

        # Exibindo o dataframe
        st.success(f"✅ **{len(df)}** transações carregadas.")
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

        # Exportação dos dados
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
    st.info("Por favor, faça o upload de uma planilha para gerar os gráficos.")

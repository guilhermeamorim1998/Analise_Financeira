import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 Dashboard de Extratos Bancários - Sicoob e Caixa")

# 🔍 Função auxiliar para localizar a coluna de histórico
def encontrar_coluna_similar(df, nomes_possiveis):
    for nome in nomes_possiveis:
        for coluna in df.columns:
            if nome.lower() in coluna.lower():
                return coluna
    return None

# 📂 Upload de arquivos Excel
uploaded_files = st.file_uploader("📎 Selecione os arquivos Excel", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.header(f"📁 Arquivo: {uploaded_file.name}")
        
        xls = pd.ExcelFile(uploaded_file)
        abas = xls.sheet_names
        aba_selecionada = st.selectbox(f"Selecione a aba do arquivo {uploaded_file.name}", abas, key=uploaded_file.name)

        df = xls.parse(aba_selecionada)

        # Confere se tem as colunas mínimas obrigatórias
        if "Data" in df.columns and "Tipo" in df.columns and "Valor" in df.columns:
            df["Data"] = pd.to_datetime(df["Data"], errors='coerce')
            df["AnoMes"] = df["Data"].dt.strftime('%Y-%m')
            df = df.dropna(subset=["Data"])
            df = df.sort_values("Data")

            st.success(f"✅ {len(df)} transações carregadas.")
            st.dataframe(df, use_container_width=True)

            # 📈 Gráfico de Saldo Final por Mês
            st.subheader("📈 Saldo Final de Cada Mês")
            df_saldo = df[df["Tipo"] == "Saldo"]
            if not df_saldo.empty and "Saldo Anterior" in df.columns:
                fig1 = px.line(df_saldo, x="Data", y="Saldo Anterior", markers=True, title="Saldo Final Mensal")
                fig1.update_layout(xaxis_title="Data", yaxis_title="Saldo (R$)", template="plotly_dark", height=500)
                st.plotly_chart(fig1, use_container_width=True)

                st.subheader("📅 Tabela de Saldos Mensais")
                resumo_saldos = df_saldo[["AnoMes", "Saldo Anterior"]].copy()
                resumo_saldos = resumo_saldos.rename(columns={"AnoMes": "Mês", "Saldo Anterior": "Saldo Final"})
                st.dataframe(resumo_saldos, use_container_width=True)
            else:
                st.info("ℹ️ Nenhum saldo mensal encontrado ou a coluna 'Saldo Anterior' está ausente.")

            # 📉 Entradas vs Saídas
            st.subheader("📉 Entradas e Saídas Mensais")

            palavras_excluir = [
                "saldo", "saldo anterior", "saldo atual",
                "saldo final", "saldo inicial", "saldo aplicado"
            ]

            def historico_tem_saldo(texto):
                texto = str(texto).lower()
                return any(p in texto for p in palavras_excluir)

            col_hist = encontrar_coluna_similar(df, ["histórico", "descricao", "descrição", "hist"])
            if col_hist:
                df_mov = df[df["Tipo"].isin(["Entrada", "Saída"])].copy()
                df_mov = df_mov[~df_mov[col_hist].apply(historico_tem_saldo)]

                df_mov["AnoMes"] = df_mov["Data"].dt.strftime('%m/%Y')
                resumo = df_mov.groupby(["AnoMes", "Tipo"])["Valor"].sum().reset_index()

                fig2 = px.bar(resumo, x="AnoMes", y="Valor", color="Tipo", barmode="group", title="Entradas vs Saídas Mensais")
                fig2.update_layout(xaxis_title="Mês/Ano", yaxis_title="Valor (R$)", template="plotly_dark", height=500)
                st.plotly_chart(fig2, use_container_width=True)

                # 🥧 Gráfico Donut de Despesas
                st.subheader("🥧 Categorias das Despesas")
                categorias = df[df["Tipo"] == "Saída"].groupby(col_hist)["Valor"].sum().reset_index()
                categorias["Valor"] = -categorias["Valor"]
                categorias = categorias[categorias["Valor"] > 0]
                total = categorias["Valor"].sum()
                categorias = categorias[categorias["Valor"] / total >= 0.01]

                fig3 = px.pie(categorias, names=col_hist, values="Valor", hole=0.6, title="Distribuição das Despesas")
                fig3.update_traces(textinfo='percent+label', textposition='inside', pull=[0.05]*len(categorias))
                fig3.update_layout(template="plotly_dark", showlegend=True, height=500)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.warning("⚠️ Nenhuma coluna com nome semelhante a 'Histórico' foi encontrada.")
        else:
            st.warning("⚠️ A aba selecionada não possui as colunas esperadas: 'Data', 'Tipo', 'Valor'.")
else:
    st.info("📎 Faça upload de planilhas com extratos contendo as colunas: Data, Tipo, Valor e Histórico.")

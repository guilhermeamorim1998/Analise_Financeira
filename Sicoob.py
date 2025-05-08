import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re
from io import BytesIO
import plotly.express as px
import locale

# Ajustar locale para português (Brasil)
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')

# Configuração da página
st.set_page_config(page_title="Extrator de Extratos Bancários", page_icon="📄", layout="wide")
st.title("📄 Extrator de Extratos Bancários - Versão Ultra-Robusta 🚀")
st.markdown("---")

# 📎 Upload de arquivos e inputs via sidebar
with st.sidebar:
    uploaded_files = st.file_uploader("📎 Selecione os arquivos PDF dos extratos", type=["pdf"], accept_multiple_files=True)
    ano_padrao = st.number_input("📅 Informe o ano dos extratos (caso datas venham sem ano):", min_value=2000, max_value=2100, value=2024, step=1)
    saldo_inicial = st.number_input("💰 Informe o saldo inicial (opcional):", value=0.0, step=100.0)
    tipo_filtro = st.selectbox("🔎 Filtrar por tipo:", ["Todos", "Entradas", "Saídas"])

# Função robusta para extrair transações
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

            historico = ""
            descricao = []
            valor = None
            tipo = None

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
                        if tipo == 'D':
                            valor = -valor
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

# Função para detectar se histórico indica saldo
def contem_palavra_saldo(texto):
    if isinstance(texto, str):
        texto = texto.lower()
        return any(palavra in texto for palavra in ["saldo", "saldo anterior", "saldo atual", "saldo final", "saldo inicial"])
    return False

# Processamento dos arquivos
if uploaded_files:
    todas_transacoes = []

    for arquivo in uploaded_files:
        st.info(f"🔍 Processando: **{arquivo.name}**")
        try:
            with fitz.open(stream=arquivo.read(), filetype="pdf") as doc:
                texto_completo = "".join(pagina.get_text("text") for pagina in doc)

            transacoes = extrair_transacoes(texto_completo, ano_padrao=ano_padrao)

            if transacoes:
                for linha in transacoes:
                    linha.append(arquivo.name)
                    todas_transacoes.append(linha)
            else:
                st.warning(f"⚠️ Nenhuma transação reconhecida em **{arquivo.name}**.")
        except Exception as e:
            st.error(f"❌ Erro ao processar {arquivo.name}: {e}")

    if todas_transacoes:
        # Criação do DataFrame
        df = pd.DataFrame(todas_transacoes, columns=["Data", "Histórico", "Valor", "Descrição", "Arquivo"])
        df["Índice"] = df.index
        df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors='coerce')
        df = df.dropna(subset=["Data"])
        df = df.sort_values(["Data", "Índice"]).drop(columns=["Índice"])

        df["AnoMes"] = df["Data"].dt.to_period("M")

        def encontrar_saldo_final(grupo):
            saldo_entries = grupo[grupo["Histórico"].apply(contem_palavra_saldo)]
            if not saldo_entries.empty:
                return saldo_entries["Data"].idxmax()
            else:
                return grupo["Data"].idxmax()

        ultimos_indices = df.groupby("AnoMes").apply(encontrar_saldo_final).dropna().values

        df["Tipo"] = df.index.map(lambda idx: "Saldo" if idx in ultimos_indices else ("Entrada" if df.at[idx, "Valor"] > 0 else "Saída"))
        df["Saldo Anterior"] = None
        df.loc[df["Tipo"] == "Saldo", "Saldo Anterior"] = df["Valor"]
        df["Saldo Anterior"] = pd.to_numeric(df["Saldo Anterior"], errors="coerce")

        # Filtro por tipo
        if tipo_filtro != "Todos":
            df = df[df["Tipo"] == tipo_filtro[:-1]]

        st.success(f"✅ **{len(df)}** transações extraídas com sucesso.")
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        st.header("📊 Dashboard Financeiro")

        # 📈 Saldo Final de Cada Mês
        st.subheader("📈 Saldo Final de Cada Mês")
        df_saldo_mensal = df[df["Tipo"] == "Saldo"]
        fig1 = px.line(df_saldo_mensal, x="Data", y="Saldo Anterior", markers=True, title="Saldo Final Mensal")
        fig1.update_layout(xaxis_title="Data", yaxis_title="Saldo (R$)", template="plotly_dark", height=500)
        st.plotly_chart(fig1, use_container_width=True)

        # ✅ Novo: Gráfico de Saldo Acumulado
        st.subheader("📈 Evolução do Saldo Acumulado")
        df_sorted = df.sort_values("Data").copy()
        df_sorted["Saldo Acumulado"] = df_sorted["Valor"].cumsum() + saldo_inicial

        fig_saldo_acumulado = px.line(df_sorted, x="Data", y="Saldo Acumulado", title="Evolução do Saldo Acumulado")
        fig_saldo_acumulado.update_layout(xaxis_title="Data", yaxis_title="Saldo Acumulado (R$)", template="plotly_dark", height=500)
        st.plotly_chart(fig_saldo_acumulado, use_container_width=True)

        # 📅 Tabela resumo de saldo por mês
        st.subheader("📅 Tabela de Saldos Mensais")
        resumo_saldos = df_saldo_mensal[["AnoMes", "Saldo Anterior"]].copy()
        resumo_saldos["AnoMes"] = resumo_saldos["AnoMes"].astype(str)
        st.dataframe(resumo_saldos.rename(columns={"AnoMes": "Mês", "Saldo Anterior": "Saldo Final"}), use_container_width=True)

        # 📉 Entradas vs Saídas Mensais
        st.subheader("📉 Entradas e Saídas Mensais")
        palavras_excluir = ["saldo", "saldo anterior", "saldo atual", "saldo final", "saldo inicial"]

        def historico_tem_saldo(texto):
            texto = str(texto).lower()
            return any(p in texto for p in palavras_excluir)

        df_mov = df[df["Tipo"].isin(["Entrada", "Saída"])].copy()
        df_mov = df_mov[~df_mov["Histórico"].apply(historico_tem_saldo)]
        df_mov["AnoMes"] = df_mov["Data"].dt.strftime('%m/%Y')
        resumo = df_mov.groupby(["AnoMes", "Tipo"])["Valor"].sum().reset_index()

        fig2 = px.bar(resumo, x="AnoMes", y="Valor", color="Tipo", barmode="group", title="Entradas vs Saídas Mensais")
        fig2.update_layout(xaxis_title="Mês/Ano", yaxis_title="Valor (R$)", template="plotly_dark", height=500)
        st.plotly_chart(fig2, use_container_width=True)

        # 🥧 Gráfico Donut de Despesas
        st.subheader("🥧 Categorias das Despesas")
        categorias = df[df["Tipo"] == "Saída"].groupby("Histórico")["Valor"].sum().reset_index()
        categorias["Valor"] = -categorias["Valor"]
        categorias = categorias[categorias["Valor"] > 0]
        total = categorias["Valor"].sum()
        categorias = categorias[categorias["Valor"] / total >= 0.01]

        fig3 = px.pie(categorias, names="Histórico", values="Valor", hole=0.6, title="Distribuição das Despesas")
        fig3.update_traces(textinfo='percent+label', textposition='inside', pull=[0.05]*len(categorias))
        fig3.update_layout(template="plotly_dark", showlegend=True, height=500)
        st.plotly_chart(fig3, use_container_width=True)

        # 📥 Exportação para Excel
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="📥 Baixar Excel com Dados",
            data=buffer,
            file_name="extrato_bancario_detalhado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("⚠️ Nenhuma transação reconhecida em nenhum dos PDFs.")
else:
    st.info("📎 Faça o upload dos extratos bancários em PDF para iniciar a extração.")

import streamlit as st
from pymongo import MongoClient
import plotly.express as px
import pandas as pd
from datetime import datetime

# Conexão com MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["etiquetas_db"]
colecao = db["status_etiquetas"]

# Função para obter o histórico de preços com nome dos produtos
def obter_historico_precos():
    dados_historicos = []
    for doc in colecao.find({"nome": {"$in": ["ETIQUETA-1", "ETIQUETA-2", "ETIQUETA-3"]}}):
        nome_produto = doc.get("produto", doc["nome"])
        historico_precos = doc.get("historico_precos", [])
        for item in historico_precos:
            dados_historicos.append({
                "produto": nome_produto,
                "data": datetime.strptime(item["data"], "%Y-%m-%d"),
                "preco": float(item["preco"])
            })
    return dados_historicos

# Função para plotar gráfico de preços históricos
def plotar_precos_historicos(dados_historicos):
    df = pd.DataFrame(dados_historicos)
    fig = px.line(df, x="data", y="preco", color="produto",
                  labels={"preco": "Preço (R$)", "data": "Data", "produto": "Produto"},
                  title="Histórico de Preços dos Produtos")

    fig.update_xaxes(tickformat="%d/%m/%Y", tickangle=45)
    fig.update_traces(mode="lines+markers")
    st.plotly_chart(fig)

# Interface Streamlit
st.set_page_config(page_title="Histórico de Preços dos Produtos", layout="wide")
st.title("📊 Histórico de Preços dos Produtos Monitorados")

# Obter os dados históricos dos produtos
dados_historicos = obter_historico_precos()

# Plotar gráfico
plotar_precos_historicos(dados_historicos)

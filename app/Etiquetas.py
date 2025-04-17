import streamlit as st
import asyncio
from bleak import BleakScanner, BleakClient
from pymongo import MongoClient
from datetime import datetime, timedelta
import random

CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
ETIQUETAS_ESPERADAS = ["ETIQUETA-1", "ETIQUETA-2", "ETIQUETA-3"]

st.set_page_config(page_title="Etiquetas BLE", layout="wide")
st.title("📲 Dashboard de Etiquetas Digitais")
st.caption("Status em tempo real e atualização de preços via BLE")

# ============ MONGO ============
client = MongoClient("mongodb://localhost:27017/")
db = client["etiquetas_db"]
colecao = db["status_etiquetas"]

# Criação inicial do banco com histórico realista
if colecao.count_documents({}) == 0:
    hoje = datetime.now()
    produtos = [
        {"nome": "ETIQUETA-1", "produto": "Arroz 5kg", "faixa_preco": (24.98, 29.76)},
        {"nome": "ETIQUETA-2", "produto": "Feijão 1kg", "faixa_preco": (2.99, 7.73)},
        {"nome": "ETIQUETA-3", "produto": "Óleo de soja 900ml", "faixa_preco": (4.19, 7.99)}
    ]
    for produto in produtos:
        historico_precos = []
        for i in range(90):  # 90 dias
            data = hoje - timedelta(days=90 - i)
            preco = round(random.uniform(*produto["faixa_preco"]), 2)
            historico_precos.append({"preco": str(preco), "data": data.strftime("%Y-%m-%d")})
        colecao.insert_one({
            "nome": produto["nome"],
            "produto": produto["produto"],
            "historico_precos": historico_precos,
            "ultima_conexao": "Nunca"
        })

# ============ SESSION ============
if "dados_etiquetas" not in st.session_state:
    st.session_state.dados_etiquetas = {}
    for doc in colecao.find({"nome": {"$in": ETIQUETAS_ESPERADAS}}):
        historico = doc.get("historico_precos", [])
        ultimo_preco = historico[-1]["preco"] if historico else "0.00"
        st.session_state.dados_etiquetas[doc["nome"]] = {
            "produto": doc.get("produto", ""),
            "preco": ultimo_preco,
            "ultima_conexao": doc.get("ultima_conexao", "Nunca")
        }

# ============ SCAN ============
@st.cache_data(ttl=30, show_spinner="🔍 Procurando etiquetas BLE...")
def escanear_etiquetas():
    dispositivos = asyncio.run(BleakScanner.discover(timeout=5))
    return {d.name: d.address for d in dispositivos if d.name in ETIQUETAS_ESPERADAS}

etiquetas_online = escanear_etiquetas()

# ============ FORMATAÇÃO ============
def formatar_preco(preco):
    try:
        valor = float(preco)
        return f"R$ {valor:.2f}".replace('.', ',')
    except:
        return "R$ 0,00"

# ============ INTERFACE ============
cols = st.columns(3)

for i, etiqueta in enumerate(ETIQUETAS_ESPERADAS):
    with cols[i % 3]:
        @st.fragment
        def exibir_etiqueta(etiqueta=etiqueta):
            online = etiqueta in etiquetas_online
            endereco = etiquetas_online.get(etiqueta, None)
            preco_key = f"preco-{etiqueta}"
            clear_key = f"clear-{etiqueta}"

            if preco_key not in st.session_state:
                st.session_state[preco_key] = ""
            if clear_key in st.session_state and st.session_state[clear_key]:
                st.session_state[preco_key] = ""
                st.session_state[clear_key] = False

            dados = st.session_state.dados_etiquetas[etiqueta]
            produto = dados["produto"]
            preco_atual = dados["preco"]
            ultima_conexao = dados["ultima_conexao"]

            st.markdown(f"### 🏷️ {etiqueta}")
            st.write(f"**📦 Produto:** {produto}")
            st.metric("Status", "🟢 Online" if online else "🔴 Offline")
            st.metric("Preço Atual", formatar_preco(preco_atual))
            st.write(f"Última conexão: **{ultima_conexao}**")

            novo_preco = st.text_input(f"Novo preço para {etiqueta}", key=preco_key)

            if online and st.button(f"📤 Enviar para {etiqueta}", key=f"btn-{etiqueta}"):
                async def enviar_preco():
                    try:
                        async with BleakClient(endereco) as client:
                            mensagem = f"{produto}xxxR${float(novo_preco):.2f}"
                            await client.write_gatt_char(CHAR_UUID, mensagem.encode())

                            agora = datetime.now()
                            data_str = agora.strftime("%Y-%m-%d")
                            hora_str = agora.strftime("%H:%M:%S")

                            colecao.update_one(
                                {"nome": etiqueta},
                                {"$pull": {"historico_precos": {"data": data_str}}}
                            )
                            colecao.update_one(
                                {"nome": etiqueta},
                                {
                                    "$push": {"historico_precos": {"preco": novo_preco, "data": data_str}},
                                    "$set": {"ultima_conexao": hora_str}
                                }
                            )

                            st.session_state.dados_etiquetas[etiqueta]["preco"] = novo_preco
                            st.session_state.dados_etiquetas[etiqueta]["ultima_conexao"] = hora_str
                            st.session_state[clear_key] = True

                            st.success(f"✅ Enviado às {hora_str}")
                            st.rerun(scope="fragment")

                    except Exception as e:
                        st.error(f"❌ Erro: {e}")

                asyncio.run(enviar_preco())

        exibir_etiqueta()

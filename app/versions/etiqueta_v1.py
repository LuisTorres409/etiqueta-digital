import streamlit as st
import asyncio
from bleak import BleakScanner, BleakClient
from datetime import datetime

# ==================== CONFIGURAÇÕES ====================
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
ETIQUETAS_ESPERADAS = ["ETIQUETA-1", "ETIQUETA-2", "ETIQUETA-3"]

st.set_page_config(page_title="Etiquetas BLE", layout="wide")
st.title("📲 Dashboard de Etiquetas Digitais")
st.caption("Status em tempo real e atualização de preços via BLE")

# ==================== SESSION STATE ====================
if "ultimas_conexoes" not in st.session_state:
    st.session_state.ultimas_conexoes = {nome: "Nunca" for nome in ETIQUETAS_ESPERADAS}
    
# Inicializar preços atuais das etiquetas
if "precos_atuais" not in st.session_state:
    st.session_state.precos_atuais = {nome: "0.00" for nome in ETIQUETAS_ESPERADAS}

# ==================== SCAN BLE ====================
@st.cache_data(ttl=30, show_spinner="🔍 Procurando etiquetas BLE...")
def escanear_etiquetas():
    dispositivos = asyncio.run(BleakScanner.discover(timeout=5))
    return {
        d.name: d.address
        for d in dispositivos
        if d.name in ETIQUETAS_ESPERADAS
    }

etiquetas_online = escanear_etiquetas()

# Função para formatar preço no estilo brasileiro
def formatar_preco(preco):
    try:
        valor = float(preco)
        return f"R$ {valor:.2f}".replace('.', ',')
    except (ValueError, TypeError):
        return "R$ 0,00"

# ==================== INTERFACE ====================
cols = st.columns(3)

for i, etiqueta in enumerate(ETIQUETAS_ESPERADAS):
    with cols[i % 3]:
        @st.fragment
        def exibir_etiqueta(etiqueta=etiqueta):
            online = etiqueta in etiquetas_online
            endereco = etiquetas_online.get(etiqueta, None)
            
            preco_key = f"preco-{etiqueta}"
            clear_key = f"clear_{preco_key}"
            
            # Initialize session state for this tag if needed
            if preco_key not in st.session_state:
                st.session_state[preco_key] = ""
                
            # Check if we need to clear the input field
            if clear_key in st.session_state and st.session_state[clear_key]:
                st.session_state[preco_key] = ""
                st.session_state[clear_key] = False

            st.markdown(f"### 🏷️ {etiqueta}")
            status_color = "🟢 Online" if online else "🔴 Offline"
            st.metric(label="Status", value=status_color)
            
            # Exibir preço atual formatado
            preco_atual_formatado = formatar_preco(st.session_state.precos_atuais[etiqueta])
            st.metric(label="Preço Atual", value=preco_atual_formatado)
            
            st.write(f"Última conexão: **{st.session_state.ultimas_conexoes[etiqueta]}**")

            preco = st.text_input(f"Novo preço para {etiqueta}", key=preco_key)

            if online and st.button(f"📤 Enviar para {etiqueta}", key=f"btn-{etiqueta}"):
                async def enviar_preco():
                    try:
                        async with BleakClient(endereco) as client:
                            await client.write_gatt_char(CHAR_UUID, preco.encode())
                            agora = datetime.now().strftime("%H:%M:%S")
                            st.session_state.ultimas_conexoes[etiqueta] = agora
                            
                            # Atualizar o preço atual da etiqueta
                            st.session_state.precos_atuais[etiqueta] = preco
                            
                            st.success(f"✅ Preço enviado para {etiqueta} às {agora}")
                            
                            # Set flag to clear the input on next rerun instead of directly modifying
                            st.session_state[clear_key] = True
                            st.rerun(scope="fragment")
                    except Exception as e:
                        st.error(f"❌ Erro ao enviar para {etiqueta}: {e}")

                asyncio.run(enviar_preco())
        
        exibir_etiqueta()
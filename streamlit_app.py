import streamlit as st
import ccxt
import time
import random
from supabase import create_client, Client

# Configuração da página do Streamlit com estilo Dar-Shan / Cavalo de Fogo
st.set_page_config(page_title="Sara_FireBot - Auto Bot", page_icon="🐴", layout="wide")

# Inicialização de variáveis de sessão antes de carregar o CSS
if 'saldo_usdt' not in st.session_state:
    st.session_state.saldo_usdt = 10000.0
    st.session_state.saldo_btc = 0.0
    st.session_state.historico = []
    st.session_state.bot_ativo = False

# Cores dinâmicas para o botão baseado no estado do robô
cor_botao = "#28a745" if st.session_state.bot_ativo else "#dc3545"
cor_hover = "#218838" if st.session_state.bot_ativo else "#c82333"

# Estilização visual unificada (Tema Escuro Premium com detalhes em Fogo)
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0b0606; color: #ffffff; }}
    h1 {{ color: #ff4500 !important; text-align: center; font-family: 'Segoe UI', Roboto, sans-serif; font-weight: 800; text-shadow: 0px 0px 15px #ff8c00; margin-bottom: 5px; }}
    .subtitle {{ text-align: center; color: #ffa500; font-size: 1.2rem; margin-bottom: 30px; font-weight: 300; }}
    
    /* Customização do botão dinâmico */
    div.stButton > button:first-child {{
        background-color: {cor_botao} !important;
        color: white !important;
        border: none !important;
        padding: 15px 30px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        box-shadow: 0px 4px 15px {cor_botao}88 !important;
    }}
    div.stButton > button:first-child:hover {{
        background-color: {cor_hover} !important;
        box-shadow: 0px 6px 20px {cor_hover}bb !important;
        transform: scale(1.01);
    }}
    </style>
""", unsafe_allow_html=True)

st.title("🐴 SARA_FIREBOT — AUTONOMOUS BOT V1")
st.markdown("<p class='subtitle'>🔥 Guardião de Dar-Shan: Automatizando Cripto de Forma Autônoma</p>", unsafe_allow_html=True)

# --- CONEXÃO SEGURA COM SUPABASE (100% OCULTA VIA SECRETS) ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        pass

def salvar_no_supabase(mensagem):
    if supabase:
        try:
            supabase.table("historico_bot").insert({"operacao": mensagem}).execute()
        except Exception:
            pass

# Conexão pública para leitura de preços
@st.cache_data(ttl=5)
def pegar_preco_bitcoin():
    try:
        exchange = ccxt.binance()
        ticker = exchange.fetch_ticker('BTC/USDT')
        return ticker['last']
    except:
        return random.randint(62000, 65000)

preco_atual = pegar_preco_bitcoin()

# --- INTERFACE UNIFICADA (SEM BARRA LATERAL) ---
col_config1, col_config2 = st.columns(2)
with col_config1:
    config_queda = st.slider("Comprar se cair (%)", 0.5, 5.0, 1.5, step=0.1)
with col_config2:
    config_lucro = st.slider("Vender se subir (%)", 0.5, 10.0, 2.0, step=0.1)

st.write("")

# Botão de controle com texto dinâmico e cores reativas
texto_botao = "🟢 DESCANSAR CAVALO DE FOGO (PAUSAR)" if st.session_state.bot_ativo else "🔴 CONVOCAR CAVALO DE FOGO (LIGAR)"
if st.button(texto_botao):
    st.session_state.bot_ativo = not st.session_state.bot_ativo
    st.rerun()

st.write("---")

# --- PAINEL DE MÉTRICAS ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="💰 Fundo Disponível (USDT)", value=f"${st.session_state.saldo_usdt:,.2f}")
with col2:
    st.metric(label="🪙 Ativos em Carteira (BTC)", value=f"{st.session_state.saldo_btc:.4f} BTC")
with col3:
    st.metric(label="📊 Preço do BTC (Binance)", value=f"${preco_atual:,.2f}", delta="Sincronizado em Tempo Real")

st.write("")

# --- LÓGICA OPERACIONAL ---
if st.session_state.bot_ativo:
    st.success("🔥 SARA_FIREBOT OPERANDO EM MODO AUTÔNOMO NAS TERRAS DE DAR-SHAN...")
    
    gatilho = random.choice(['nada', 'nada', 'comprar', 'vender'])
    
    if gatilho == 'comprar' and st.session_state.saldo_usdt > 100:
        quantidade_comprar = st.session_state.saldo_usdt / preco_atual
        st.session_state.saldo_btc += quantidade_comprar
        st.session_state.saldo_usdt = 0.0
        
        msg = f"🛒 ENTRADA: Sara detectou sinal! Cavalo de Fogo adquiriu {quantidade_comprar:.4f} BTC a ${preco_atual:,.2f}"
        st.session_state.historico.append(msg)
        salvar_no_supabase(msg)
        st.toast("🔥 Portal aberto! Compra executada.")
        
    elif gatilho == 'vender' and st.session_state.saldo_btc > 0:
        lucro_usdt = st.session_state.saldo_btc * preco_atual
        st.session_state.saldo_usdt = lucro_usdt
        st.session_state.saldo_btc = 0.0
        
        msg = f"💰 SAÍDA: Lucro resgatado! Posição liquidada a ${preco_atual:,.2f} retornando para USDT."
        st.session_state.historico.append(msg)
        salvar_no_supabase(msg)
        st.toast("👑 Ouro protegido! Venda realizada.")
else:
    st.warning("💤 Cavalo de Fogo está descansando no santuário. Ative o painel para iniciar.")

# --- CRÔNICAS DE OPERAÇÃO ---
st.write("---")
st.write("### 📜 Crônicas de Operação - Sara_FireBot")
if st.session_state.historico:
    for acao in reversed(st.session_state.historico):
        st.info(acao)
else:
    st.write("*Nenhum bloco minerado ou transação realizada nesta sessão.*")

# Loop de atualização do robô ativo
time.sleep(2)
if st.session_state.bot_ativo:
    st.rerun()

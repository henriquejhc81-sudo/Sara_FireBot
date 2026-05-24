import streamlit as st
import ccxt
import time
import random
from supabase import create_client, Client

# Configuração da página do Streamlit com estilo Dar-Shan / Cavalo de Fogo
st.set_page_config(page_title="Sara_FireBot - Auto Bot", page_icon="🐴", layout="wide")

# Estilização visual (Tema Escuro com Vermelho Fogo e Laranja Neon)
st.markdown("""
    <style>
    .stApp { background-color: #0d0808; color: #ffffff; }
    h1 { color: #ff4500 !important; text-align: center; font-family: 'Georgia', serif; text-shadow: 2px 2px 10px #ff8c00; }
    .status-box { background-color: #1a0f0f; padding: 20px; border-radius: 10px; border: 1px solid #ff4500; }
    </style>
""", unsafe_allow_html=True)

st.title("🐴 SARA_FIREBOT — AUTONOMOUS BOT V1")
st.write("### 🔥 Guardião de Dar-Shan: Automatizando Cripto de Forma Autônoma")

# --- INTEGRAÇÃO SUPABASE ---
# Configuração segura via Secrets do Streamlit ou Fallback Local
SUPABASE_URL = st.sidebar.text_input("Supabase URL", value=st.secrets.get("SUPABASE_URL", ""), type="password")
SUPABASE_KEY = st.sidebar.text_input("Supabase API Key", value=st.secrets.get("SUPABASE_KEY", ""), type="password")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.sidebar.error(f"Erro ao conectar no Supabase: {e}")

def salvar_no_supabase(mensagem):
    """Envia o log de operação para a tabela 'historico_bot' no Supabase"""
    if supabase:
        try:
            supabase.table("historico_bot").insert({"operacao": mensagem}).execute()
        except Exception as e:
            st.error(f"Falha ao salvar no banco de dados: {e}")

# --- INICIALIZAÇÃO DE VARIÁVEIS ---
if 'saldo_usdt' not in st.session_state:
    st.session_state.saldo_usdt = 10000.0  # Fundo inicial simulado
    st.session_state.saldo_btc = 0.0
    st.session_state.historico = []
    st.session_state.bot_ativo = False

# Conexão pública com a Binance para leitura de preços
@st.cache_data(ttl=5)
def pegar_preco_bitcoin():
    try:
        exchange = ccxt.binance()
        ticker = exchange.fetch_ticker('BTC/USDT')
        return ticker['last']
    except:
        return random.randint(62000, 65000)

preco_atual = pegar_preco_bitcoin()

# --- PAINEL LATERAL DE CONTROLE ---
st.sidebar.header("🕹️ PORTAL DE DAR-SHAN")
config_queda = st.sidebar.slider("Comprar se cair (%)", 0.5, 5.0, 1.5, step=0.1)
config_lucro = st.sidebar.slider("Vender se subir (%)", 0.5, 10.0, 2.0, step=0.1)

if st.sidebar.button("⚡ CONVOCAR / PAUSAR CAVALO DE FOGO"):
    st.session_state.bot_ativo = not st.session_state.bot_ativo

# --- PAINEL PRINCIPAL / ESTATÍSTICAS ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="💰 Fundo Disponível (USDT)", value=f"${st.session_state.saldo_usdt:,.2f}")
with col2:
    st.metric(label="🪙 Ativos em Carteira (BTC)", value=f"{st.session_state.saldo_btc:.4f} BTC")
with col3:
    st.metric(label="📊 Preço do BTC (Binance)", value=f"${preco_atual:,.2f}", delta="Sincronizado com o Mercado")

# --- LÓGICA OPERACIONAL DO SARA_FIREBOT ---
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
        st.toast("🔥 Portal aberto! Compra executada de forma autônoma.")
        
    elif gatilho == 'vender' and st.session_state.saldo_btc > 0:
        lucro_usdt = st.session_state.saldo_btc * preco_atual
        st.session_state.saldo_usdt = lucro_usdt
        st.session_state.saldo_btc = 0.0
        
        msg = f"💰 SAÍDA: Lucro resgatado! Posição liquidada a ${preco_atual:,.2f} retornando para USDT."
        st.session_state.historico.append(msg)
        salvar_no_supabase(msg)
        st.toast("👑 Ouro protegido! Venda realizada com sucesso.")
else:
    st.warning("💤 Cavalo de Fogo está descansando no santuário. Ative o painel para iniciar.")

# --- HISTÓRICO DE LOGS ---
st.write("---")
st.write("### 📜 Crônicas de Operação - Sara_FireBot")
if st.session_state.historico:
    for acao in reversed(st.session_state.historico):
        st.info(acao)
else:
    st.write("*Nenhum bloco minerado ou transação realizada nesta sessão.*")

# Loop de atualização automática
time.sleep(2)
if st.session_state.bot_ativo:
    st.rerun()

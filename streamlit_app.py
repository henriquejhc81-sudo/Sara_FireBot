import streamlit as st
import ccxt
import time
import random
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client

# Configuração da página do Streamlit com estilo Dar-Shan / Cavalo de Fogo
st.set_page_config(page_title="Sara_FireBot - Auto Bot", page_icon="🐴", layout="wide")

# Inicialização de variáveis de sessão essenciais
if 'saldo_usdt' not in st.session_state:
    st.session_state.saldo_usdt = 10000.0
    st.session_state.saldo_btc = 0.0
    st.session_state.historico = []
    st.session_state.bot_ativo = False
    st.session_state.preco_referencia = 0.0
    st.session_state.historico_precos = []  # Para alimentar o gráfico dinâmico

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

st.title("🐴 SARA_FIREBOT — AUTONOMOUS BOT V2")
st.markdown("<p class='subtitle'>🔥 Algoritmo de Dar-Shan: Inteligência Matemática e Estratégia Real</p>", unsafe_allow_html=True)

# --- CONEXÃO SEGURA COM SUPABASE (VIA SECRETS) ---
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

# Conexão pública para leitura de preços reais da Binance
@st.cache_data(ttl=3)
def pegar_preco_bitcoin():
    try:
        exchange = ccxt.binance()
        ticker = exchange.fetch_ticker('BTC/USDT')
        return ticker['last']
    except:
        # Fallback inteligente com leve oscilação para manter o gráfico vivo se a API falhar
        base = 65000 if not st.session_state.historico_precos else st.session_state.historico_precos[-1]['preco']
        return base + random.uniform(-75, 75)

preco_atual = pegar_preco_bitcoin()

# Salva o preço atual no histórico para gerar o gráfico temporal
tempo_agora = datetime.now().strftime('%H:%M:%S')
st.session_state.historico_precos.append({'hora': tempo_agora, 'preco': preco_atual})
if len(st.session_state.historico_precos) > 30:  # Mantém apenas os últimos 30 pontos no gráfico
    st.session_state.historico_precos.pop(0)

# --- INTERFACE UNIFICADA ---
col_config1, col_config2 = st.columns(2)
with col_config1:
    config_queda = st.slider("Comprar se o mercado cair (%)", 0.1, 5.0, 0.5, step=0.1)
with col_config2:
    config_lucro = st.slider("Vender se o mercado subir (%)", 0.1, 10.0, 1.0, step=0.1)

st.write("")

# Lógica do Botão Liga/Desliga
texto_botao = "🟢 DESCANSAR CAVALO DE FOGO (PAUSAR)" if st.session_state.bot_ativo else "🔴 CONVOCAR CAVALO DE FOGO (LIGAR)"
if st.button(texto_botao):
    st.session_state.bot_ativo = not st.session_state.bot_ativo
    if st.session_state.bot_ativo:
        st.session_state.preco_referencia = preco_atual  # Define o ponto zero da estratégia
    st.rerun()

st.write("---")

# --- PAINEL DE MÉTRICAS ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="💰 Fundo Disponível (USDT)", value=f"${st.session_state.saldo_usdt:,.2f}")
with col2:
    st.metric(label="🪙 Ativos em Carteira (BTC)", value=f"{st.session_state.saldo_btc:.4f} BTC")
with col3:
    st.metric(label="📊 Preço Atual BTC", value=f"${preco_atual:,.2f}", 
              delta=f"Alvo Compra: ${st.session_state.preco_referencia * (1 - config_queda/100):,.2f}" if st.session_state.bot_ativo and st.session_state.saldo_usdt > 0 else "Análise Ativa")

st.write("")

# --- RENDERIZAÇÃO DO GRÁFICO EM TEMPO REAL ---
df_precos = pd.DataFrame(st.session_state.historico_precos)
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_precos['hora'], y=df_precos['preco'], mode='lines+markers',
                         line=dict(color='#ff4500', width=3),
                         marker=dict(color='#ffa500', size=6),
                         name='Preço BTC'))
fig.update_layout(title="📈 Flutuação de Mercado de Dar-Shan (Live)",
                  template="plotly_dark",
                  paper_bgcolor='rgba(0,0,0,0)',
                  plot_bgcolor='rgba(0,0,0,0)',
                  xaxis=dict(showgrid=False),
                  yaxis=dict(showgrid=True, gridcolor='#221111'),
                  margin=dict(l=20, r=20, t=40, b=20),
                  height=300)
st.plotly_chart(fig, use_container_width=True)

# --- MOTOR DE ESTRATÉGIA MATEMÁTICA ---
if st.session_state.bot_ativo:
    st.success(f"🔥 SARA_FIREBOT MONITORANDO MERCADO. Preço de Referência Base: ${st.session_state.preco_referencia:,.2f}")
    
    # Calcula a variação percentual atual em relação ao preço de referência
    variacao_percentual = ((preco_atual - st.session_state.preco_referencia) / st.session_state.preco_referencia) * 100
    
    # Caso 1: Robô tem dólares e mercado caiu o esperado -> COMPRA
    if st.session_state.saldo_usdt > 100 and variacao_percentual <= -config_queda:
        quantidade_comprar = st.session_state.saldo_usdt / preco_atual
        st.session_state.saldo_btc += quantidade_comprar
        st.session_state.saldo_usdt = 0.0
        st.session_state.preco_referencia = preco_atual  # Atualiza a referência para a próxima venda
        
        msg = f"🛒 ENTRADA: Mercado recuou {variacao_percentual:.2f}%. Cavalo de Fogo executou COMPRA de {quantidade_comprar:.4f} BTC a ${preco_atual:,.2f}"
        st.session_state.historico.append(msg)
        salvar_no_supabase(msg)
        st.toast("🔥 Alvo de queda atingido! Compra executada.")
        st.rerun()
        
    # Caso 2: Robô tem Bitcoin e mercado subiu o esperado -> VENDA
    elif st.session_state.saldo_btc > 0 and variacao_percentual >= config_lucro:
        lucro_usdt = st.session_state.saldo_btc * preco_atual
        st.session_state.saldo_usdt = lucro_usdt
        st.session_state.saldo_btc = 0.0
        st.session_state.preco_referencia = preco_atual  # Atualiza a referência para a próxima compra
        
        msg = f"💰 SAÍDA: Meta de lucro atingida (+{variacao_percentual:.2f}%)! Venda realizada a ${preco_atual:,.2f}. Ouro protegido!"
        st.session_state.historico.append(msg)
        salvar_no_supabase(msg)
        st.toast("👑 Meta batida! Lucro realizado.")
        st.rerun()
else:
    st.warning("💤 Cavalo de Fogo está descansando no santuário. Ative o painel para iniciar o rastreamento.")

# --- CRÔNICAS DE OPERAÇÃO ---
st.write("---")
st.write("### 📜 Crônicas de Operação - Sara_FireBot")
if st.session_state.historico:
    for acao in reversed(st.session_state.historico):
        st.info(acao)
else:
    st.write("*Aguardando gatilhos matemáticos nos preços para registrar os blocos de transações.*")

# Ciclo automático de atualização dinâmica da tela
time.sleep(3)
if st.session_state.bot_ativo:
    st.rerun()

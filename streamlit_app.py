import streamlit as st
import ccxt
import time
import random
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client

# Configuração da Página
st.set_page_config(page_title="Sara_Firebolt - Auto Bot", page_icon="⚡", layout="wide")

# Inicialização do Estado Interno
if 'saldo_usdt' not in st.session_state:
    st.session_state.saldo_usdt = 10000.0
    st.session_state.saldo_btc = 0.0
    st.session_state.historico = []
    st.session_state.bot_ativo = False
    st.session_state.preco_referencia = 0.0
    st.session_state.historico_precos = []
    st.session_state.queda_autonoma = 0.15
    st.session_state.lucro_autonomo = 0.35

# Banco de Dados Supabase (Fundo Otimizado)
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def guardar_log(msg):
    if supabase:
        try:
            supabase.table("historico_bot").insert({"operacao": msg}).execute()
            res = supabase.table("historico_bot").select("id").order("id", desc=True).execute()
            if len(res.data) > 50:
                supabase.table("historico_bot").delete().lt("id", res.data[-1]["id"]).execute()
        except: pass

# Inteligência de Volatilidade da Janela Temporal
@st.cache_data(ttl=20)
def recalcular_alvos_mercado():
    try:
        ex = ccxt.binance()
        velas = ex.fetch_ohlcv('BTC/USDT', timeframe='1m', limit=30)
        df = pd.DataFrame(velas, columns=['t', 'o', 'h', 'l', 'c', 'v'])
        var_media = ((df['h'] - df['l']) / df['l']).mean() * 100
        return max(0.05, round(var_media * 0.4, 2)), max(0.10, round(var_media * 0.9, 2))
    except:
        return 0.10, 0.20

if st.session_state.bot_ativo:
    st.session_state.queda_autonoma, st.session_state.lucro_autonomo = recalcular_alvos_mercado()

# Captura de Preço Real da Binance (Movido para cima para corrigir o NameError)
@st.cache_data(ttl=2)
def pegar_preco_binance():
    try: return ccxt.binance().fetch_ticker('BTC/USDT')['last']
    except: return None

res_preco = pegar_preco_binance()
preco_atual = res_preco if res_preco is not None else (st.session_state.historico_precos[-1]['preco'] + random.uniform(-8, 8) if st.session_state.historico_precos else 64138.0)

st.session_state.historico_precos.append({'hora': datetime.now().strftime('%H:%M:%S'), 'preco': preco_atual})
if len(st.session_state.historico_precos) > 30: st.session_state.historico_precos.pop(0)

# Cores e Estilos CSS (Sem ícones e com espaçamento otimizado)
cor_b = "#00cc66" if st.session_state.bot_ativo else "#cc3333"
cor_h = "#00aa55" if st.session_state.bot_ativo else "#aa2222"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0b0f17; color: #ffffff; font-family: sans-serif; }}
    h1 {{ color: #ff5500 !important; text-align: left; font-size: 1.8rem; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 20px; }}
    
    div.stButton > button:first-child {{
        background-color: {cor_b} !important; color: white !important; border: none !important;
        padding: 10px 20px !important; font-size: 14px !important; font-weight: bold !important;
        border-radius: 6px !important; width: auto !important; transition: all 0.3s ease !important;
        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;
    }}
    div.stButton > button:first-child:hover {{ background-color: {cor_h} !important; }}
    
    .metric-container {{ display: flex; gap: 15px; margin-bottom: 15px; }}
    .metric-card {{ background-color: #121824; border: 1px solid #1f293d; padding: 12px 20px; border-radius: 6px; flex: 1; text-align: center; }}
    .metric-title {{ color: #8492a6; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 3px; }}
    .metric-value {{ color: #ffffff; font-size: 1.3rem; font-weight: 700; }}
    
    .ia-banner {{ background-color: #0c2520; border-left: 4px solid #00cc66; padding: 10px 15px; border-radius: 4px; color: #00ffaa; font-size: 0.85rem; font-weight: 600; margin-bottom: 15px; }}
    .log-box {{ background-color: #121824; border: 1px solid #1f293d; padding: 10px 15px; border-radius: 6px; color: #8492a6; font-size: 0.85rem; margin-bottom: 8px; font-family: monospace; }}
    .log-box-buy {{ color: #00ffaa; }}
    .log-box-sell {{ color: #ff5555; }}
    </style>
""", unsafe_allow_html=True)

# Topo do Dashboard (Nome atualizado sem o ícone do cavalo)
st.title("SARA_FIREBOLT — ADAPTIVE QUANTUM V3")

# Botão de Ação Reativo (Agora com a variável preco_atual já declarada acima)
txt_btn = "🟢 RADAR ATIVO (CLIQUE PARA PAUSAR)" if st.session_state.bot_ativo else "🔴 RADAR OFFLINE (CLIQUE PARA LIGAR)"
if st.button(txt_btn):
    st.session_state.bot_ativo = not st.session_state.bot_ativo
    if st.session_state.bot_ativo: st.session_state.preco_referencia = preco_atual
    st.rerun()

# Renderização dos Cards Alinhados e Compactos
st.markdown(f"""
    <div class='metric-container'>
        <div class='metric-card'>
            <div class='metric-title'>🔒 Saldo USDT</div>
            <div class='metric-value'>${st.session_state.saldo_usdt:,.2f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>🪙 Saldo BTC</div>
            <div class='metric-value'>{st.session_state.saldo_btc:.4f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>📊 Preço BTC (Binance)</div>
            <div class='metric-value'>${preco_atual:,.2f}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Banner de Status de Inteligência Temporal
if st.session_state.bot_ativo:
    st.markdown(f"<div class='ia-banner'>🎯 IA TEMPORAL: Janela Ativa | Alvo Queda: -{st.session_state.queda_autonoma}% | Alvo Lucro: +{st.session_state.lucro_autonomo}%</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='ia-banner' style='background-color: #241c1c; border-left-color: #cc3333; color: #ff6666;'>💤 IA TEMPORAL: Sistema em modo de descanso no santuário.</div>", unsafe_allow_html=True)

# Gráfico Técnico Ocultado/Integrado de Forma Fluida
df_p = pd.DataFrame(st.session_state.historico_precos)
fig = go.Figure(go.Scatter(x=df_p['hora'], y=df_p['preco'], mode='lines', line=dict(color='#ff5500', width=2), fill='tozeroy', fillcolor='rgba(255, 85, 0, 0.01)'))
fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=5, r=5, t=5, b=5), height=100, xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=False, visible=False))
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# Processamento do Motor Algorítmico
if st.session_state.bot_ativo:
    diff = ((preco_atual - st.session_state.preco_referencia) / st.session_state.preco_referencia) * 100
    
    if st.session_state.saldo_usdt > 100 and diff <= -st.session_state.queda_autonoma:
        qtd = st.session_state.saldo_usdt / preco_atual
        st.session_state.saldo_btc, st.session_state.saldo_usdt, st.session_state.preco_referencia = qtd, 0.0, preco_atual
        msg = f"🛒 [{datetime.now().strftime('%H:%M:%S')}] COMPRA: Entrada executada a ${preco_atual:,.2f} | Gatilho IA: -{st.session_state.queda_autonoma}%"
        st.session_state.historico.append(msg)
        guardar_log(msg)
        st.toast("🔥 Compra executada pelo radar!")
        st.rerun()
        
    elif st.session_state.saldo_btc > 0 and diff >= st.session_state.lucro_autonomo:
        lucro = st.session_state.saldo_btc * preco_atual
        st.session_state.saldo_usdt, st.session_state.saldo_btc, st.session_state.preco_referencia = lucro, 0.0, preco_atual
        msg = f"💰 [{datetime.now().strftime('%H:%M:%S')}] VENDA: Liquidação feita a ${preco_atual:,.2f} com lucro! | [IA: +{diff:.2f}%]"
        st.session_state.historico.append(msg)
        guardar_log(msg)
        st.toast("👑 Lucro coletado pelo radar!")
        st.rerun()

# Histórico de Transações Estilizado e Botão de Download Integrado de forma limpa
st.markdown("### 📜 Histórico de Caça")

if st.session_state.historico:
    csv_data = pd.DataFrame(st.session_state.historico, columns=["Logs"]).to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Baixar Relatório de Caça (CSV)", data=csv_data, file_name="sara_firebolt_logs.csv", mime='text/csv')
    st.write("")
    
    for acao in reversed(st.session_state.historico):
        classe_cor = "log-box-buy" if "COMPRA" in acao else "log-box-sell"
        st.markdown(f"<div class='log-box {classe_cor}'>{acao}</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='log-box'>*Aguardando variação analítica de Dar-Shan para registrar as crônicas.*</div>", unsafe_allow_html=True)

# Loop de Atualização Contínua
time.sleep(2)
if st.session_state.bot_ativo: st.rerun()

import streamlit as st
import ccxt
import time
import random
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client

# Configuração da Página - Modo Compacto e Imersivo
st.set_page_config(page_title="Sara_Firebolt", page_icon="⚡", layout="wide")

# Inicialização do Estado Interno
if 'saldo_usdt' not in st.session_state:
    st.session_state.saldo_usdt = 10000.0
    st.session_state.saldo_btc = 0.0
    st.session_state.historico = []
    st.session_state.bot_ativo = False
    st.session_state.preco_referencia = 0.0
    st.session_state.historico_precos = []
    st.session_state.queda_autonoma = 0.08
    st.session_state.lucro_autonomo = 0.18

# Banco de Dados Supabase
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
@st.cache_data(ttl=15)
def recalcular_alvos_mercado():
    try:
        ex = ccxt.binance()
        velas = ex.fetch_ohlcv('BTC/USDT', timeframe='1m', limit=20)
        df = pd.DataFrame(velas, columns=['t', 'o', 'h', 'l', 'c', 'v'])
        var_media = ((df['h'] - df['l']) / df['l']).mean() * 100
        return max(0.04, round(var_media * 0.4, 2)), max(0.08, round(var_media * 0.9, 2))
    except:
        return 0.08, 0.18

if st.session_state.bot_ativo:
    st.session_state.queda_autonoma, st.session_state.lucro_autonomo = recalcular_alvos_mercado()

# Captura de Preço Real da Binance
@st.cache_data(ttl=2)
def pegar_preco_binance():
    try: return ccxt.binance().fetch_ticker('BTC/USDT')['last']
    except: return None

res_preco = pegar_preco_binance()
preco_atual = res_preco if res_preco is not None else (st.session_state.historico_precos[-1]['preco'] + random.uniform(-3, 3) if st.session_state.historico_precos else 64188.0)

st.session_state.historico_precos.append({'hora': datetime.now().strftime('%H:%M:%S'), 'preco': preco_atual})
if len(st.session_state.historico_precos) > 20: st.session_state.historico_precos.pop(0)

# Cores e Estilos CSS Avançados para Limpeza Máxima
cor_b = "#10b981" if st.session_state.bot_ativo else "#ef4444"
cor_h = "#059669" if st.session_state.bot_ativo else "#dc2626"

st.markdown(f"""
    <style>
    /* REMOVE A FAIXA SUPERIOR BRANCA PADRÃO DO STREAMLIT */
    header, [data-testid="stHeader"] {{ visibility: hidden; height: 0px !important; background: transparent !important; }}
    footer {{ visibility: hidden; }}
    .block-container {{ padding-top: 2rem !important; padding-bottom: 0rem !important; }}
    
    /* Fundo imersivo escuro */
    .stApp {{ background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
    
    /* Título SARA_FIREBOLT */
    h1 {{ color: #d4af37 !important; text-align: left; font-size: 2.2rem; font-weight: 700; margin-bottom: 15px; margin-top: -10px; }}
    h3 {{ color: #e1b12c !important; font-size: 1.1rem; font-weight: 600; margin-top: 10px; margin-bottom: 10px; }}
    
    /* Botão Retangular Compacto */
    div.stButton > button:first-child {{
        background-color: {cor_b} !important; color: white !important; border: none !important;
        padding: 8px 20px !important; font-size: 13px !important; font-weight: 600 !important;
        border-radius: 4px !important; width: auto !important; transition: all 0.2s ease !important;
        margin-bottom: 10px;
    }}
    div.stButton > button:first-child:hover {{ background-color: {cor_h} !important; }}
    
    /* Grid de Métricas Ultra-Compacto */
    .metric-container {{ display: flex; gap: 15px; margin-bottom: 10px; }}
    .metric-card {{ background-color: #161b22; border: 1px solid #30363d; padding: 12px 18px; border-radius: 6px; flex: 1; text-align: left; }}
    .metric-title {{ color: #8b949e; font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }}
    .metric-value {{ color: #f0f6fc; font-size: 1.4rem; font-weight: 600; }}
    
    /* Banner da IA */
    .ia-banner {{ background-color: #1c1912; border-left: 3px solid #d4af37; padding: 10px 14px; border-radius: 4px; color: #e1b12c; font-size: 0.82rem; font-weight: 500; margin-bottom: 10px; }}
    
    /* Logs Curtos para caber na Tela */
    .log-box {{ background-color: #161b22; border: 1px solid #30363d; padding: 8px 14px; border-radius: 6px; color: #8b949e; font-size: 0.82rem; margin-bottom: 6px; font-family: monospace; }}
    .log-box-buy {{ border-left: 3px solid #10b981; color: #f0f6fc; }}
    .log-box-sell {{ border-left: 3px solid #d4af37; color: #f0f6fc; }}
    </style>
""", unsafe_allow_html=True)

# Título Limpo
st.title("SARA_FIREBOLT")

# Controle do Radar
txt_btn = "🟢 RADAR ATIVO (PAUSAR)" if st.session_state.bot_ativo else "🔴 RADAR OFFLINE (INICIAR)"
if st.button(txt_btn):
    st.session_state.bot_ativo = not st.session_state.bot_ativo
    if st.session_state.bot_ativo: st.session_state.preco_referencia = preco_atual
    st.rerun()

# Cards Alinhados
st.markdown(f"""
    <div class='metric-container'>
        <div class='metric-card'>
            <div class='metric-title'>Saldo USDT</div>
            <div class='metric-value'>${st.session_state.saldo_usdt:,.2f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Saldo BTC</div>
            <div class='metric-value'>{st.session_state.saldo_btc:.4f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Preço BTC (Binance)</div>
            <div class='metric-value'>${preco_atual:,.2f}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Banner de Monitoramento
if st.session_state.bot_ativo:
    st.markdown(f"<div class='ia-banner'>✨ MONITORAMENTO AUTOMÁTICO ATIVO | Janela de Alvos: Compra se recuar {st.session_state.queda_autonoma}% • Venda se valorizar {st.session_state.lucro_autonomo}%</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='ia-banner' style='background-color: #211818; border-left-color: #ef4444; color: #f87171;'>💤 SISTEMA EM MODO OCIOSO. Rastreamento temporal desativado.</div>", unsafe_allow_html=True)

# Mini-gráfico reduzido a nível mínimo para não empurrar os elementos
df_p = pd.DataFrame(st.session_state.historico_precos)
fig = go.Figure(go.Scatter(x=df_p['hora'], y=df_p['preco'], mode='lines', line=dict(color='#d4af37', width=1), fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.002)'))
fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=0, b=0), height=35, xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=False, visible=False))
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# Lógica Interna Quantitativa
if st.session_state.bot_ativo:
    diff = ((preco_atual - st.session_state.preco_referencia) / st.session_state.preco_referencia) * 100
    
    if st.session_state.saldo_usdt > 100 and diff <= -st.session_state.queda_autonoma:
        qtd = st.session_state.saldo_usdt / preco_atual
        st.session_state.saldo_btc, st.session_state.saldo_usdt, st.session_state.preco_referencia = qtd, 0.0, preco_atual
        msg = f"🛒 COMPRA [{datetime.now().strftime('%H:%M:%S')}]: Posição montada a ${preco_atual:,.2f} | Variação: {diff:.2f}%"
        st.session_state.historico.append(msg)
        guardar_log(msg)
        st.toast("⚡ Entrada executada de forma autônoma.")
        st.rerun()
        
    elif st.session_state.saldo_btc > 0 and diff >= st.session_state.lucro_autonomo:
        lucro = st.session_state.saldo_btc * preco_atual
        st.session_state.saldo_usdt, st.session_state.saldo_btc, st.session_state.preco_referencia = lucro, 0.0, preco_atual
        msg = f"💰 VENDA [{datetime.now().strftime('%H:%M:%S')}]: Liquidação feita a ${preco_atual:,.2f} | Lucro: +{diff:.2f}%"
        st.session_state.historico.append(msg)
        guardar_log(msg)
        st.toast("✨ Alvo atingido! Capital em USDT protegido.")
        st.rerun()

# Seção de Histórico de Caça Subida e Unificada
st.markdown("### Histórico de Caça")

if st.session_state.historico:
    csv_data = pd.DataFrame(st.session_state.historico, columns=["Logs"]).to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Baixar Logs (CSV)", data=csv_data, file_name="sara_firebolt_logs.csv", mime='text/csv')
    st.write("")
    
    for acao in reversed(st.session_state.historico):
        classe_cor = "log-box-buy" if "COMPRA" in acao else "log-box-sell"
        st.markdown(f"<div class='log-box {classe_cor}'>{acao}</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='log-box'>*Nenhuma operação realizada pelo algoritmo nesta sessão.*</div>", unsafe_allow_html=True)

# Atualização em tempo real
time.sleep(2)
if st.session_state.bot_ativo: st.rerun()

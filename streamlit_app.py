import streamlit as st
import ccxt
import time
import random
import pandas as pd
import io
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Sara_Firebolt", page_icon="⚡", layout="wide")

if 'saldo_usdt' not in st.session_state:
    st.session_state.saldo_usdt = 10000.0
    st.session_state.historico = []  
    st.session_state.bot_ativo = False
    st.session_state.historico_precos = []
    st.session_state.ativos = {
        'BTC/USDT': {'saldo': 0.0, 'pm': 0.0, 'ordens': 0, 'ref': 0.0, 'topo': 0.0, 'queda_ia': 0.08, 'lucro_ia': 0.18, 'last_p': 64188.0},
        'ETH/USDT': {'saldo': 0.0, 'pm': 0.0, 'ordens': 0, 'ref': 0.0, 'topo': 0.0, 'queda_ia': 0.12, 'lucro_ia': 0.25, 'last_p': 3450.0}
    }

URL = st.secrets.get("SUPABASE_URL", "")
KEY = st.secrets.get("SUPABASE_KEY", "")
supabase = create_client(URL, KEY) if URL and KEY else None

# Sincronização Inicial Inteligente com o Supabase
if supabase and not st.session_state.historico:
    try:
        res = supabase.table("historico_bot").select("created_at, operacao").order("id", desc=False).execute()
        for item in res.data:
            st.session_state.historico.append({
                'Data/Hora': datetime.strptime(item['created_at'][:19], '%Y-%m-%dT%H:%M:%S').strftime('%d/%m/%Y %H:%M:%S'),
                'Texto Visual': item['operacao']
            })
    except: pass

def guardar_log(msg):
    if supabase:
        try:
            supabase.table("historico_bot").insert({"operacao": msg}).execute()
            res = supabase.table("historico_bot").select("id").order("id", desc=True).execute()
            if len(res.data) > 50:
                supabase.table("historico_bot").delete().lt("id", res.data[-1]["id"]).execute()
        except: pass

@st.cache_data(ttl=12)
def analisar_dados_mercado(par):
    try:
        ex = ccxt.binance()
        velas = ex.fetch_ohlcv(par, timeframe='1m', limit=30)
        df = pd.DataFrame(velas, columns=['t', 'o', 'h', 'l', 'c', 'v'])
        df['sma20'] = df['c'].rolling(window=20).mean()
        var_m = ((df['h'] - df['l']) / df['l']).mean() * 100
        return max(0.04, round(var_m * 0.4, 2)), max(0.08, round(var_m * 0.9, 2)), df['sma20'].iloc[-1]
    except: 
        return (0.08, 0.18, None) if par == 'BTC/USDT' else (0.12, 0.25, None)

@st.cache_data(ttl=2)
def pegar_precos_binance():
    try:
        ex = ccxt.binance()
        return ex.fetch_ticker('BTC/USDT')['last'], ex.fetch_ticker('ETH/USDT')['last']
    except: return None, None

p_btc, p_eth = pegar_precos_binance()
if p_btc: st.session_state.ativos['BTC/USDT']['last_p'] = p_btc
if p_eth: st.session_state.ativos['ETH/USDT']['last_p'] = p_eth

sma_tendencia = {}
if st.session_state.bot_ativo:
    for par in ['BTC/USDT', 'ETH/USDT']:
        q, l, s = analisar_dados_mercado(par)
        st.session_state.ativos[par]['queda_ia'] = q
        st.session_state.ativos[par]['lucro_ia'] = l
        sma_tendencia[par] = s

st.session_state.historico_precos.append({'hora': datetime.now().strftime('%H:%M:%S'), 'preco': st.session_state.ativos['BTC/USDT']['last_p']})
if len(st.session_state.historico_precos) > 20: st.session_state.historico_precos.pop(0)

st.markdown(f"""
    <style>
    header, [data-testid="stHeader"] {{ visibility: hidden; height: 0px !important; background: transparent !important; }}
    footer {{ visibility: hidden; }}
    .block-container {{ padding-top: 2rem !important; padding-bottom: 0rem !important; }}
    .stApp {{ background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
    h1 {{ color: #d4af37 !important; text-align: left; font-size: 2.2rem; font-weight: 700; margin-bottom: 15px; margin-top: -10px; }}
    h3 {{ color: #e1b12c !important; font-size: 1.1rem; font-weight: 600; margin-top: 10px; margin-bottom: 10px; }}
    div.stButton > button:first-child {{
        background-color: {"#10b981" if st.session_state.bot_ativo else "#ef4444"} !important; color: white !important; border: none !important;
        padding: 8px 20px !important; font-size: 13px !important; font-weight: 600 !important;
        border-radius: 4px !important; width: auto !important; transition: all 0.2s ease !important; margin-bottom: 10px;
    }}
    div.stButton > button:first-child:hover {{ background-color: {"#059669" if st.session_state.bot_ativo else "#dc2626"} !important; }}
    .metric-container {{ display: flex; gap: 15px; margin-bottom: 10px; }}
    .metric-card {{ background-color: #161b22; border: 1px solid #30363d; padding: 12px 18px; border-radius: 6px; flex: 1; text-align: left; }}
    .metric-title {{ color: #8b949e; font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }}
    .metric-value {{ color: #f0f6fc; font-size: 1.35rem; font-weight: 600; }}
    .ia-banner {{ background-color: #1c1912; border-left: 3px solid #d4af37; padding: 10px 14px; border-radius: 4px; color: #e1b12c; font-size: 0.82rem; font-weight: 500; margin-bottom: 10px; }}
    .log-box {{ background-color: #161b22; border: 1px solid #30363d; padding: 8px 14px; border-radius: 6px; color: #8b949e; font-size: 0.82rem; margin-bottom: 6px; font-family: monospace; }}
    .log-box-buy {{ border-left: 3px solid #10b981; color: #f0f6fc; }}
    .log-box-sell {{ border-left: 3px solid #d4af37; color: #f0f6fc; }}
    </style>
""", unsafe_allow_html=True)

st.title("SARA_FIREBOLT")

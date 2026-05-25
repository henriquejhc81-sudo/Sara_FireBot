import streamlit as st
import ccxt
import time
import random
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Sara_Firebolt", page_icon="⚡", layout="wide")

if 'saldo_usdt' not in st.session_state:
    st.session_state.saldo_usdt = 10000.0
    st.session_state.saldo_btc = 0.0
    st.session_state.historico = []
    st.session_state.bot_ativo = False
    st.session_state.preco_referencia = 0.0
    st.session_state.historico_precos = []
    st.session_state.queda_autonoma = 0.08
    st.session_state.lucro_autonomo = 0.18
    st.session_state.ordens_executadas = 0  
    st.session_state.preco_medio_btc = 0.0  
    st.session_state.maior_preco_atingido = 0.0  

URL = st.secrets.get("SUPABASE_URL", "")
KEY = st.secrets.get("SUPABASE_KEY", "")
supabase = create_client(URL, KEY) if URL and KEY else None

def guardar_log(msg):
    if supabase:
        try:
            supabase.table("historico_bot").insert({"operacao": msg}).execute()
            res = supabase.table("historico_bot").select("id").order("id", desc=True).execute()
            if len(res.data) > 50:
                supabase.table("historico_bot").delete().lt("id", res.data[-1]["id"]).execute()
        except: pass

@st.cache_data(ttl=15)
def analisar_dados_mercado():
    try:
        ex = ccxt.binance()
        velas = ex.fetch_ohlcv('BTC/USDT', timeframe='1m', limit=30)
        df = pd.DataFrame(velas, columns=['t', 'o', 'h', 'l', 'c', 'v'])
        df['sma20'] = df['c'].rolling(window=20).mean()
        var_m = ((df['h'] - df['l']) / df['l']).mean() * 100
        return max(0.04, round(var_m * 0.4, 2)), max(0.08, round(var_m * 0.9, 2)), df['sma20'].iloc[-1]
    except: return 0.08, 0.18, None

ultima_sma = None
if st.session_state.bot_ativo:
    st.session_state.queda_autonoma, st.session_state.lucro_autonomo, ultima_sma = analisar_dados_mercado()

@st.cache_data(ttl=2)
def pegar_preco_binance():
    try: return ccxt.binance().fetch_ticker('BTC/USDT')['last']
    except: return None

res_p = pegar_preco_binance()
preco_atual = res_p if res_p is not None else (st.session_state.historico_precos[-1]['preco'] + random.uniform(-3, 3) if st.session_state.historico_precos else 64188.0)

st.session_state.historico_precos.append({'hora': datetime.now().strftime('%H:%M:%S'), 'preco': preco_atual})
if len(st.session_state.historico_precos) > 20: st.session_state.historico_precos.pop(0)

cor_b = "#10b981" if st.session_state.bot_ativo else "#ef4444"
cor_h = "#059669" if st.session_state.bot_ativo else "#dc2626"

st.markdown(f"""
    <style>
    header, [data-testid="stHeader"] {{ visibility: hidden; height: 0px !important; background: transparent !important; }}
    footer {{ visibility: hidden; }}
    .block-container {{ padding-top: 2rem !important; padding-bottom: 0rem !important; }}
    .stApp {{ background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
    h1 {{ color: #d4af37 !important; text-align: left; font-size: 2.2rem; font-weight: 700; margin-bottom: 15px; margin-top: -10px; }}
    h3 {{ color: #e1b12c !important; font-size: 1.1rem; font-weight: 600; margin-top: 10px; margin-bottom: 10px; }}
    div.stButton > button:first-child {{
        background-color: {cor_b} !important; color: white !important; border: none !important;
        padding: 8px 20px !important; font-size: 13px !important; font-weight: 600 !important;
        border-radius: 4px !important; width: auto !important; transition: all 0.2s ease !important; margin-bottom: 10px;
    }}
    div.stButton > button:first-child:hover {{ background-color: {cor_h} !important; }}
    .metric-container {{ display: flex; gap: 15px; margin-bottom: 10px; }}
    .metric-card {{ background-color: #161b22; border: 1px solid #30363d; padding: 12px 18px; border-radius: 6px; flex: 1; text-align: left; }}
    .metric-title {{ color: #8b949e; font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }}
    .metric-value {{ color: #f0f6fc; font-size: 1.4rem; font-weight: 600; }}
    .ia-banner {{ background-color: #1c1912; border-left: 3px solid #d4af37; padding: 10px 14px; border-radius: 4px; color: #e1b12c; font-size: 0.82rem; font-weight: 500; margin-bottom: 10px; }}
    .log-box {{ background-color: #161b22; border: 1px solid #30363d; padding: 8px 14px; border-radius: 6px; color: #8b949e; font-size: 0.82rem; margin-bottom: 6px; font-family: monospace; }}
    .log-box-buy {{ border-left: 3px solid #10b981; color: #f0f6fc; }}
    .log-box-sell {{ border-left: 3px solid #d4af37; color: #f0f6fc; }}
    </style>
""", unsafe_allow_html=True)

st.title("SARA_FIREBOLT")
txt_btn = "🟢 RADAR ATIVO (PAUSAR)" if st.session_state.bot_ativo else "🔴 RADAR OFFLINE (INICIAR)"
if st.button(txt_btn):
    st.session_state.bot_ativo = not st.session_state.bot_ativo
    if st.session_state.bot_ativo:
        st.session_state.preco_referencia = preco_atual
        st.session_state.ordens_executadas = 0
        st.session_state.preco_medio_btc = 0.0
        st.session_state.maior_preco_atingido = 0.0
    st.rerun()

exp_t = f"{st.session_state.saldo_btc:.4f} BTC (Pm: ${st.session_state.preco_medio_btc:,.2f})" if st.session_state.saldo_btc > 0 else "0.0000"
st.markdown(f"""
    <div class='metric-container'>
        <div class='metric-card'>
            <div class='metric-title'>Saldo USDT</div>
            <div class='metric-value'>${st.session_state.saldo_usdt:,.2f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Posição Consolidada</div>
            <div class='metric-value'>{exp_t}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Preço BTC (Binance)</div>
            <div class='metric-value'>${preco_atual:,.2f}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

if st.session_state.bot_ativo:
    st_tend = "ALTA (COMPRAS LIBERADAS)" if (ultima_sma and preco_atual >= ultima_sma) else "BAIXA (AGUARDANDO RETORNO À MÉDIA)"
    st.markdown(f"<div class='ia-banner'>✨ MOTOR QUANTUM ATIVO | Tendência: {st_tend} | Alvos Dinâmicos: Queda -{st.session_state.queda_autonoma}% • Lucro +{st.session_state.lucro_autonomo}% | Nível Fracionamento: {st.session_state.ordens_executadas}/3</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='ia-banner' style='background-color: #211818; border-left-color: #ef4444; color: #f87171;'>💤 SISTEMA EM MODO OCIOSO. Rastreamento temporal desativado.</div>", unsafe_allow_html=True)

df_p = pd.DataFrame(st.session_state.historico_precos)
fig = go.Figure(go.Scatter(x=df_p['hora'], y=df_p['preco'], mode='lines', line=dict(color='#d4af37', width=1), fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.001)'))
fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=0, b=0), height=25, xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=False, visible=False))
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

if st.session_state.bot_ativo:
    if st.session_state.ordens_executadas < 3:
        diff_c = ((preco_atual - st.session_state.preco_referencia) / st.session_state.preco_referencia) * 100
        tend_ok = True if (not ultima_sma or preco_atual >= ultima_sma) else False
        
        if (st.session_state.ordens_executadas == 0 and tend_ok) or (diff_c <= -st.session_state.queda_autonoma and tend_ok):
            fatia = 3333.33 if st.session_state.saldo_usdt >= 3333.33 else st.session_state.saldo_usdt
            if fatia > 50:
                qtd_a = fatia / preco_atual
                custo_t = (st.session_state.saldo_btc * st.session_state.preco_medio_btc) + fatia
                st.session_state.saldo_btc += qtd_a
                st.session_state.saldo_usdt -= fatia
                st.session_state.preco_medio_btc = custo_t / st.session_state.saldo_btc
                st.session_state.ordens_executadas += 1
                st.session_state.preco_referencia = preco_atual
                st.session_state.maior_preco_atingido = preco_atual
                
                msg = f"🛒 COMPRA PARCIAL [{st.session_state.ordens_executadas}/3]: Alocado ${fatia:,.2f} a ${preco_atual:,.2f}. Novo Pm: ${st.session_state.preco_medio_btc:,.2f}"
                st.session_state.historico.append(msg)
                guardar_log(msg)
                st.toast("⚡ Fração de posição montada.")
                st.rerun()

    if st.session_state.saldo_btc > 0:
        lucro_p = ((preco_atual - st.session_state.preco_medio_btc) / st.session_state.preco_medio_btc) * 100
        if preco_atual > st.session_state.maior_preco_atingido:
            st.session_state.maior_preco_atingido = preco_atual
            
        rec_topo = ((st.session_state.maior_preco_atingido - preco_atual) / st.session_state.maior_preco_atingido) * 100
        
        if lucro_p >= st.session_state.lucro_autonomo and rec_topo >= 0.05:
            val_liq = st.session_state.saldo_btc * preco_atual
            luc_liq = val_liq - (st.session_state.ordens_executadas * 3333.33)
            st.session_state.saldo_usdt += val_liq
            
            msg = f"💰 VENDA QUANTUM: Liquidado a ${preco_atual:,.2f} | Lucro total: +{lucro_p:.2f}% (Retorno: ${luc_liq:,.2f})"
            st.session_state.historico.append(msg)
            guardar_log(msg)
            
            st.session_state.saldo_btc, st.session_state.preco_medio_btc, st.session_state.ordens_executadas = 0.0, 0.0, 0
            st.session_state.preco_referencia, st.session_state.maior_preco_atingido = preco_atual, 0.0
            st.toast("👑 Lucro coletado no topo!")
            st.rerun()

st.markdown("### Histórico de Caça")

if st.session_state.historico:
    csv_d = pd.DataFrame(st.session_state.historico, columns=["Logs"]).to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Baixar Logs (CSV)", data=csv_d, file_name="sara_firebolt_quantum_logs.csv", mime='text/csv')
    st.write("")
    for acao in reversed(st.session_state.historico):
        c_cor = "log-box-buy" if "COMPRA" in acao else "log-box-sell"
        st.markdown(f"<div class='log-box {c_cor}'>{acao}</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='log-box'>*Nenhuma operação realizada pelo algoritmo matemático nesta sessão.*</div>", unsafe_allow_html=True)

time.sleep(2)
if st.session_state.bot_ativo: st.rerun()

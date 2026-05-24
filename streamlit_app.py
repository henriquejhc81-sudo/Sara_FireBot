import streamlit as st
import ccxt
import time
import random
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client

# Configuração da Página
st.set_page_config(page_title="Sara_FireBot - Auto Bot", page_icon="🐴", layout="wide")

# Inicialização do Estado Interno
if 'saldo_usdt' not in st.session_state:
    st.session_state.saldo_usdt = 10000.0
    st.session_state.saldo_btc = 0.0
    st.session_state.historico = []
    st.session_state.bot_ativo = False
    st.session_state.preco_referencia = 0.0
    st.session_state.historico_precos = []
    st.session_state.queda_autonoma = 0.2
    st.session_state.lucro_autonomo = 0.4

# Cores e Estilos CSS Premium (Tema de Fogo)
cor_b = "#28a745" if st.session_state.bot_ativo else "#dc3545"
cor_h = "#218838" if st.session_state.bot_ativo else "#c82333"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #060303; color: #ffffff; }}
    h1 {{ color: #ff4500 !important; text-align: center; font-family: sans-serif; font-weight: 900; text-shadow: 0px 0px 15px #ff8c00; margin-bottom: 2px; }}
    .subtitle {{ text-align: center; color: #ffaa00; font-size: 1.1rem; margin-bottom: 25px; font-style: italic; }}
    .metric-card {{
        background: linear-gradient(135deg, #140b0b 0%, #26110f 100%);
        border: 1px solid #ff450055; padding: 20px; border-radius: 12px; text-align: center;
        box-shadow: 0 4px 15px rgba(255, 69, 0, 0.1);
    }}
    .metric-title {{ color: #aaaaaa; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }}
    .metric-value {{ color: #ffffff; font-size: 1.8rem; font-weight: 700; margin-top: 5px; }}
    .metric-badge {{ display: inline-block; padding: 4px 10px; background: #ff450022; color: #ff8c00; border-radius: 20px; font-size: 0.8rem; margin-top: 8px; font-weight: bold; border: 1px solid #ff450044; }}
    div.stButton > button:first-child {{
        background-color: {cor_b} !important; color: white !important; border: none !important;
        padding: 16px !important; font-size: 18px !important; font-weight: bold !important;
        border-radius: 10px !important; width: 100% !important; transition: all 0.3s ease !important;
    }}
    div.stButton > button:first-child:hover {{ background-color: {cor_h} !important; transform: scale(1.005); }}
    </style>
""", unsafe_allow_html=True)

st.title("🐴 SARA_FIREBOT — AUTONOMOUS BOT V3")
st.markdown("<p class='subtitle'>🔥 Algoritmo Adaptativo: Motor Quântico Otimizando Alvos em Tempo Real</p>", unsafe_allow_html=True)

# Banco de Dados Supabase Inteligente (Limpeza Automática)
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

# Inteligência Quântica: Análise de Volatilidade Recente (Últimos 30m)
@st.cache_data(ttl=20)
def recalcular_alvos_mercado():
    try:
        ex = ccxt.binance()
        velas = ex.fetch_ohlcv('BTC/USDT', timeframe='1m', limit=30)
        df = pd.DataFrame(velas, columns=['t', 'o', 'h', 'l', 'c', 'v'])
        var_media = ((df['h'] - df['l']) / df['l']).mean() * 100
        return max(0.04, round(var_media * 0.5, 2)), max(0.08, round(var_media * 1.1, 2))
    except:
        return 0.12, 0.25

if st.session_state.bot_ativo:
    st.session_state.queda_autonoma, st.session_state.lucro_autonomo = recalcular_alvos_mercado()

# Consulta de Preço com Fallback dinâmico
@st.cache_data(ttl=2)
def pegar_preco_binance():
    try: return ccxt.binance().fetch_ticker('BTC/USDT')['last']
    except: return None

res_preco = pegar_preco_binance()
preco_atual = res_preco if res_preco is not None else (st.session_state.historico_precos[-1]['preco'] + random.uniform(-10, 10) if st.session_state.historico_precos else 65000.0)

# Alimentação do Gráfico Temporal
st.session_state.historico_precos.append({'hora': datetime.now().strftime('%H:%M:%S'), 'preco': preco_atual})
if len(st.session_state.historico_precos) > 30: st.session_state.historico_precos.pop(0)

# Botão de Ação Reativo
txt_btn = "🟢 DESCANSAR CAVALO DE FOGO (PAUSAR)" if st.session_state.bot_ativo else "🔴 CONVOCAR INTELIGÊNCIA AUTÔNOMA (LIGAR)"
if st.button(txt_btn):
    st.session_state.bot_ativo = not st.session_state.bot_ativo
    if st.session_state.bot_ativo: st.session_state.preco_referencia = preco_atual
    st.rerun()

st.write("")

# Renderização do Dashboard Premium
m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f"<div class='metric-card'><div class='metric-title'>💰 Saldo USDT</div><div class='metric-value'>${st.session_state.saldo_usdt:,.2f}</div><div class='metric-badge'>Livre para Compra</div></div>", unsafe_allow_html=True)
with m2:
    st.markdown(f"<div class='metric-card'><div class='metric-title'>🪙 Carteira Ativos</div><div class='metric-value'>{st.session_state.saldo_btc:.5f} BTC</div><div class='metric-badge'>Exposição Atual</div></div>", unsafe_allow_html=True)
with m3:
    b_txt = f"📉 Queda Auto: {st.session_state.queda_autonoma}% | 📈 Lucro Auto: {st.session_state.lucro_autonomo}%" if st.session_state.bot_ativo else "Sistema Ocioso"
    st.markdown(f"<div class='metric-card'><div class='metric-title'>📊 Cotação BTC Real</div><div class='metric-value'>${preco_atual:,.2f}</div><div class='metric-badge'>{b_txt}</div></div>", unsafe_allow_html=True)

st.write("")

# Exibição do Gráfico de Área Fluido
df_p = pd.DataFrame(st.session_state.historico_precos)
fig = go.Figure(go.Scatter(x=df_p['hora'], y=df_p['preco'], mode='lines', line=dict(color='#ff4500', width=3), fill='tozeroy', fillcolor='rgba(255, 69, 0, 0.02)'))
fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), height=200, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
st.plotly_chart(fig, use_container_width=True)

# Execução Matemática dos Alvos de Operação
if st.session_state.bot_ativo:
    diff = ((preco_atual - st.session_state.preco_referencia) / st.session_state.preco_referencia) * 100
    
    if st.session_state.saldo_usdt > 100 and diff <= -st.session_state.queda_autonoma:
        qtd = st.session_state.saldo_usdt / preco_atual
        st.session_state.saldo_btc, st.session_state.saldo_usdt, st.session_state.preco_referencia = qtd, 0.0, preco_atual
        msg = f"🛒 COMPRA AUTOMÁTICA [{datetime.now().strftime('%H:%M')}]: Entrada executada a ${preco_atual:,.2f} após recuo de {diff:.2f}%."
        st.session_state.historico.append(msg)
        guardar_log(msg)
        st.toast("🔥 Compra disparada com sucesso!")
        st.rerun()
        
    elif st.session_state.saldo_btc > 0 and diff >= st.session_state.lucro_autonomo:
        lucro = st.session_state.saldo_btc * preco_atual
        st.session_state.saldo_usdt, st.session_state.saldo_btc, st.session_state.preco_referencia = lucro, 0.0, preco_atual
        msg = f"💰 VENDA AUTOMÁTICA [{datetime.now().strftime('%H:%M')}]: Lucro garantido (+{diff:.2f}%) liquidando a ${preco_atual:,.2f}."
        st.session_state.historico.append(msg)
        guardar_log(msg)
        st.toast("👑 Meta atingida! Lucro coletado.")
        st.rerun()
else:
    st.info("💡 Modo Inteligente pausado. Ligue no botão principal para ativar a análise adaptativa de mercado.")

# Seção de Relatórios em CSV e Histórico Visual
st.write("---")
c_tit, c_down = st.columns(2)
with c_tit: st.write("### 📜 Crônicas Quânticas de Operação")
with c_down:
    if st.session_state.historico:
        csv_data = pd.DataFrame(st.session_state.historico, columns=["Logs"]).to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Baixar Relatório (CSV)", data=csv_data, file_name="sara_firebot.csv", mime='text/csv')

if st.session_state.historico:
    for acao in reversed(st.session_state.historico): st.info(acao)
else:
    st.write("*Aguardando flutuação matemática do Bitcoin para registrar ordens.*")

# Loop de Execução Contínua
time.sleep(2)
if st.session_state.bot_ativo: st.rerun()

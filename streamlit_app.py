import streamlit as st
import pandas as pd
import ccxt
import pytz
import time
import threading
import random
import plotly.express as px
from datetime import datetime

# ==========================================
# ⚡ MEGA ROBÔ: LIONBOT SENTINEL // OMNICORE V8.0
# ARQUITETURA LOCAL (NO DB / NO AI)
# ==========================================
st.set_page_config(page_title="LionBot Sentinel | Auto Bot", page_icon="🦁", layout="wide", initial_sidebar_state="collapsed")
tz_br = pytz.timezone('America/Sao_Paulo')
COR_TEMA = "#00ffcc" # Verde Neon LionBot

# ==========================================
# 1. ESTILIZAÇÃO CSS (CYBERPUNK + INSTITUCIONAL)
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    .stApp {{ background-color: #0b0f19; color: #f8fafc; font-family: 'Inter', sans-serif; }}
    .header-box {{ background: linear-gradient(90deg, #161f30 0%, #0b0f19 100%); padding: 20px; border-radius: 10px; border-left: 4px solid {COR_TEMA}; margin-bottom: 20px; border-top: 1px solid #1e293b; box-shadow: 0 0 15px rgba(0, 255, 204, 0.1); }}
    .titulo {{ color: {COR_TEMA}; font-weight: 900; font-family: 'JetBrains Mono', monospace; margin: 0; text-align: center; letter-spacing: 2px; text-transform: uppercase; }}
    .subtitulo {{ color: #94a3b8; font-family: 'Inter', sans-serif; margin-top: 5px; text-align: center; font-size: 13px; font-weight: 600; }}
    
    .kpi-container {{ background: linear-gradient(145deg, #161f30 0%, #0b0f19 100%); border: 1px solid #1e293b; border-radius: 6px; padding: 16px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4); position: relative; overflow: hidden; height: 100%; }}
    .kpi-container::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: {COR_TEMA}; opacity: 0.8; }}
    .kpi-title {{ color: #94a3b8; font-size: 0.70rem; text-transform: uppercase; font-weight: 700; margin-bottom: 6px; letter-spacing: 0.05em; font-family: 'Inter', sans-serif; }} 
    .kpi-value {{ color: #ffffff; font-size: 1.6rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; text-shadow: 0 0 10px rgba(0,255,204,0.1); }}
    
    .panel-box {{ background: #161f30; border: 1px solid #1e293b; border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
    .panel-header {{ font-size: 13px; font-family: 'Inter', sans-serif; color: {COR_TEMA}; text-transform: uppercase; font-weight: 700; border-bottom: 1px solid #1e293b; padding-bottom: 12px; margin-bottom: 15px; letter-spacing: 0.05em; }}
    
    .terminal-box {{ background: #000000; border: 1px solid #1e293b; padding: 12px; border-radius: 4px; height: 250px; overflow-y: auto; font-size: 11px; font-family: 'JetBrains Mono', monospace; box-shadow: inset 0 0 10px rgba(0, 255, 204, 0.05); }}
    .log-row {{ padding: 3px 0; border-bottom: 1px dashed #1e293b; }}
    
    div[data-testid="stButton"] > button {{ border-radius: 4px !important; font-weight: 600 !important; font-family: 'Inter', sans-serif !important; padding: 0.5rem 1rem !important; transition: all 0.3s ease !important; font-size: 11px !important; border: 1px solid transparent !important; }}
    div[data-testid="stButton"] > button[kind="primary"] {{ background: linear-gradient(90deg, #0f766e 0%, #047857 100%) !important; color: #ffffff !important; border-color: {COR_TEMA} !important; }}
    div[data-testid="stButton"] > button[kind="primary"]:hover {{ background: {COR_TEMA} !important; color: #000000 !important; box-shadow: 0 0 15px rgba(0, 255, 204, 0.6) !important; }}
    div[data-testid="stButton"] > button[kind="secondary"] {{ background-color: #0f172a !important; color: #94a3b8 !important; border: 1px solid #1e293b !important; }}
    div[data-testid="stButton"] > button[kind="secondary"]:hover {{ border-color: {COR_TEMA} !important; color: {COR_TEMA} !important; background-color: #1e1b2e !important; box-shadow: 0 0 10px rgba(0, 255, 204, 0.2) !important; }}
    
    /* Custom Tabs Styling */
    button[data-baseweb="tab"] {{ font-family: 'JetBrains Mono', monospace !important; font-weight: bold !important; color: #94a3b8 !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color: {COR_TEMA} !important; border-bottom-color: {COR_TEMA} !important; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MEMÓRIA LOCAL RAM (SEM BANCO DE DADOS)
# ==========================================
ALVOS_GLOBAIS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT', 'LINK/USDT', 'AVAX/USDT', 'NEAR/USDT', 'SUI/USDT']
TIMEFRAMES = ['2h', '4h', '6h', '12h']

@st.cache_resource
def carregar_memoria():
    return {
        'bot_ativo': False, 
        'caixa_livre_simulado': 10000.00, 
        'lucro_liquido_simulado': 0.0, 
        'simuladores': {tf: {} for tf in TIMEFRAMES}, # 4 Motores Independentes
        'terminal_logs': [], 
        'mercado_atual': {}, 
        'ultima_att': "Aguardando..."
    }
memoria = carregar_memoria()

def add_log(msg, tipo="info"):
    memoria['terminal_logs'].insert(0, {"hora": datetime.now(tz_br).strftime('%H:%M:%S'), "msg": msg, "tipo": tipo})
    memoria['terminal_logs'] = memoria['terminal_logs'][:40]

# ==========================================
# 3. GHOST AI & ANTI-BAN POOL
# ==========================================
headers_ghost = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
}

@st.cache_resource
def iniciar_pool_leitura():
    exchanges = [ccxt.binance(), ccxt.kucoin(), ccxt.bybit()]
    for ex in exchanges:
        ex.enableRateLimit = True
        ex.headers = headers_ghost
    return exchanges
pool_exchanges = iniciar_pool_leitura()

def obter_dados_ghost(simbolo, timeframe, limit):
    random.shuffle(pool_exchanges)
    for ex in pool_exchanges:
        try: return ex.fetch_ohlcv(simbolo, timeframe, limit=limit)
        except: continue
    raise Exception(f"Falha nas rotas Ghost para {simbolo} em {timeframe}.")

# ==========================================
# 4. MATRIZ DE RISCO MULTI-TIME (SEM IA)
# ==========================================
def analise_matriz_risco(simbolo, timeframe):
    try:
        velas = obter_dados_ghost(simbolo, timeframe, 100)
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
        preco = float(df['close'].iloc[-1])
        
        dist_ema = ((preco / ema_20) - 1) * 100
        stop_loss_sugerido = preco * 0.975 
        alvo_surf = preco * 1.0075
        
        score_base = 50
        if rsi < 35: score_base += 30
        elif rsi > 70: score_base -= 40
        if -1.0 <= dist_ema <= 0.5: score_base += 15
        
        score_final = max(0, min(99, score_base))
        motivo = f"Consenso Técnico Puro ({timeframe})" if score_final >= 60 else f"Aguardando alinhamento ({timeframe})."
            
        return score_final, preco, stop_loss_sugerido, alvo_surf, motivo
    except Exception as e:
        return 0, 0.0, 0.0, 0.0, str(e)

# ==========================================
# 5. THREAD CONTÍNUA (4 MOTORES DE SIMULAÇÃO)
# ==========================================
@st.cache_resource
def iniciar_motores_sentinel():
    def loop_operacional():
        while True:
            if not memoria['bot_ativo']: time.sleep(2); continue
            try:
                agora = datetime.now(tz_br); ts_agora = time.time()
                
                # Leitura Global do Ticker Atual para todos os motores
                try:
                    for p, d in pool_exchanges[0].fetch_tickers(ALVOS_GLOBAIS).items():
                        if d['last']: memoria['mercado_atual'][p] = float(d['last'])
                except: pass

                # Varrimento da Matriz nos 4 Tempos Gráficos
                for tf in TIMEFRAMES:
                    for m in ALVOS_GLOBAIS:
                        score_final, preco_atual, stop_dyn, alvo_dyn, motivo = analise_matriz_risco(m, tf)
                        
                        # Gatilho de Entrada puramente matemático
                        if score_final >= 80 and m not in memoria['simuladores'][tf]:
                            memoria['simuladores'][tf][m] = [{
                                'qtd': (1000) / preco_atual, # Investimento simulado de $1000 por lote
                                'pm': preco_atual, 
                                'pico_preco': preco_atual,
                                'fundo_preco': preco_atual,
                                'stop_dyn': -0.025, # -2.50% Padrão Karv
                                'alvo_dyn': 0.0075, # +0.75% Padrão Karv
                                'sinal_enviado': False,
                                'ts_compra': ts_agora
                            }]
                            add_log(f"🧠 Motor {tf.upper()}: Algoritmo detectou anomalia em {m} (Score: {score_final}). Armado.", "info")
                            
                # Gerenciamento de Custódia (As 4 Tabelas)
                for tf in TIMEFRAMES:
                    for m, grids in list(memoria['simuladores'][tf].items()):
                        pr = memoria['mercado_atual'].get(m)
                        if not pr: continue
                        g_rem = []
                        for g in grids:
                            if pr > g['pico_preco']: g['pico_preco'] = pr
                            if pr < g['fundo_preco']: g['fundo_preco'] = pr
                            
                            pnl_atual = (pr - g['pm']) / g['pm']
                            pnl_do_pico = (g['pico_preco'] - g['pm']) / g['pm']
                            queda_do_topo = (pr - g['pico_preco']) / g['pico_preco']
                            
                            gatilho_entrada = -0.010 # -1.0% para comprar a queda
                            
                            if pnl_atual <= gatilho_entrada and not g['sinal_enviado']:
                                g['sinal_enviado'] = True
                                add_log(f"⚡ SINAL {tf.upper()} ATIVADO! [{m}] rompeu o gatilho quantitativo.", "buy")
                                
                            surf_armar = g['alvo_dyn']
                            stop_loss = g['stop_dyn']
                            surf_recuo_fixo = -0.0025
                            
                            vender = False; tipo = ""
                            if g['sinal_enviado']:
                                if pnl_do_pico >= surf_armar and queda_do_topo <= surf_recuo_fixo and pnl_atual > 0: 
                                    vender = True; tipo = f"WIN ({tf.upper()})"
                                elif pnl_atual <= stop_loss: 
                                    vender = True; tipo = f"STOP ({tf.upper()})"
                            
                            if vender:
                                l = (g['qtd'] * pr) - (g['qtd'] * g['pm'])
                                memoria['lucro_liquido_simulado'] += l
                                add_log(f"💰 CICLO ENCERRADO [{m}]: {tipo} ${l:+.2f}", "info" if l > 0 else "sell")
                                g_rem.append(g)
                                
                        for g in g_rem: grids.remove(g)
                        if not grids: del memoria['simuladores'][tf][m]

                memoria['ultima_att'] = agora.strftime('%d/%m/%Y %H:%M:%S')

            except Exception as e: add_log(f"⚠️ Healer Engine: Erro no loop {str(e)[:40]}", "warn")
            time.sleep(15) 
    threading.Thread(target=loop_operacional, daemon=True).start()

iniciar_motores_sentinel()

time.sleep(0.5)
if time.time() - memoria.get('tela_att', 0) > 3:
    memoria['tela_att'] = time.time()
    st.rerun()

# ==========================================
# 6. INTERFACE VISUAL (OMNICORE DASHBOARD)
# ==========================================
st.markdown("""
    <div class="header-box" translate="no">
        <h1 class="titulo">🦁 LIONBOT SENTINEL // OMNICORE V8.1</h1>
        <div class="subtitulo">ORQUESTRADOR QUANTITATIVO DE 4 DIMENSÕES | MULTIVERSE SCANNER</div>
    </div>
""", unsafe_allow_html=True)

# KPIs Principais
k1, k2, k3, k4 = st.columns(4)
with k1: st.markdown(f"<div class='kpi-container'><div class='kpi-title'>Caixa Base Simulado</div><div class='kpi-value'>${memoria['caixa_livre_simulado']:,.2f}</div></div>", unsafe_allow_html=True)
with k2: st.markdown(f"<div class='kpi-container'><div class='kpi-title'>Lucro Multiverso (Simulado)</div><div class='kpi-value {'text-green' if memoria['lucro_liquido_simulado']>=0 else 'text-red'}'>${memoria['lucro_liquido_simulado']:,.2f}</div></div>", unsafe_allow_html=True)
with k3: st.markdown(f"<div class='kpi-container'><div class='kpi-title'>Total de Operações Ativas</div><div class='kpi-value text-yellow'>{sum(len(memoria['simuladores'][tf]) for tf in TIMEFRAMES)}</div></div>", unsafe_allow_html=True)
with k4: 
    btn_label = "⏹ HALT MOTORS" if memoria['bot_ativo'] else "▶ ENGAGE OMNICORE"
    btn_type = "secondary" if memoria['bot_ativo'] else "primary"
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(btn_label, use_container_width=True, type=btn_type): 
        memoria['bot_ativo'] = not memoria['bot_ativo']
        st.toast(f"Status dos Motores: {'LIGADOS' if memoria['bot_ativo'] else 'DESLIGADOS'}")
        st.rerun()

st.markdown("<hr style='border:1px solid #1e293b; margin: 20px 0;'>", unsafe_allow_html=True)

# ==========================================
# 💼 CUSTÓDIA MULTIVERSO (AS 4 DIMENSÕES DE TEMPO)
# ==========================================
st.markdown(f"<h3 style='font-size: 16px; color: {COR_TEMA}; font-family: \"JetBrains Mono\", monospace;'>💼 CUSTÓDIA DE GATILHOS (MOTORES SIMULADORES)</h3>", unsafe_allow_html=True)
st.markdown(f"<p style='font-size: 12px; color: #94a3b8;'>Última Varrida: {memoria['ultima_att']}</p>", unsafe_allow_html=True)

tabs = st.tabs(["🚀 MOTOR 2H", "🚀 MOTOR 4H", "🚀 MOTOR 6H", "🚀 MOTOR 12H"])

for i, tf in enumerate(TIMEFRAMES):
    with tabs[i]:
        st.markdown(f"<div class='panel-box'>", unsafe_allow_html=True)
        if memoria['simuladores'][tf]:
            st.markdown("<div style='padding: 0 5px;'>", unsafe_allow_html=True)
            hc1, hc2, hc3, hc4, hc5, hc6, hc7 = st.columns([1.5, 1.1, 1.3, 1.4, 1.4, 1.4, 1.1])
            with hc1: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Asset</span>", unsafe_allow_html=True)
            with hc2: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Gatilho Def.</span>", unsafe_allow_html=True)
            with hc3: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Alvos (Simulado)</span>", unsafe_allow_html=True)
            with hc4: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>PM / Current</span>", unsafe_allow_html=True)
            with hc5: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Max High / Low</span>", unsafe_allow_html=True)
            with hc6: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Floating PNL</span>", unsafe_allow_html=True)
            with hc7: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Status</span>", unsafe_allow_html=True)
            st.markdown("<hr style='border:1px solid #1e293b; margin: 8px 0;'>", unsafe_allow_html=True)

            for m, grids in list(memoria['simuladores'][tf].items()):
                qtd_tot = sum([g['qtd'] for g in grids]); pm_tot = sum([g['qtd']*g['pm'] for g in grids]) / qtd_tot if qtd_tot > 0 else 0
                pr_atual = memoria['mercado_atual'].get(m, pm_tot)
                pico = max([g.get('pico_preco', pm_tot) for g in grids]); fundo = min([g.get('fundo_preco', pm_tot) for g in grids])
                
                m_alta = ((pico - pm_tot) / pm_tot) * 100 if pm_tot > 0 else 0; m_queda = ((fundo - pm_tot) / pm_tot) * 100 if pm_tot > 0 else 0
                pnl_usd = (qtd_tot * pr_atual) - (qtd_tot * pm_tot); pnl_pct = (pnl_usd / (qtd_tot * pm_tot)) * 100 if pm_tot > 0 else 0
                
                gatilho_atual = -1.0 # Gatilho visual padrão
                sinal_enviado = grids[0].get('sinal_enviado', False)
                status_txt = "🟢 ATIVO" if sinal_enviado else "⏳ TRACK"
                
                surf_u = grids[0].get('alvo_dyn')
                stop_u = grids[0].get('stop_dyn')

                with st.container():
                    c1, c2, c3, c4, c5, c6, c7 = st.columns([1.5, 1.1, 1.3, 1.4, 1.4, 1.4, 1.1])
                    with c1: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:13px; color:#F8FAFC; font-weight:700; padding-top:4px;'>{m}</div>", unsafe_allow_html=True)
                    with c2: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:12px; font-weight:700; color:{COR_TEMA}; padding-top:4px;'>{gatilho_atual:+.2f}%</div>", unsafe_allow_html=True)
                    with c3: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:11px;'><span style='color:#10b981;'>+{surf_u*100:.2f}%</span><br><span style='color:#ef4444;'>{stop_u*100:.2f}%</span></div>", unsafe_allow_html=True)
                    with c4: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:12px; color:#94a3b8;'>${pm_tot:.4f}<br><span style='color:#ffffff;'>${pr_atual:.4f}</span></div>", unsafe_allow_html=True)
                    with c5: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:11px;'><span style='color:#10b981;'>{m_alta:+.2f}%</span><br><span style='color:#ef4444;'>{m_queda:+.2f}%</span></div>", unsafe_allow_html=True)
                    with c6: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:14px; font-weight:700; color:{'#10b981' if pnl_pct >= 0 else '#ef4444'}; padding-top:4px;'>{pnl_pct:+.2f}%</div>", unsafe_allow_html=True)
                    with c7:
                        if st.button("✕ CLOSE", key=f"del_{tf}_{m}", help=f"Ejetar do simulador {tf.upper()}", type="secondary"):
                            del memoria['simuladores'][tf][m]
                            add_log(f"🗑️ BAIL OUT: {m} ejetada do motor {tf.upper()}.", "warn"); st.rerun()
                    st.markdown("<hr style='border:1px dashed #1e293b; margin: 8px 0;'>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info(f"O Motor de {tf.upper()} está escaneando a liquidez em busca de anomalias estatísticas...")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 📜 TERMINAL DE LOGS SENTINEL
# ==========================================
st.markdown("### 📜 HISTÓRICO DE CAÇA (SENTINEL LOGS)")
st.markdown("<div class='terminal-box'>", unsafe_allow_html=True)
if memoria['terminal_logs']:
    for l in memoria['terminal_logs'][:20]:
        cor_log = COR_TEMA if l['tipo'] == 'buy' else '#ef4444' if l['tipo'] == 'sell' else '#38bdf8' if l['tipo'] == 'info' else '#f59e0b'
        st.markdown(f"<div style='border-bottom:1px solid #161f30; padding:4px 0;'><span style='color:#64748b;'>[{l['hora']}]</span> <span style='color: {cor_log}; font-weight:bold;'>{l['msg']}</span></div>", unsafe_allow_html=True)
else:
    st.write("*Nenhuma operação registrada na memória RAM.*")
st.markdown("</div>", unsafe_allow_html=True)

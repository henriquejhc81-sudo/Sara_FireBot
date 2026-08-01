import streamlit as st
import pandas as pd
import ccxt
import pytz
import time
import threading
import random
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ==========================================
# ⚡ MULTIVERSE SCANNER: LIONBOT OMNICORE V8.2
# ARQUITETURA LOCAL (NO DB / NO AI / PURE MATH)
# ==========================================
st.set_page_config(page_title="LionBot Multiverse", page_icon="🦁", layout="wide", initial_sidebar_state="collapsed")
tz_br = pytz.timezone('America/Sao_Paulo')
COR_TEMA = "#00ffcc" # Verde Neon LionBot

# ==========================================
# 1. ESTILIZAÇÃO CSS (MINIMALISTA E INSTITUCIONAL)
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    .stApp {{ background-color: #0b0f19; color: #f8fafc; font-family: 'Inter', sans-serif; }}
    .block-container {{ padding-top: 1.5rem; max-width: 98%; }} 
    [data-testid="stHeader"] {{ display: none; }}
    
    .panel-box {{ background: linear-gradient(145deg, #161f30 0%, #0b0f19 100%); border: 1px solid #1e293b; border-radius: 6px; padding: 15px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5); }}
    .panel-header {{ font-size: 13px; font-family: 'JetBrains Mono', monospace; color: {COR_TEMA}; text-transform: uppercase; font-weight: 700; border-bottom: 1px solid #1e293b; padding-bottom: 10px; margin-bottom: 15px; letter-spacing: 1px; display: flex; justify-content: space-between; align-items: center; }}
    
    div[data-testid="stButton"] > button {{ border-radius: 4px !important; font-weight: 600 !important; font-family: 'Inter', sans-serif !important; padding: 0.2rem 0.5rem !important; transition: all 0.3s ease !important; font-size: 10px !important; border: 1px solid transparent !important; height: 28px; }}
    div[data-testid="stButton"] > button[kind="secondary"] {{ background-color: #0f172a !important; color: #94a3b8 !important; border: 1px solid #1e293b !important; }}
    div[data-testid="stButton"] > button[kind="secondary"]:hover {{ border-color: #ef4444 !important; color: #ef4444 !important; background-color: #1e1b2e !important; box-shadow: 0 0 10px rgba(239, 68, 68, 0.2) !important; }}
    
    .empty-state {{ text-align: center; padding: 25px; color: #475569; font-size: 12px; font-family: 'Inter', sans-serif; letter-spacing: 0.5px; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MEMÓRIA LOCAL RAM (AUTO-START)
# ==========================================
ALVOS_GLOBAIS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT', 'LINK/USDT', 'AVAX/USDT', 'NEAR/USDT', 'SUI/USDT']
TIMEFRAMES = ['2h', '4h', '6h', '12h']

@st.cache_resource
def carregar_memoria():
    return {
        'bot_ativo': True, # 🔥 Robô já liga alimentado e rodando
        'simuladores': {tf: {} for tf in TIMEFRAMES}, 
        'mercado_atual': {}, 
        'ultima_att': "Iniciando varredura histórica..."
    }
memoria = carregar_memoria()

# ==========================================
# 3. GHOST POOL (LEITURA ANTI-BAN)
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
    return []

# ==========================================
# 4. MATRIZ DE RISCO MULTI-TIME (PURA MATEMÁTICA)
# ==========================================
def analise_matriz_risco(simbolo, timeframe):
    try:
        # Puxa 100 velas passadas para "ler as horas passadas" assim que liga
        velas = obter_dados_ghost(simbolo, timeframe, 100)
        if not velas: return 0, 0.0, 0.0, 0.0, 0.0, 0.0
        
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
        preco = float(df['close'].iloc[-1])
        
        dist_ema = ((preco / ema_20) - 1) * 100
        stop_loss_sugerido = -0.025 # -2.5% Padrão
        alvo_surf = 0.0075 # +0.75% Padrão
        
        score_base = 50
        if rsi < 35: score_base += 30
        elif rsi > 70: score_base -= 40
        if -1.0 <= dist_ema <= 0.5: score_base += 15
        
        score_final = max(0, min(99, score_base))
            
        return score_final, preco, stop_loss_sugerido, alvo_surf, rsi, dist_ema
    except Exception as e:
        return 0, 0.0, 0.0, 0.0, 0.0, 0.0

# ==========================================
# 5. THREAD CONTÍNUA (4 MOTORES DE SIMULAÇÃO)
# ==========================================
@st.cache_resource
def iniciar_motores_sentinel():
    def loop_operacional():
        while True:
            if not memoria['bot_ativo']: 
                time.sleep(2); continue
                
            try:
                agora = datetime.now(tz_br); ts_agora = time.time()
                
                # Leitura Global do Preço Atual
                try:
                    for p, d in pool_exchanges[0].fetch_tickers(ALVOS_GLOBAIS).items():
                        if d['last']: memoria['mercado_atual'][p] = float(d['last'])
                except: pass

                # Varrimento da Matriz nos 4 Tempos Gráficos
                for tf in TIMEFRAMES:
                    for m in ALVOS_GLOBAIS:
                        score_final, preco_atual, stop_dyn, alvo_dyn, rsi, dist_ema = analise_matriz_risco(m, tf)
                        
                        # Gatilho de Entrada Puramente Matemático (Score >= 80)
                        if score_final >= 80 and m not in memoria['simuladores'][tf]:
                            memoria['simuladores'][tf][m] = [{
                                'qtd': (1000) / preco_atual, # Tamanho fictício apenas para rastreio de variação
                                'pm': preco_atual, 
                                'pico_preco': preco_atual,
                                'fundo_preco': preco_atual,
                                'stop_dyn': stop_dyn, 
                                'alvo_dyn': alvo_dyn, 
                                'rsi_entrada': rsi,
                                'ema_entrada': dist_ema,
                                'sinal_enviado': False,
                                'ts_compra': ts_agora
                            }]
                            
                # Gerenciamento de PNL e Máximas
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
                            
                            gatilho_entrada = -0.010 # -1.0% para confirmar a reversão
                            
                            if pnl_atual <= gatilho_entrada and not g['sinal_enviado']:
                                g['sinal_enviado'] = True
                                
                            surf_armar = g['alvo_dyn']
                            stop_loss = g['stop_dyn']
                            surf_recuo_fixo = -0.0025
                            
                            vender = False
                            if g['sinal_enviado']:
                                if pnl_do_pico >= surf_armar and queda_do_topo <= surf_recuo_fixo and pnl_atual > 0: 
                                    vender = True # Win
                                elif pnl_atual <= stop_loss: 
                                    vender = True # Stop
                            
                            if vender:
                                g_rem.append(g)
                                
                        for g in g_rem: grids.remove(g)
                        if not grids: del memoria['simuladores'][tf][m]

                memoria['ultima_att'] = agora.strftime('%H:%M:%S')

            except Exception: pass
            time.sleep(10) # Loop extremamente rápido e otimizado
            
    threading.Thread(target=loop_operacional, daemon=True).start()

iniciar_motores_sentinel()

# Refresh veloz para a UI acompanhar os cálculos quase em tempo real
st_autorefresh(interval=4000, key="auto_multiverse")

# ==========================================
# 6. INTERFACE VISUAL (MULTIVERSE PANELS)
# ==========================================

for tf in TIMEFRAMES:
    st.markdown(f"""
    <div class='panel-box'>
        <div class='panel-header'>
            <span>🚀 MOTOR {tf.upper()} - MULTIVERSE SCANNER</span>
            <span style='color:#64748b; font-size:10px; font-family:"Inter", sans-serif; font-weight:normal;'>Última Varrida: {memoria['ultima_att']}</span>
        </div>
    """, unsafe_allow_html=True)
    
    if memoria['simuladores'][tf]:
        st.markdown("<div style='padding: 0 5px;'>", unsafe_allow_html=True)
        hc1, hc2, hc3, hc4, hc5, hc6, hc7 = st.columns([1.5, 1.2, 1.3, 1.4, 1.4, 1.4, 0.8])
        with hc1: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Asset</span>", unsafe_allow_html=True)
        with hc2: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Gatilho / RSI</span>", unsafe_allow_html=True)
        with hc3: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Alvos (Limites)</span>", unsafe_allow_html=True)
        with hc4: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>PM / Current</span>", unsafe_allow_html=True)
        with hc5: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Max High / Low</span>", unsafe_allow_html=True)
        with hc6: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Floating PNL</span>", unsafe_allow_html=True)
        with hc7: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Action</span>", unsafe_allow_html=True)
        st.markdown("<hr style='border:1px solid #1e293b; margin: 8px 0;'>", unsafe_allow_html=True)

        for m, grids in list(memoria['simuladores'][tf].items()):
            qtd_tot = sum([g['qtd'] for g in grids]); pm_tot = sum([g['qtd']*g['pm'] for g in grids]) / qtd_tot if qtd_tot > 0 else 0
            pr_atual = memoria['mercado_atual'].get(m, pm_tot)
            pico = max([g.get('pico_preco', pm_tot) for g in grids]); fundo = min([g.get('fundo_preco', pm_tot) for g in grids])
            
            m_alta = ((pico - pm_tot) / pm_tot) * 100 if pm_tot > 0 else 0; m_queda = ((fundo - pm_tot) / pm_tot) * 100 if pm_tot > 0 else 0
            pnl_usd = (qtd_tot * pr_atual) - (qtd_tot * pm_tot); pnl_pct = (pnl_usd / (qtd_tot * pm_tot)) * 100 if pm_tot > 0 else 0
            
            gatilho_atual = -1.0
            sinal_enviado = grids[0].get('sinal_enviado', False)
            status_txt = "🟢 ATIVO" if sinal_enviado else "⏳ TRACK"
            
            surf_u = grids[0].get('alvo_dyn', 0.0)
            stop_u = grids[0].get('stop_dyn', 0.0)
            rsi_val = grids[0].get('rsi_entrada', 0.0)
            ema_val = grids[0].get('ema_entrada', 0.0)

            with st.container():
                c1, c2, c3, c4, c5, c6, c7 = st.columns([1.5, 1.2, 1.3, 1.4, 1.4, 1.4, 0.8])
                with c1: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:14px; color:#F8FAFC; font-weight:700; padding-top:4px;'>{m}</div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:12px; font-weight:700; color:{COR_TEMA}; padding-top:2px;'>{gatilho_atual:+.2f}%<br><span style='font-size:10px; color:#94a3b8; font-weight:normal;'>RSI: {rsi_val:.1f} | EMA: {ema_val:+.2f}%</span></div>", unsafe_allow_html=True)
                with c3: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:11px; padding-top:4px;'><span style='color:#10b981;'>+{surf_u*100:.2f}%</span><br><span style='color:#ef4444;'>{stop_u*100:.2f}%</span></div>", unsafe_allow_html=True)
                with c4: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:12px; color:#94a3b8; padding-top:4px;'>${pm_tot:.4f}<br><span style='color:#ffffff;'>${pr_atual:.4f}</span></div>", unsafe_allow_html=True)
                with c5: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:11px; padding-top:4px;'><span style='color:#10b981;'>{m_alta:+.2f}%</span><br><span style='color:#ef4444;'>{m_queda:+.2f}%</span></div>", unsafe_allow_html=True)
                with c6: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:15px; font-weight:700; color:{'#10b981' if pnl_pct >= 0 else '#ef4444'}; padding-top:6px;'>{pnl_pct:+.2f}%</div>", unsafe_allow_html=True)
                with c7:
                    st.markdown("<div style='padding-top:4px;'>", unsafe_allow_html=True)
                    if st.button("✕ DROP", key=f"del_{tf}_{m}", help=f"Ejetar do simulador", type="secondary"):
                        del memoria['simuladores'][tf][m]
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<hr style='border:1px dashed #1e293b; margin: 8px 0;'>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='empty-state'>Nenhuma anomalia matemática detectada no vetor de {tf.upper()}. Escaneando o multiverso...</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

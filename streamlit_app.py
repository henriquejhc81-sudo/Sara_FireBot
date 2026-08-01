import streamlit as st
import pandas as pd
import ccxt
import pytz
import time
import threading
import random
from datetime import datetime

# ==========================================
# ⚡ MULTIVERSE SCANNER: LIONBOT OMNICORE V8.3
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
        if not velas: return 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0.0).ewm(alpha=14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=14, adjust=False).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
        
        # Leitura da Vela Exata do Timeframe (Representa as últimas horas do TF escolhido)
        vela_atual = df.iloc[-1]
        preco_open = float(vela_atual['open'])
        preco_high = float(vela_atual['high'])
        preco_low = float(vela_atual['low'])
        preco_atual = float(vela_atual['close'])
        
        dist_ema = ((preco_atual / ema_20) - 1) * 100
        
        # Cálculo Real de Volatilidade dentro da Janela do Timeframe
        var_alta = (preco_high / preco_open) - 1
        var_queda = (preco_low / preco_open) - 1
        var_atual = (preco_atual / preco_open) - 1
        
        score_base = 50
        if rsi < 35: score_base += 30
        elif rsi > 70: score_base -= 40
        if -1.0 <= dist_ema <= 0.5: score_base += 15
        
        score_final = max(0, min(99, score_base))
            
        return score_final, preco_atual, preco_open, var_alta, var_queda, var_atual, rsi, dist_ema
    except Exception as e:
        return 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

# ==========================================
# 5. THREAD CONTÍNUA (4 MOTORES DE ANÁLISE)
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
                        score_final, preco_atual, preco_open, var_alta, var_queda, var_atual, rsi, dist_ema = analise_matriz_risco(m, tf)
                        
                        # Gatilho de Entrada Puramente Matemático (Score >= 80)
                        if score_final >= 80 and m not in memoria['simuladores'][tf]:
                            memoria['simuladores'][tf][m] = {
                                'ts_compra': ts_agora # Marca apenas a hora que encontrou a anomalia
                            }
                            
                        # Atualiza os dados em tempo real se a moeda estiver na tela
                        if m in memoria['simuladores'][tf]:
                            memoria['simuladores'][tf][m].update({
                                'preco_atual': preco_atual,
                                'preco_open': preco_open,
                                'var_alta': var_alta,
                                'var_queda': var_queda,
                                'var_atual': var_atual,
                                'rsi': rsi,
                                'dist_ema': dist_ema,
                                'score': score_final
                            })

                memoria['ultima_att'] = agora.strftime('%d/%m/%Y %H:%M:%S')

            except Exception: pass
            time.sleep(10) # Loop ultraleve em background
            
    threading.Thread(target=loop_operacional, daemon=True).start()

iniciar_motores_sentinel()

# Refresh veloz nativo para a UI acompanhar os cálculos quase em tempo real
time.sleep(3)

# ==========================================
# 6. INTERFACE VISUAL (MULTIVERSE PANELS)
# ==========================================

# Renderiza os 4 motores de forma empilhada (um embaixo do outro)
for tf in TIMEFRAMES:
    st.markdown(f"""
    <div class='panel-box'>
        <div class='panel-header'>
            <span>🚀 MOTOR QUANTITATIVO {tf.upper()}</span>
            <span style='color:#64748b; font-size:10px; font-family:"Inter", sans-serif; font-weight:normal;'>Última Varrida: {memoria['ultima_att']}</span>
        </div>
    """, unsafe_allow_html=True)
    
    if memoria['simuladores'][tf]:
        st.markdown("<div style='padding: 0 5px;'>", unsafe_allow_html=True)
        # Ajuste nas proporções das colunas (Removido os Limites)
        hc1, hc2, hc3, hc4, hc5, hc6 = st.columns([1.5, 1.8, 1.5, 1.5, 1.5, 0.8])
        
        with hc1: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Asset</span>", unsafe_allow_html=True)
        with hc2: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Fundamentos (Score / RSI)</span>", unsafe_allow_html=True)
        with hc3: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Open / Current Price</span>", unsafe_allow_html=True)
        with hc4: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Volatilidade TF (Max/Min)</span>", unsafe_allow_html=True)
        with hc5: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Variação Atual</span>", unsafe_allow_html=True)
        with hc6: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Action</span>", unsafe_allow_html=True)
        st.markdown("<hr style='border:1px solid #1e293b; margin: 8px 0;'>", unsafe_allow_html=True)

        for m, dados in list(memoria['simuladores'][tf].items()):
            pr_atual = dados.get('preco_atual', 0.0)
            pr_open = dados.get('preco_open', 0.0)
            
            m_alta = dados.get('var_alta', 0.0) * 100
            m_queda = dados.get('var_queda', 0.0) * 100
            var_pct = dados.get('var_atual', 0.0) * 100
            
            rsi_val = dados.get('rsi', 0.0)
            ema_val = dados.get('dist_ema', 0.0)
            score_val = dados.get('score', 0)
            
            # Cálculo de Tempo Ativo na Tela
            duracao_s = time.time() - dados.get('ts_compra', time.time())
            horas_ativas = int(duracao_s // 3600)
            minutos_ativos = int((duracao_s % 3600) // 60)
            tempo_str = f"{horas_ativas}h {minutos_ativos}m"

            with st.container():
                c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.8, 1.5, 1.5, 1.5, 0.8])
                
                with c1: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:14px; color:#F8FAFC; font-weight:700; padding-top:4px;'>{m}<br><span style='font-size:9px; color:#94a3b8; font-weight:normal;'>{tempo_str}</span></div>", unsafe_allow_html=True)
                
                with c2: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:12px; font-weight:700; color:{COR_TEMA}; padding-top:2px;'>Score: {score_val}<br><span style='font-size:10px; color:#94a3b8; font-weight:normal;'>RSI: {rsi_val:.1f} | EMA: {ema_val:+.2f}%</span></div>", unsafe_allow_html=True)
                
                with c3: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:12px; color:#94a3b8; padding-top:4px;'>${pr_open:.4f}<br><span style='color:#ffffff;'>${pr_atual:.4f}</span></div>", unsafe_allow_html=True)
                
                with c4: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:11px; padding-top:4px;'><span style='color:#10b981;'>{m_alta:+.2f}%</span><br><span style='color:#ef4444;'>{m_queda:+.2f}%</span></div>", unsafe_allow_html=True)
                
                with c5: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:15px; font-weight:700; color:{'#10b981' if var_pct >= 0 else '#ef4444'}; padding-top:6px;'>{var_pct:+.2f}%</div>", unsafe_allow_html=True)
                
                with c6:
                    st.markdown("<div style='padding-top:4px;'>", unsafe_allow_html=True)
                    if st.button("✕", key=f"del_{tf}_{m}", help=f"Remover", type="secondary"):
                        del memoria['simuladores'][tf][m]
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                st.markdown("<hr style='border:1px dashed #1e293b; margin: 8px 0;'>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='empty-state'>Nenhuma anomalia matemática detectada no vetor de {tf.upper()}. Escaneando o multiverso...</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.rerun()

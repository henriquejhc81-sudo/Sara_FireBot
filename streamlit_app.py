import streamlit as st
import pandas as pd
import ccxt
import pytz
import time
import threading
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ==========================================
# ⚡ MULTIVERSE SCANNER: LIONBOT OMNICORE V8.5
# ARQUITETURA LOCAL (MOMENTUM + OVERSOLD MATH)
# ==========================================
st.set_page_config(page_title="LionBot Multiverse", page_icon="🦁", layout="wide", initial_sidebar_state="collapsed")
tz_br = pytz.timezone('America/Sao_Paulo')
COR_TEMA = "#00ffcc" 

# ==========================================
# 1. ESTILIZAÇÃO CSS (MINIMALISTA EXTREMA)
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    .stApp {{ background-color: #0b0f19; color: #f8fafc; font-family: 'Inter', sans-serif; }}
    .block-container {{ padding-top: 1.5rem; max-width: 98%; }} 
    [data-testid="stHeader"] {{ display: none; }}
    
    .panel-box {{ background: linear-gradient(145deg, #161f30 0%, #0b0f19 100%); border: 1px solid #1e293b; border-radius: 6px; padding: 15px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5); }}
    .panel-header {{ font-size: 13px; font-family: 'JetBrains Mono', monospace; color: {COR_TEMA}; text-transform: uppercase; font-weight: 700; border-bottom: 1px solid #1e293b; padding-bottom: 10px; margin-bottom: 15px; letter-spacing: 1px; display: flex; justify-content: space-between; align-items: center; }}
    
    div[data-testid="stButton"] > button {{ border-radius: 4px !important; font-weight: 600 !important; font-family: 'Inter', sans-serif !important; padding: 0.2rem 0.5rem !important; transition: all 0.3s ease !important; font-size: 10px !important; border: 1px solid transparent !important; height: 32px; }}
    div[data-testid="stButton"] > button[kind="secondary"] {{ background-color: #0f172a !important; color: #94a3b8 !important; border: 1px solid #1e293b !important; }}
    div[data-testid="stButton"] > button[kind="secondary"]:hover {{ border-color: #ef4444 !important; color: #ef4444 !important; background-color: #1e1b2e !important; box-shadow: 0 0 10px rgba(239, 68, 68, 0.2) !important; }}
    div[data-testid="stButton"] > button[kind="primary"] {{ background: linear-gradient(90deg, #0f766e 0%, #047857 100%) !important; color: #ffffff !important; border-color: {COR_TEMA} !important; }}
    
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
        'bot_ativo': True, 
        'simuladores': {tf: {} for tf in TIMEFRAMES}, 
        'ultima_att': "Iniciando varredura quantitativa..."
    }
memoria = carregar_memoria()

# ==========================================
# 3. LEITURA OTIMIZADA BINANCE
# ==========================================
@st.cache_resource
def iniciar_leitor_publico():
    ex = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    return ex
mercado = iniciar_leitor_publico()

# ==========================================
# 4. MATRIZ DE RISCO MULTI-TIME (NOVA MATEMÁTICA)
# ==========================================
def analise_matriz_risco(simbolo, timeframe):
    try:
        # Puxa 100 velas (Ex: 100 velas de 4H = últimos 16 dias de dados)
        velas = mercado.fetch_ohlcv(simbolo, timeframe, limit=100)
        
        if not velas or len(velas) < 20: return None
        
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Cálculos de Indicadores
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss
        rsi = float(100 - (100 / (1 + rs)).iloc[-1])
        
        ema_20 = float(df['close'].ewm(span=20, adjust=False).mean().iloc[-1])
        
        # LÊ A VELA ATUAL (A variação exata dentro do Timeframe atual)
        vela_atual = df.iloc[-1]
        preco_open = float(vela_atual['open'])
        preco_high = float(vela_atual['high'])
        preco_low = float(vela_atual['low'])
        preco_atual = float(vela_atual['close'])
        
        if preco_open <= 0 or ema_20 <= 0: return None
        
        dist_ema = ((preco_atual / ema_20) - 1) * 100
        
        # Variação Real do Timeframe
        var_alta = ((preco_high / preco_open) - 1) * 100
        var_queda = ((preco_low / preco_open) - 1) * 100
        var_atual = ((preco_atual / preco_open) - 1) * 100
        
        # 🧠 NOVA MATEMÁTICA DE PONTUAÇÃO (SCORE BASE)
        score_base = 40
        
        # 1. Avaliação do RSI (Força)
        if rsi <= 40: 
            score_base += 40 # Oversold (Oportunidade de Rebote)
        elif 55 <= rsi <= 68: 
            score_base += 35 # Momentum (Tendência de Alta Saudável)
        elif rsi > 75: 
            score_base -= 50 # Overbought (Perigo de Queda)
            
        # 2. Avaliação da Média (EMA20)
        if dist_ema < -2.0:
            score_base += 20 # Muito abaixo da média (Puxada elástica)
        elif 0.1 <= dist_ema <= 1.5:
            score_base += 15 # Rompendo a média para cima
            
        score_final = max(0, min(99, int(score_base)))
            
        return score_final, preco_atual, preco_open, var_alta, var_queda, var_atual, rsi, dist_ema
    except Exception:
        return None

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
                agora = datetime.now(tz_br)
                ts_agora = time.time()

                # Varredura em Lote (Super Otimizada)
                for tf in TIMEFRAMES:
                    for m in ALVOS_GLOBAIS:
                        # Respeita o limite de taxa da corretora
                        time.sleep(0.1) 
                        
                        resultado = analise_matriz_risco(m, tf)
                        if resultado is None: continue 
                        
                        score_final, preco_atual, preco_open, var_alta, var_queda, var_atual, rsi, dist_ema = resultado
                        
                        # 🔥 GATILHO: Exibe na tela se a matemática for favorável (Score >= 75)
                        if score_final >= 75 and m not in memoria['simuladores'][tf]:
                            memoria['simuladores'][tf][m] = {
                                'ts_encontrado': ts_agora 
                            }
                            
                        # Atualiza os dados em tempo real se a moeda já estiver no painel
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
            time.sleep(10) # Loop reinicia a cada 10 segundos
            
    threading.Thread(target=loop_operacional, daemon=True).start()

iniciar_motores_sentinel()

# ==========================================
# 6. HEADER MINIMALISTA & CONTROLE
# ==========================================
c_head1, c_head2, c_head3 = st.columns([6, 2, 2])
with c_head1:
    st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:22px; font-weight:900; color:{COR_TEMA}; padding-top:4px;'>LIONBOT MULTIVERSE SCANNER</div>", unsafe_allow_html=True)
with c_head2:
    st.markdown(f"<div style='text-align:right; font-family:\"Inter\", sans-serif; font-size:12px; color:#94a3b8; padding-top:12px;'>Motores em Operação</div>", unsafe_allow_html=True)
with c_head3:
    btn_label = "⏹ HALT MOTORS" if memoria['bot_ativo'] else "▶ ENGAGE OMNICORE"
    btn_type = "secondary" if memoria['bot_ativo'] else "primary"
    if st.button(btn_label, use_container_width=True, type=btn_type): 
        memoria['bot_ativo'] = not memoria['bot_ativo']
        st.rerun()

st.markdown("<hr style='border:1px solid #1e293b; margin: 15px 0 25px 0;'>", unsafe_allow_html=True)

# ==========================================
# 7. INTERFACE VISUAL (PILHA DE MOTORES)
# ==========================================
for tf in TIMEFRAMES:
    st.markdown(f"""
    <div class='panel-box'>
        <div class='panel-header'>
            <span>🚀 MOTOR QUANTITATIVO {tf.upper()}</span>
            <span style='color:#64748b; font-size:10px; font-family:"Inter", sans-serif; font-weight:normal;'>ÚLTIMA VARRIDA: {memoria['ultima_att']}</span>
        </div>
    """, unsafe_allow_html=True)
    
    if memoria['simuladores'][tf]:
        st.markdown("<div style='padding: 0 5px;'>", unsafe_allow_html=True)
        # Grid ajustado matematicamente
        hc1, hc2, hc3, hc4, hc5, hc6 = st.columns([1.5, 2.0, 1.5, 1.5, 1.5, 0.8])
        
        with hc1: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Asset</span>", unsafe_allow_html=True)
        with hc2: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Fundamentos (Score / RSI)</span>", unsafe_allow_html=True)
        with hc3: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Open / Current Price</span>", unsafe_allow_html=True)
        with hc4: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Max High / Low</span>", unsafe_allow_html=True)
        with hc5: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Variação Atual</span>", unsafe_allow_html=True)
        with hc6: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Action</span>", unsafe_allow_html=True)
        st.markdown("<hr style='border:1px solid #1e293b; margin: 8px 0;'>", unsafe_allow_html=True)

        # Ordenar para mostrar os maiores Scores no topo
        moedas_ordenadas = sorted(memoria['simuladores'][tf].items(), key=lambda x: x[1].get('score', 0), reverse=True)

        for m, dados in moedas_ordenadas:
            pr_atual = dados.get('preco_atual', 0.0)
            pr_open = dados.get('preco_open', 0.0)
            
            m_alta = dados.get('var_alta', 0.0)
            m_queda = dados.get('var_queda', 0.0)
            var_pct = dados.get('var_atual', 0.0)
            
            rsi_val = dados.get('rsi', 0.0)
            ema_val = dados.get('dist_ema', 0.0)
            score_val = dados.get('score', 0)
            
            # Cálculo de Tempo Ativo na Tela
            duracao_s = time.time() - dados.get('ts_encontrado', time.time())
            horas_ativas = int(duracao_s // 3600)
            minutos_ativos = int((duracao_s % 3600) // 60)
            tempo_str = f"Detectado há: {horas_ativas}h {minutos_ativos}m"

            with st.container():
                c1, c2, c3, c4, c5, c6 = st.columns([1.5, 2.0, 1.5, 1.5, 1.5, 0.8])
                
                with c1: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:14px; color:#F8FAFC; font-weight:700; padding-top:4px;'>{m}<br><span style='font-size:9px; color:#94a3b8; font-weight:normal;'>{tempo_str}</span></div>", unsafe_allow_html=True)
                
                with c2: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:12px; font-weight:700; color:{COR_TEMA}; padding-top:2px;'>Score: {score_val}/100<br><span style='font-size:10px; color:#94a3b8; font-weight:normal;'>RSI: {rsi_val:.1f} | EMA: {ema_val:+.2f}%</span></div>", unsafe_allow_html=True)
                
                with c3: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:12px; color:#94a3b8; padding-top:4px;'>${pr_open:.4f}<br><span style='color:#ffffff;'>${pr_atual:.4f}</span></div>", unsafe_allow_html=True)
                
                with c4: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:11px; padding-top:4px;'><span style='color:#10b981;'>{m_alta:+.2f}%</span><br><span style='color:#ef4444;'>{m_queda:+.2f}%</span></div>", unsafe_allow_html=True)
                
                with c5: st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:15px; font-weight:700; color:{'#10b981' if var_pct >= 0 else '#ef4444'}; padding-top:8px;'>{var_pct:+.2f}%</div>", unsafe_allow_html=True)
                
                with c6:
                    st.markdown("<div style='padding-top:4px;'>", unsafe_allow_html=True)
                    if st.button("✕ DROP", key=f"del_{tf}_{m}", help=f"Remover da tela", type="secondary"):
                        del memoria['simuladores'][tf][m]
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                st.markdown("<hr style='border:1px dashed #1e293b; margin: 8px 0;'>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='empty-state'>Nenhuma anomalia de volatilidade detectada no vetor de {tf.upper()}. Aguardando alinhamento de mercado...</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Atualização de tela a cada 5 segundos
st_autorefresh(interval=5000, key="auto_multiverse")

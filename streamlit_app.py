import streamlit as st
import pandas as pd
import ccxt
import time
import threading
from datetime import datetime

# ==========================================
# ⚡ MULTIVERSE SCANNER: NEXUS ENGINE V9.0
# ARQUITETURA DE MAPEAMENTO DE VOLATILIDADE EXTREMA
# ==========================================
st.set_page_config(page_title="Nexus Multiverse Scanner", page_icon="🌌", layout="wide", initial_sidebar_state="collapsed")
COR_TEMA = "#00ffcc" 

# ==========================================
# 1. ESTILIZAÇÃO CSS (CYBERPUNK MINIMALISTA)
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    .stApp {{ background-color: #0b0f19; color: #f8fafc; font-family: 'Inter', sans-serif; }}
    .block-container {{ padding-top: 1.5rem; max-width: 98%; }} 
    [data-testid="stHeader"] {{ display: none; }}
    
    .panel-box {{ background: linear-gradient(145deg, #161f30 0%, #0b0f19 100%); border: 1px solid #1e293b; border-radius: 6px; padding: 18px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5); }}
    .panel-header {{ font-size: 14px; font-family: 'JetBrains Mono', monospace; color: {COR_TEMA}; text-transform: uppercase; font-weight: 700; border-bottom: 1px solid #1e293b; padding-bottom: 12px; margin-bottom: 15px; letter-spacing: 1px; display: flex; justify-content: space-between; align-items: center; }}
    
    div[data-testid="stButton"] > button {{ border-radius: 4px !important; font-weight: 600 !important; font-family: 'Inter', sans-serif !important; padding: 0.2rem 0.5rem !important; transition: all 0.3s ease !important; font-size: 10px !important; border: 1px solid transparent !important; height: 32px; }}
    div[data-testid="stButton"] > button[kind="primary"] {{ background: linear-gradient(90deg, #0f766e 0%, #047857 100%) !important; color: #ffffff !important; border-color: {COR_TEMA} !important; }}
    div[data-testid="stButton"] > button[kind="secondary"] {{ background-color: #0f172a !important; color: #94a3b8 !important; border: 1px solid #1e293b !important; }}
    div[data-testid="stButton"] > button[kind="secondary"]:hover {{ border-color: #ef4444 !important; color: #ef4444 !important; background-color: #1e1b2e !important; box-shadow: 0 0 10px rgba(239, 68, 68, 0.2) !important; }}
    
    .tag-momentum {{ background-color: rgba(16, 185, 129, 0.15); color: #10b981; padding: 3px 8px; border-radius: 3px; font-size: 10px; font-weight: bold; border: 1px solid #10b981; display: inline-block; }}
    .tag-oversold {{ background-color: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 3px 8px; border-radius: 3px; font-size: 10px; font-weight: bold; border: 1px solid #38bdf8; display: inline-block; }}
    .tag-danger {{ background-color: rgba(239, 68, 68, 0.15); color: #ef4444; padding: 3px 8px; border-radius: 3px; font-size: 10px; font-weight: bold; border: 1px solid #ef4444; display: inline-block; }}
    .tag-neutral {{ background-color: rgba(148, 163, 184, 0.1); color: #94a3b8; padding: 3px 8px; border-radius: 3px; font-size: 10px; font-weight: bold; border: 1px solid #334155; display: inline-block; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONFIGURAÇÃO DE ALVOS E MEMÓRIA
# ==========================================
ALVOS_GLOBAIS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT', 'LINK/USDT', 'AVAX/USDT', 'NEAR/USDT', 'SUI/USDT']
TIMEFRAMES = ['2h', '4h', '6h', '12h']

@st.cache_resource
def carregar_memoria():
    return {
        'motor_rodando': True, 
        'dados_scaneados': {tf: [] for tf in TIMEFRAMES}, 
        'ultima_varredura': "Inicializando matriz de dados..."
    }
memoria = carregar_memoria()

# Conexão Segura e Otimizada com Binance
@st.cache_resource
def iniciar_leitor_publico():
    return ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
exchange = iniciar_leitor_publico()

# ==========================================
# 3. NÚCLEO MATEMÁTICO (NEXUS ENGINE)
# ==========================================
def calcular_metricas_vela(simbolo, timeframe):
    try:
        # Puxa 40 velas para garantir precisão no cálculo da EMA e RSI
        velas = exchange.fetch_ohlcv(simbolo, timeframe, limit=40)
        if not velas or len(velas) < 20: return None
        
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Cálculos de Força Relativa (RSI 14)
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss
        rsi = float(100 - (100 / (1 + rs)).iloc[-1])
        
        # Cálculo de Distanciamento de Média (EMA 20)
        ema_20 = float(df['close'].ewm(span=20, adjust=False).mean().iloc[-1])
        
        # Dados exatos da vela atual (em andamento)
        vela_atual = df.iloc[-1]
        preco_open = float(vela_atual['open'])
        preco_high = float(vela_atual['high'])
        preco_low = float(vela_atual['low'])
        preco_atual = float(vela_atual['close'])
        
        if preco_open <= 0 or ema_20 <= 0: return None
        
        dist_ema = ((preco_atual / ema_20) - 1) * 100
        
        # Volatilidade Real do Timeframe (%)
        var_alta = ((preco_high / preco_open) - 1) * 100
        var_queda = ((preco_low / preco_open) - 1) * 100
        var_atual = ((preco_atual / preco_open) - 1) * 100
        
        # CLASSIFICADOR SEMÂNTICO DE SINAIS (A INTELIGÊNCIA)
        sinal = "🟡 CONSOLIDAÇÃO"
        classe_css = "tag-neutral"
        
        if rsi < 35:
            sinal = "🟢 OVERSOLD (REBOTE)"
            classe_css = "tag-oversold"
        elif rsi > 70:
            sinal = "🔴 OVERBOUGHT"
            classe_css = "tag-danger"
        elif var_atual < -2.0:
            sinal = "🩸 QUEDA LIVRE"
            classe_css = "tag-danger"
        elif rsi >= 55 and var_atual > 0.5:
            sinal = "🔥 MOMENTUM ALTA"
            classe_css = "tag-momentum"

        return {
            'ativo': simbolo,
            'preco_open': preco_open,
            'preco_atual': preco_atual,
            'var_alta': var_alta,
            'var_queda': var_queda,
            'var_atual': var_atual,
            'rsi': rsi,
            'dist_ema': dist_ema,
            'sinal': sinal,
            'classe_css': classe_css,
            'volatilidade_abs': abs(var_atual) # Usado para rankear as que mais se movem
        }
    except Exception:
        return None

# ==========================================
# 4. THREAD DE VARREDURA INFINITA
# ==========================================
@st.cache_resource
def iniciar_varredura_background():
    def loop_scan():
        while True:
            if not memoria['motor_rodando']: 
                time.sleep(2); continue
                
            try:
                for tf in TIMEFRAMES:
                    resultados_temporarios = []
                    
                    for m in ALVOS_GLOBAIS:
                        time.sleep(0.3) # Respeito estrito ao Rate Limit da Binance
                        dados = calcular_metricas_vela(m, tf)
                        if dados:
                            resultados_temporarios.append(dados)
                            
                    # Ordena do maior movimento para o menor (Absoluto) e pega o TOP 5
                    if resultados_temporarios:
                        resultados_ordenados = sorted(resultados_temporarios, key=lambda x: x['volatilidade_abs'], reverse=True)
                        memoria['dados_scaneados'][tf] = resultados_ordenados[:5] # Sempre mostra os 5 melhores

                memoria['ultima_varredura'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

            except Exception: pass
            time.sleep(15) # Pausa antes de refazer a matriz completa
            
    threading.Thread(target=loop_scan, daemon=True).start()

iniciar_varredura_background()

# ==========================================
# 5. RENDERIZAÇÃO DA INTERFACE UI
# ==========================================
c_head1, c_head2, c_head3 = st.columns([6, 2, 2])
with c_head1:
    st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:24px; font-weight:900; color:{COR_TEMA}; padding-top:4px;'>NEXUS MULTIVERSE SCANNER</div>", unsafe_allow_html=True)
with c_head2:
    st.markdown(f"<div style='text-align:right; font-family:\"Inter\", sans-serif; font-size:12px; color:#94a3b8; padding-top:12px;'>Controle de Motores</div>", unsafe_allow_html=True)
with c_head3:
    btn_label = "⏹ HALT MOTORS" if memoria['motor_rodando'] else "▶ ENGAGE NEXUS"
    btn_type = "secondary" if memoria['motor_rodando'] else "primary"
    if st.button(btn_label, use_container_width=True, type=btn_type): 
        memoria['motor_rodando'] = not memoria['motor_rodando']
        st.rerun()

st.markdown("<hr style='border:1px solid #1e293b; margin: 10px 0 25px 0;'>", unsafe_allow_html=True)

# Renderiza os 4 painéis de tempo gráfico
for tf in TIMEFRAMES:
    st.markdown(f"""
    <div class='panel-box'>
        <div class='panel-header'>
            <span>🚀 VETOR QUANTITATIVO {tf.upper()}</span>
            <span style='color:#64748b; font-size:10px; font-family:"Inter", sans-serif; font-weight:normal;'>Sincronização: {memoria['ultima_varredura']}</span>
        </div>
    """, unsafe_allow_html=True)
    
    dados_tf = memoria['dados_scaneados'][tf]
    
    if dados_tf:
        st.markdown("<div style='padding: 0 5px;'>", unsafe_allow_html=True)
        hc1, hc2, hc3, hc4, hc5 = st.columns([1.5, 2.0, 1.8, 1.5, 1.5])
        
        with hc1: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Asset</span>", unsafe_allow_html=True)
        with hc2: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Algorithmic Signal</span>", unsafe_allow_html=True)
        with hc3: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Open / Current Price</span>", unsafe_allow_html=True)
        with hc4: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Max High / Low</span>", unsafe_allow_html=True)
        with hc5: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Variação Atual</span>", unsafe_allow_html=True)
        st.markdown("<hr style='border:1px solid #1e293b; margin: 8px 0;'>", unsafe_allow_html=True)

        for d in dados_tf:
            m = d['ativo']
            pr_open = d['preco_open']
            pr_atual = d['preco_atual']
            m_alta = d['var_alta']
            m_queda = d['var_queda']
            var_pct = d['var_atual']
            rsi_val = d['rsi']
            ema_val = d['dist_ema']

            with st.container():
                c1, c2, c3, c4, c5 = st.columns([1.5, 2.0, 1.8, 1.5, 1.5])
                
                with c1: 
                    st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:15px; color:#F8FAFC; font-weight:700; padding-top:4px;'>{m.replace('/USDT', '')}</div>", unsafe_allow_html=True)
                
                with c2: 
                    st.markdown(f"<div style='padding-top:4px;'><span class='{d['classe_css']}'>{d['sinal']}</span><br><span style='font-size:10px; color:#94a3b8; font-family:\"JetBrains Mono\", monospace;'>RSI: {rsi_val:.1f} | EMA: {ema_val:+.2f}%</span></div>", unsafe_allow_html=True)
                
                with c3: 
                    st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:13px; color:#94a3b8; padding-top:4px;'>${pr_open:.4f}<br><span style='color:#ffffff;'>${pr_atual:.4f}</span></div>", unsafe_allow_html=True)
                
                with c4: 
                    st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:12px; padding-top:4px;'><span style='color:#10b981;'>{m_alta:+.2f}%</span><br><span style='color:#ef4444;'>{m_queda:+.2f}%</span></div>", unsafe_allow_html=True)
                
                with c5: 
                    st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:16px; font-weight:700; color:{'#10b981' if var_pct >= 0 else '#ef4444'}; padding-top:8px;'>{var_pct:+.2f}%</div>", unsafe_allow_html=True)
                    
                st.markdown("<hr style='border:1px dashed #1e293b; margin: 8px 0;'>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='empty-state'>Iniciando cálculos matriziais para o vetor {tf.upper()}...</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Loop de atualização visual sem estourar a API
time.sleep(8)
st.rerun()

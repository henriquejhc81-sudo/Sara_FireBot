import streamlit as st
import pandas as pd
import ccxt
import time
import threading
from datetime import datetime

# ==========================================
# ⚡ MULTIVERSE SCANNER: NEXUS ENGINE V9.1
# ARQUITETURA DE MAPEAMENTO E CORREÇÃO DE RENDERIZAÇÃO
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
    
    .panel-box {{ 
        background: linear-gradient(145deg, #161f30 0%, #0b0f19 100%); 
        border: 1px solid #1e293b; 
        border-radius: 6px; 
        padding: 18px; 
        margin-bottom: 15px; 
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5); 
    }}
    .panel-header {{ 
        font-size: 14px; 
        font-family: 'JetBrains Mono', monospace; 
        color: {COR_TEMA}; 
        text-transform: uppercase; 
        font-weight: 700; 
        letter-spacing: 1px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
    }}
    
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
        'ultima_varredura': "Aguardando sincronização inicial..."
    }
memoria = carregar_memoria()

@st.cache_resource
def iniciar_leitor_publico():
    return ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
exchange = iniciar_leitor_publico()

# ==========================================
# 3. NÚCLEO MATEMÁTICO (NEXUS ENGINE)
# ==========================================
def calcular_metricas_vela(simbolo, timeframe):
    try:
        velas = exchange.fetch_ohlcv(simbolo, timeframe, limit=40)
        if not velas or len(velas) < 20: return None
        
        # Força os tipos de dados como numéricos (Evita crash silencioso no Pandas)
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = df.astype({'open': float, 'high': float, 'low': float, 'close': float, 'volume': float})
        
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss
        rsi = float(100 - (100 / (1 + rs)).iloc[-1])
        
        ema_20 = float(df['close'].ewm(span=20, adjust=False).mean().iloc[-1])
        
        vela_atual = df.iloc[-1]
        preco_open = float(vela_atual['open'])
        preco_high = float(vela_atual['high'])
        preco_low = float(vela_atual['low'])
        preco_atual = float(vela_atual['close'])
        
        if preco_open <= 0 or ema_20 <= 0: return None
        
        dist_ema = ((preco_atual / ema_20) - 1) * 100
        
        var_alta = ((preco_high / preco_open) - 1) * 100
        var_queda = ((preco_low / preco_open) - 1) * 100
        var_atual = ((preco_atual / preco_open) - 1) * 100
        
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
            'volatilidade_abs': abs(var_atual)
        }
    except Exception as e:
        # Agora o erro vai aparecer no terminal onde você rodou o streamlit run
        print(f"[NEXUS ENGINE ERRO] Falha ao calcular {simbolo} no TF {timeframe}: {e}")
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
                        time.sleep(0.3)
                        dados = calcular_metricas_vela(m, tf)
                        if dados:
                            resultados_temporarios.append(dados)
                            
                    if resultados_temporarios:
                        resultados_ordenados = sorted(resultados_temporarios, key=lambda x: x['volatilidade_abs'], reverse=True)
                        memoria['dados_scaneados'][tf] = resultados_ordenados[:5]

                memoria['ultima_varredura'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

            except Exception as loop_error:
                print(f"[NEXUS ENGINE ERRO NO LOOP] {loop_error}")
                pass
            
            time.sleep(15) 
            
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

# Renderiza os 4 painéis de tempo gráfico sem quebrar tags HTML
for tf in TIMEFRAMES:
    st.markdown(f"""
    <div class='panel-box' style='padding-bottom: 8px;'>
        <div class='panel-header' style='border-bottom: none; margin-bottom: 0; padding-bottom: 0;'>
            <span>🚀 VETOR QUANTITATIVO {tf.upper()}</span>
            <span style='color:#64748b; font-size:10px; font-family:"Inter", sans-serif; font-weight:normal;'>Sincronização: {memoria['ultima_varredura']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    dados_tf = memoria['dados_scaneados'][tf]
    
    if dados_tf:
        hc1, hc2, hc3, hc4, hc5 = st.columns([1.5, 2.0, 1.8, 1.5, 1.5])
        with hc1: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Asset</span>", unsafe_allow_html=True)
        with hc2: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Algorithmic Signal</span>", unsafe_allow_html=True)
        with hc3: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Open / Current Price</span>", unsafe_allow_html=True)
        with hc4: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Max High / Low</span>", unsafe_allow_html=True)
        with hc5: st.markdown("<span style='color:#94a3b8; font-size:10px; font-weight:700; text-transform:uppercase;'>Variação Atual</span>", unsafe_allow_html=True)
        st.markdown("<hr style='border:1px solid #1e293b; margin: 8px 0;'>", unsafe_allow_html=True)

        for d in dados_tf:
            c1, c2, c3, c4, c5 = st.columns([1.5, 2.0, 1.8, 1.5, 1.5])
            with c1: 
                st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:15px; color:#F8FAFC; font-weight:700; padding-top:4px;'>{d['ativo'].replace('/USDT', '')}</div>", unsafe_allow_html=True)
            with c2: 
                st.markdown(f"<div style='padding-top:4px;'><span class='{d['classe_css']}'>{d['sinal']}</span><br><span style='font-size:10px; color:#94a3b8; font-family:\"JetBrains Mono\", monospace;'>RSI: {d['rsi']:.1f} | EMA: {d['dist_ema']:+.2f}%</span></div>", unsafe_allow_html=True)
            with c3: 
                st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:13px; color:#94a3b8; padding-top:4px;'>${d['preco_open']:.4f}<br><span style='color:#ffffff;'>${d['preco_atual']:.4f}</span></div>", unsafe_allow_html=True)
            with c4: 
                st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:12px; padding-top:4px;'><span style='color:#10b981;'>{d['var_alta']:+.2f}%</span><br><span style='color:#ef4444;'>{d['var_queda']:+.2f}%</span></div>", unsafe_allow_html=True)
            with c5: 
                st.markdown(f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:16px; font-weight:700; color:{'#10b981' if d['var_atual'] >= 0 else '#ef4444'}; padding-top:8px;'>{d['var_atual']:+.2f}%</div>", unsafe_allow_html=True)
                
            st.markdown("<hr style='border:1px dashed #1e293b; margin: 8px 0;'>", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='panel-box' style='text-align: center; color: #94a3b8; margin-top: -10px; border-top: none;'>
            Iniciando cálculos matriziais para o vetor {tf.upper()}...
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)

# Loop de atualização visual
time.sleep(8)
st.rerun()

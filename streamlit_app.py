import streamlit as st
import pandas as pd
import ccxt
import pytz
from datetime import datetime

# ==========================================
# ⚡ MEGA ROBÔ: AUTOBOLT OMNICORE v3.0 (B2C + MOTOR INTEGRADO)
# ==========================================
st.set_page_config(
    page_title="AUTOBOLT OS // INSTITUCIONAL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

tz_br = pytz.timezone('America/Sao_Paulo')

# ==========================================
# 1. ESTILIZAÇÃO CSS PREMIUM (DARK MODE + B2C)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; font-family: 'Inter', sans-serif; }
    .header-box {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    .titulo { color: #ffffff; font-weight: 900; font-family: 'Inter', sans-serif; margin: 0; letter-spacing: 1px; text-transform: uppercase; }
    .subtitulo { color: #94a3b8; font-family: 'Inter', monospace; margin-top: 5px; font-size: 13px; }
    .disclaimer { text-align: center; color: #475569; font-size: 11px; margin-top: 40px; font-family: monospace; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOTOR DE ANÁLISE INTEGRADO (CCXT)
# ==========================================
@st.cache_resource
def iniciar_exchange():
    return ccxt.kucoin({'enableRateLimit': True})

exchange = iniciar_exchange()

def calcular_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def classificar_ativo(simbolo):
    if simbolo in ['BTC/USDT', 'ETH/USDT']:
        return 'Alta Liquidez', 75, 1.025  
    elif simbolo in ['AVAX/USDT', 'NEAR/USDT', 'SUI/USDT']:
        return 'Alta Vol.', 85, 1.050      
    else:
        return 'Média Vol.', 80, 1.035     

def analise_autobolt(simbolo):
    try:
        grupo, limite_rsi, limite_ema = classificar_ativo(simbolo)
        
        velas_4h = exchange.fetch_ohlcv(simbolo, '4h', limit=200)
        velas_15m = exchange.fetch_ohlcv(simbolo, '15m', limit=100)
        
        df_4h = pd.DataFrame(velas_4h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_15m = pd.DataFrame(velas_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        df_15m['RSI'] = calcular_rsi(df_15m['close'], 14)
        df_15m['EMA_20'] = df_15m['close'].ewm(span=20, adjust=False).mean()
        df_4h['EMA_200'] = df_4h['close'].ewm(span=200, adjust=False).mean()
        
        atual = df_15m.iloc[-1]
        macro_atual = df_4h.iloc[-1]
        
        preco = atual['close']
        rsi = atual['RSI']
        ema_20 = atual['EMA_20']
        ema_200_macro = macro_atual['EMA_200']
        
        status = "ALTA PROBABILIDADE"
        motivo = "Tendência de Alta & Sem Exaustão Confirmada"
        confianca = 85
        
        # 3 Travas do Autobolt traduzidas para o B2C
        if pd.isna(rsi) or pd.isna(ema_20):
            status = "OBSERVAÇÃO"
            motivo = "Aguardando volume histórico"
            confianca = 0
            
        elif preco < ema_200_macro:
            status = "MÉDIA PROBABILIDADE"
            motivo = "Bloqueio Macro: Tendência de Baixa no Gráfico 4h"
            confianca = 25
            
        elif rsi >= limite_rsi:
            status = "RISCO DE TOPO"
            motivo = f"Quarentena: RSI Micro >= {limite_rsi} (Exaustão)"
            confianca = 40
            
        elif preco > (ema_20 * limite_ema): 
            status = "RISCO DE TOPO"
            motivo = f"Quarentena: Preço esticado (> {(limite_ema - 1)*100:.1f}% da EMA)"
            confianca = 45

        # Bônus de confiança se a distância da EMA for ideal para compra (Pullback)
        distancia_ema = ((preco / ema_20) - 1) * 100
        if status == "ALTA PROBABILIDADE" and -1.0 <= distancia_ema <= 0.5:
            confianca += 10
            motivo += " | Pullback ideal na EMA 20"

        confianca = min(99, confianca)

        return {
            "Ativo": simbolo.replace('/USDT', ''),
            "Preço Atual": f"${preco:.4f}",
            "Índice de Confiança (%)": confianca,
            "Veredicto do Algoritmo": status,
            "Justificativa Base": motivo,
            "_raw_status": status # Usado para os KPIs
        }
        
    except Exception as e:
        return {
            "Ativo": simbolo.replace('/USDT', ''),
            "Preço Atual": "ERRO API",
            "Índice de Confiança (%)": 0,
            "Veredicto do Algoritmo": "FALHA DE CONEXÃO",
            "Justificativa Base": "Erro de conexão com corretora",
            "_raw_status": "FALHA"
        }

@st.cache_data(ttl=120) 
def varredura_global():
    esquadrao = [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 
        'DOT/USDT', 'LINK/USDT', 'AVAX/USDT', 'NEAR/USDT', 'SUI/USDT'
    ]
    return [analise_autobolt(moeda) for moeda in esquadrao], datetime.now(tz_br).strftime('%d/%m/%Y %H:%M:%S')

# ==========================================
# 3. INTERFACE E RENDERIZAÇÃO B2C
# ==========================================
st.markdown("""
    <div class="header-box" translate="no">
        <h1 class="titulo">⚡ AUTOBOLT ENGINE v3.0</h1>
        <div class="subtitulo">SISTEMA AUTÔNOMO DE PROTEÇÃO CONTRA TOPOS // MULTI-TIMEFRAME ALGORITHM</div>
    </div>
""", unsafe_allow_html=True)

col_btn, col_espaco = st.columns([1, 4])
with col_btn:
    if st.button("🔄 FORÇAR VARREDURA DA IA", use_container_width=True):
        st.cache_data.clear() 

with st.spinner("Autobolt mapeando fractais de 4h e 15m na KuCoin..."):
    dados_mercado, ultima_att = varredura_global()
    df = pd.DataFrame(dados_mercado)

# KPIs Institucionais
st.write("---")
col1, col2, col3, col4 = st.columns(4)

liberados = len(df[df['_raw_status'] == 'ALTA PROBABILIDADE']) if not df.empty else 0
quarentena = len(df[df['_raw_status'] == 'RISCO DE TOPO']) if not df.empty else 0
bloqueados = len(df[df['_raw_status'] == 'MÉDIA PROBABILIDADE']) if not df.empty else 0

with col1: st.metric("Ativos Varridos", len(df))
with col2: st.metric("Oportunidades (Alta Probabilidade)", liberados)
with col3: st.metric("Risco de Topo (Quarentena)", quarentena)
with col4: st.metric("Queda Macro (Bloqueados)", bloqueados)

st.write("---")
st.markdown(f"### 📡 MATRIX DE DECISÃO AUTÔNOMA <span style='font-size:12px; color:#64748b; float:right;'>Última Sincronização: {ultima_att}</span>", unsafe_allow_html=True)

def aplicar_cores_tabela(row):
    confianca = row['Índice de Confiança (%)']
    if confianca >= 80:
        cor = '#10b981' # Verde
    elif confianca >= 60:
        cor = '#f59e0b' # Amarelo
    elif confianca == 0:
        cor = '#64748b' # Cinza
    else:
        cor = '#ef4444' # Vermelho
        
    estilos = [''] * (len(row) - 1) # Desconsidera a coluna oculta
    idx_confianca = row.index.get_loc('Índice de Confiança (%)')
    idx_veredicto = row.index.get_loc('Veredicto do Algoritmo')
    
    estilos[idx_confianca] = f'color: {cor}; font-weight: bold; font-size: 14px;'
    estilos[idx_veredicto] = f'color: {cor}; font-weight: bold;'
    
    # Adiciona a cor base para as outras colunas para manter o padrão
    for i in range(len(estilos)):
        if i not in [idx_confianca, idx_veredicto]:
            estilos[i] = 'color: #e2e8f0;'
            
    # Retorna os estilos, ignorando a coluna '_raw_status'
    return estilos + ['']

if not df.empty:
    df_exibicao = df.sort_values(by="Índice de Confiança (%)", ascending=False).reset_index(drop=True)
    df_estilizado = df_exibicao.style.apply(aplicar_cores_tabela, axis=1)
    
    st.dataframe(
        df_estilizado,
        use_container_width=True,
        hide_index=True,
        column_config={"_raw_status": None}, # Oculta a coluna usada apenas para lógica dos KPIs
        height=420
    )

st.write("---")
st.markdown("### 🧠 LOG DE PENSAMENTO DA IA")
for index, row in df.iterrows():
    if row['_raw_status'] in ['RISCO DE TOPO', 'MÉDIA PROBABILIDADE']:
        st.caption(f"- **{row['Ativo']}:** Protegido. Motivo: {row['Justificativa Base']}.")

st.markdown("<div class='disclaimer'>AVISO LEGAL: Este sistema fornece análises algorítmicas baseadas em probabilidade matemática e leitura de fractais. Criptomoedas são ativos de risco. O Índice de Confiança não representa garantia de ganhos financeiros. Atue com gerenciamento de risco estruturado.</div>", unsafe_allow_html=True)

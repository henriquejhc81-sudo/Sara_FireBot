import streamlit as st
import pandas as pd
import ccxt
import pytz
import time
import threading
import random
from datetime import datetime

# ==========================================
# ⚡ MEGA ROBÔ: AUTOBOLT OMNICORE v6.0 (ANTI-BAN + TRÍADE DE MOTORES)
# ==========================================
st.set_page_config(page_title="AUTOBOLT OS // TRÍADE", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")
tz_br = pytz.timezone('America/Sao_Paulo')

# ==========================================
# 1. ESTILIZAÇÃO CSS (ALTO CONTRASTE PREMIUM)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #020617; color: #f8fafc; font-family: 'Inter', sans-serif; }
    .header-box { background: linear-gradient(90deg, #0f172a 0%, #020617 100%); padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); }
    .titulo { color: #ffffff; font-weight: 900; margin: 0; letter-spacing: 1px; text-transform: uppercase; }
    .subtitulo { color: #94a3b8; font-family: monospace; margin-top: 5px; font-size: 13px; }
    div[data-testid="stButton"] > button { background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%); color: #ffffff; border: none; border-radius: 6px; font-weight: 800; transition: all 0.3s ease; }
    div[data-testid="stButton"] > button:hover { background: linear-gradient(90deg, #1d4ed8 0%, #1e3a8a 100%); box-shadow: 0 0 10px rgba(59, 130, 246, 0.5); }
    .btn-sniper div[data-testid="stButton"] > button { background: linear-gradient(90deg, #ef4444 0%, #b91c1c 100%) !important; font-size: 11px !important; padding: 2px 10px !important; height: auto !important; min-height: 30px !important; }
    .panel-box { background: #0f172a; border: 1px solid #1e293b; border-radius: 4px; padding: 15px; margin-bottom: 15px; }
    .panel-header { font-size: 12px; color: #e2e8f0; text-transform: uppercase; font-weight: bold; border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-bottom: 12px; letter-spacing: 1px; }
    .styled-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left; }
    .styled-table th { color: #94a3b8; padding: 10px 8px; border-bottom: 1px solid #1e293b; background: #020617; font-weight:bold; text-transform: uppercase; font-size: 0.75rem; }
    .styled-table td { padding: 10px 8px; border-bottom: 1px solid #1e293b; color: #f1f5f9; font-weight: 500; }
    .terminal-box { background: #000000; border: 1px solid #1e293b; padding: 12px; border-radius: 4px; height: 250px; overflow-y: auto; font-size: 0.85rem; font-family: monospace; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 900 !important; font-size: 1.8rem !important; }
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: 600 !important; font-size: 0.8rem !important; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MEMÓRIA & CONFIGURAÇÕES GLOBAIS
# ==========================================
ALVOS_GLOBAIS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT', 'LINK/USDT', 'AVAX/USDT', 'NEAR/USDT', 'SUI/USDT']
TAXA_CORRETORA = 0.001
ALOCACAO_SIMULADA = 0.05
ALOCACAO_REAL = 0.30 # Kelly Criterion para M3 (30% da banca livre por tiro)

@st.cache_resource
def carregar_memoria():
    return {
        'bot_ativo': False, 'caixa_livre_simulado': 10000.00, 'caixa_real': 0.0,
        'lucro_liquido_simulado': 0.0, 'lucro_liquido_real': 0.0,
        'portfolio_m1': {}, 'portfolio_m2': {}, 'portfolio_m3_real': {},
        'matriz_b2c': [], 'terminal_logs': [], 'mercado_atual': {},
        'ultima_att': "Aguardando..."
    }
memoria = carregar_memoria()

# ==========================================
# 3. SOLUÇÃO ANTI-BAN: EXCHANGE ROTATION POOL
# ==========================================
@st.cache_resource
def iniciar_pool_leitura():
    return [
        ccxt.binance({'enableRateLimit': True}),
        ccxt.kucoin({'enableRateLimit': True}),
        ccxt.bybit({'enableRateLimit': True}),
        ccxt.okx({'enableRateLimit': True})
    ]
pool_exchanges = iniciar_pool_leitura()

def obter_dados_seguros(simbolo, timeframe, limit):
    # Rotaciona entre as corretoras para evitar Rate Limit (Ban)
    random.shuffle(pool_exchanges)
    for ex in pool_exchanges:
        try:
            return ex.fetch_ohlcv(simbolo, timeframe, limit=limit)
        except:
            continue
    raise Exception("Falha em todo o Pool de Corretoras.")

def add_log(msg, tipo="info"):
    memoria['terminal_logs'].insert(0, {"hora": datetime.now(tz_br).strftime('%H:%M:%S'), "msg": msg, "tipo": tipo})
    memoria['terminal_logs'] = memoria['terminal_logs'][:40]

# ==========================================
# 4. INTELIGÊNCIA AUTOBOLT & GESTÃO DE RISCO
# ==========================================
def calcular_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def classificar_ativo(simbolo):
    if simbolo in ['BTC/USDT', 'ETH/USDT']: return 'Alta Liquidez', 75, 1.025  
    elif simbolo in ['AVAX/USDT', 'NEAR/USDT', 'SUI/USDT']: return 'Alta Vol.', 85, 1.050      
    else: return 'Média Vol.', 80, 1.035     

def analise_autobolt(simbolo):
    try:
        grupo, limite_rsi, limite_ema = classificar_ativo(simbolo)
        
        # Leitura distribuída na nuvem (Anti-Ban)
        velas_4h = obter_dados_seguros(simbolo, '4h', 200)
        velas_15m = obter_dados_seguros(simbolo, '15m', 100)
        
        df_4h = pd.DataFrame(velas_4h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_15m = pd.DataFrame(velas_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        df_15m['RSI'] = calcular_rsi(df_15m['close'], 14)
        df_15m['EMA_20'] = df_15m['close'].ewm(span=20, adjust=False).mean()
        df_4h['EMA_200'] = df_4h['close'].ewm(span=200, adjust=False).mean()
        
        atual = df_15m.iloc[-1]; macro_atual = df_4h.iloc[-1]
        preco = atual['close']; rsi = atual['RSI']; ema_20 = atual['EMA_20']; ema_200_macro = macro_atual['EMA_200']
        volume_24h_usd = atual['volume'] * preco
        
        # Stop Dinâmico (Gestão de Risco)
        stop_loss_sugerido = preco * 0.975 
        alvo_surf = preco * 1.0075
        
        status = "ALTA PROBABILIDADE"; motivo = "Tendência Confirmada"; confianca = 85
        
        if volume_24h_usd < 100000: 
            status = "BAIXA LIQUIDEZ"; motivo = "Risco de Derrapagem"; confianca = 0
        elif pd.isna(rsi) or pd.isna(ema_20):
            status = "OBSERVAÇÃO"; motivo = "Aguardando volume"; confianca = 0
        elif preco < ema_200_macro:
            status = "MÉDIA PROBABILIDADE"; motivo = "Bloqueio Macro 4h"; confianca = 25
        elif rsi >= limite_rsi:
            status = "RISCO DE TOPO"; motivo = f"Exaustão (RSI {rsi:.0f})"; confianca = 40
        elif preco > (ema_20 * limite_ema): 
            status = "RISCO DE TOPO"; motivo = "Preço esticado da EMA"; confianca = 45

        distancia_ema = ((preco / ema_20) - 1) * 100
        if status == "ALTA PROBABILIDADE" and -1.0 <= distancia_ema <= 0.5:
            confianca += 10; motivo += " | Pullback ideal"

        return {
            "Ativo": simbolo, "Preço": preco, "Confianca": min(99, confianca), 
            "Stop_Loss_Sugerido": stop_loss_sugerido, "Alvo_Sugerido": alvo_surf,
            "Veredicto": status, "Justificativa": motivo
        }
    except Exception as e:
        return {"Ativo": simbolo, "Preço": 0, "Confianca": 0, "Stop_Loss_Sugerido": 0, "Alvo_Sugerido": 0, "Veredicto": "FALHA", "Justificativa": str(e)}

# ==========================================
# 5. CONEXÃO EXECUÇÃO REAL (MOTOR 3)
# ==========================================
def executar_compra_real(moeda, api_key, api_secret, api_pass, dados_analise):
    try:
        ex_real = ccxt.kucoin({'apiKey': api_key, 'secret': api_secret, 'password': api_pass, 'enableRateLimit': True})
        saldo = ex_real.fetch_balance()
        caixa = float(saldo['free'].get('USDT', 0.0))
        
        if caixa < 10:
            add_log(f"⚠️ M3 Sniper: Saldo insuficiente (${caixa:.2f}) para comprar {moeda}.", "warn")
            return False
            
        pr = dados_analise['Preço']
        tamanho_ordem = caixa * ALOCACAO_REAL
        if tamanho_ordem < 5: tamanho_ordem = 5
        
        qtd_alvo = float(ex_real.amount_to_precision(moeda, tamanho_ordem / pr))
        
        # ORDEM REAL
        ex_real.create_market_buy_order(moeda, qtd_alvo)
        
        memoria['portfolio_m3_real'][moeda] = [{
            'qtd': qtd_alvo, 'pm': pr, 'pico_preco': pr, 'stop_dyn': dados_analise['Stop_Loss_Sugerido'], 'alvo': dados_analise['Alvo_Sugerido']
        }]
        add_log(f"⚡ M3 SNIPER EXECUTADO! Ordem REAL de {moeda} enviada a ${pr:.4f}.", "buy")
        return True
    except Exception as e:
        add_log(f"❌ M3 FALHA REAL: {str(e)[:50]}", "sell")
        return False

# ==========================================
# 6. THREAD CONTÍNUA (A TRÍADE EM AÇÃO)
# ==========================================
@st.cache_resource
def iniciar_motores_triade():
    def loop_operacional():
        while True:
            if not memoria['bot_ativo']: time.sleep(2); continue
            try:
                agora = datetime.now(tz_br); ts_agora = time.time(); matriz_temp = []
                
                # Leitura ultra-rápida de preços via Ticker Global (não dá ban)
                for p, d in pool_exchanges[0].fetch_tickers(ALVOS_GLOBAIS).items():
                    if d['last']: memoria['mercado_atual'][p] = float(d['last'])

                for m in ALVOS_GLOBAIS:
                    analise = analise_autobolt(m)
                    pr = analise['Preço']
                    if pr <= 0: continue
                    
                    matriz_temp.append({
                        "Ativo": m.replace('/USDT', ''), "Preço Atual": f"${pr:.4f}", "Índice de Confiança (%)": analise['Confianca'],
                        "Stop-Loss Sugerido": f"${analise['Stop_Loss_Sugerido']:.4f}", "Veredicto do Algoritmo": analise['Veredicto'],
                        "Justificativa Base": analise['Justificativa'], "_raw_status": analise['Veredicto'], "_dados": analise
                    })

                    # --> MÓDULO BATEDOR (M1)
                    if analise['Veredicto'] == "ALTA PROBABILIDADE" and m not in memoria['portfolio_m1'] and m not in memoria['portfolio_m2'] and len(memoria['portfolio_m1']) < 10:
                        memoria['portfolio_m1'][m] = [{'pm': pr, 'pico_preco': pr, 'stop_dyn': analise['Stop_Loss_Sugerido']}]
                        add_log(f"👁️ M1 Rastreando: {m} ({analise['Confianca']}%)", "info")

                memoria['matriz_b2c'] = matriz_temp
                memoria['ultima_att'] = agora.strftime('%d/%m/%Y %H:%M:%S')

                # --> MÓDULO EXECUTOR SIMULADO (M2)
                for m, grids in list(memoria['portfolio_m1'].items()):
                    pr = memoria['mercado_atual'].get(m)
                    if not pr: continue
                    g_rem = []
                    for g in grids:
                        g['pico_preco'] = max(g['pico_preco'], pr)
                        pnl_atual = (pr - g['pm']) / g['pm']
                        
                        # Transfere do M1 para o M2 após confirmar queda técnica de -1%
                        if pnl_atual <= -0.01:
                            memoria['portfolio_m2'][m] = [{'qtd': (1000)/pr, 'pm': pr, 'pico_preco': pr, 'stop_dyn': g['stop_dyn']}]
                            add_log(f"🎯 GATILHO M1 CONFIRMADO! {m} despachado para M2 a ${pr:.4f}!", "buy")
                            g_rem.append(g)
                    for g in g_rem: grids.remove(g)
                    if not grids: del memoria['portfolio_m1'][m]

                # M2 Gerenciamento
                for m, grids in list(memoria['portfolio_m2'].items()):
                    pr = memoria['mercado_atual'].get(m)
                    g_rem = []
                    for g in grids:
                        g['pico_preco'] = max(g['pico_preco'], pr)
                        pnl_atual = (pr - g['pm']) / g['pm']
                        pnl_pico = (g['pico_preco'] - g['pm']) / g['pm']
                        queda_topo = (pr - g['pico_preco']) / g['pico_preco']
                        
                        vender = False; tipo = ""
                        if pnl_pico >= 0.0075 and queda_topo <= -0.0025: vender = True; tipo = "WIN (M2)"
                        elif pr <= g['stop_dyn']: vender = True; tipo = "STOP (M2)"
                        
                        if vender:
                            l = (g['qtd'] * pr) - (g['qtd'] * g['pm'])
                            memoria['lucro_liquido_simulado'] += l
                            add_log(f"💰 {tipo} [{m}]: ${l:+.2f}", "info" if l > 0 else "sell")
                            g_rem.append(g)
                    for g in g_rem: grids.remove(g)
                    if not grids: del memoria['portfolio_m2'][m]

            except Exception as e: add_log(f"⚠️ Erro Loop Tríade: {str(e)[:40]}", "warn")
            time.sleep(15) 
    threading.Thread(target=loop_operacional, daemon=True).start()

iniciar_motores_triade()

# Refresh automático
time.sleep(0.5)
agora = time.time()
if agora - memoria.get('tela_att', 0) > 3:
    memoria['tela_att'] = agora
    st.rerun()

# ==========================================
# 7. INTERFACE DO USUÁRIO
# ==========================================
st.markdown("""
    <div class="header-box" translate="no">
        <h1 class="titulo">⚡ AUTOBOLT OMNICORE v6.0</h1>
        <div class="subtitulo">SISTEMA MULTI-EXCHANGE ANTI-BAN | TRÍADE DE MOTORES (M1 + M2 + M3 SNIPER)</div>
    </div>
""", unsafe_allow_html=True)

with st.expander("🔐 CONFIGURAR MÓDULO M3 (CONEXÃO REAL KUCOIN)", expanded=False):
    st.markdown("<p style='font-size:12px; color:#94a3b8;'>Insira as chaves para habilitar o Motor 3 (Sniper). Isso permitirá que você faça execuções reais com 1 clique.</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: key_api = st.text_input("API Key", type="password", key="kucoin_key")
    with c2: sec_api = st.text_input("Secret Key", type="password", key="kucoin_sec")
    with c3: pass_api = st.text_input("Passphrase", type="password", key="kucoin_pass")

col_btn1, col_btn2, _ = st.columns([1, 1, 3])
with col_btn1:
    btn_label = "🛑 PAUSAR SISTEMA" if memoria['bot_ativo'] else "🚀 INICIAR VARREDURA"
    st.markdown(f"""<style>div[data-testid="stButton"] > button {{ {'background: linear-gradient(90deg, #ef4444 0%, #b91c1c 100%);' if memoria['bot_ativo'] else ''} }}</style>""", unsafe_allow_html=True)
    if st.button(btn_label, use_container_width=True): memoria['bot_ativo'] = not memoria['bot_ativo']; st.rerun()
with col_btn2:
    if st.button("🔄 REFRESH TELA", use_container_width=True): st.rerun()

st.write("---")

# Matriz B2C + Motor 3 (Mesa de Agressão)
st.markdown(f"### 📡 MATRIX DE DECISÃO B2C & MESA SNIPER (M3) <span style='font-size:12px; color:#64748b; float:right;'>Sincronização: {memoria['ultima_att']}</span>", unsafe_allow_html=True)

df = pd.DataFrame(memoria['matriz_b2c'])
if not df.empty:
    df_exibicao = df.sort_values(by="Índice de Confiança (%)", ascending=False).reset_index(drop=True)
    
    # Renderiza a tabela customizada com botões de ação M3
    html_table = "<table class='styled-table'><tr><th>Ação M3</th><th>Ativo</th><th>Preço Atual</th><th>Índice de Confiança (%)</th><th>Veredicto</th><th>Stop-Loss Dyn</th><th>Justificativa</th></tr>"
    for idx, row in df_exibicao.iterrows():
        conf = row['Índice de Confiança (%)']
        cor = '#10b981' if conf >= 80 else '#f59e0b' if conf >= 60 else '#64748b' if conf == 0 else '#ef4444'
        ativo_puro = row['Ativo']
        ativo_ccxt = f"{ativo_puro}/USDT"
        
        # Botão de Agressão Manual (Formulário para não travar o loop do Streamlit)
        btn_html = f"---"
        if conf >= 60:
            btn_html = f"""<div class='btn-sniper'><button onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: '{ativo_ccxt}'}}, '*');">⚡ COMPRAR</button></div>"""

        html_table += f"<tr>"
        
        # Lógica de Botão via Streamlit (usamos colunas na UI original, mas aqui faremos botões reais fora do HTML para segurança)
        html_table += f"<td>"
        # Usamos uma estratégia mista: renderizamos texto, e usaremos st.columns logo abaixo se preferir, ou apenas botões no Streamlit.
        # Para ficar perfeito, vamos usar as colunas do Streamlit para iterar.
        
        pass # Vamos reconstruir em formato de Streamlit Columns nativo para os botões funcionarem

    # RENDERIZAÇÃO NATIVA STREAMLIT PARA OS BOTÕES (MESA SNIPER)
    # Cabeçalho
    st.markdown("<div style='display:flex; border-bottom:1px solid #1e293b; padding-bottom:10px; color:#94a3b8; font-size:12px; font-weight:bold; text-transform:uppercase;'><div style='flex:1;'>Ação Real (M3)</div><div style='flex:1;'>Ativo</div><div style='flex:1;'>Preço</div><div style='flex:1;'>Confiança</div><div style='flex:1.5;'>Veredicto</div><div style='flex:1;'>Stop Dyn</div><div style='flex:2;'>Motivo</div></div>", unsafe_allow_html=True)
    
    for idx, row in df_exibicao.iterrows():
        conf = row['Índice de Confiança (%)']
        cor = '#10b981' if conf >= 80 else '#f59e0b' if conf >= 60 else '#64748b' if conf == 0 else '#ef4444'
        ativo_ccxt = f"{row['Ativo']}/USDT"
        
        c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 1, 1, 1, 1.5, 1, 2])
        with c1:
            if conf >= 60:
                st.markdown("<div class='btn-sniper'>", unsafe_allow_html=True)
                if st.button("⚡ COMPRAR", key=f"btn_{ativo_ccxt}"):
                    if not key_api: st.error("Insira as chaves M3 acima!")
                    else: executar_compra_real(ativo_ccxt, key_api, sec_api, pass_api, row['_dados'])
                st.markdown("</div>", unsafe_allow_html=True)
            else: st.markdown("<span style='color:#475569; font-size:12px;'>Aguardando</span>", unsafe_allow_html=True)
        with c2: st.markdown(f"<b>{row['Ativo']}</b>", unsafe_allow_html=True)
        with c3: st.markdown(f"{row['Preço Atual']}", unsafe_allow_html=True)
        with c4: st.markdown(f"<span style='color:{cor}; font-weight:bold; font-size:16px;'>{conf}%</span>", unsafe_allow_html=True)
        with c5: st.markdown(f"<span style='color:{cor}; font-weight:bold;'>{row['Veredicto do Algoritmo']}</span>", unsafe_allow_html=True)
        with c6: st.markdown(f"<span style='color:#ef4444;'>{row['Stop-Loss Sugerido']}</span>", unsafe_allow_html=True)
        with c7: st.markdown(f"<span style='font-size:12px; color:#cbd5e1;'>{row['Justificativa Base']}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='border: 1px solid #0f172a; margin: 4px 0;'>", unsafe_allow_html=True)

# Painéis dos Motores
st.write("---")
p1, p2, p3 = st.columns([1.5, 1.5, 1.5])
with p1:
    st.markdown("<div class='panel-box' translate='no'><div class='panel-header'>👁️ MOTOR 1 (BATEDOR VIRTUAL)</div>", unsafe_allow_html=True)
    if memoria['portfolio_m1']:
        for m, grids in memoria['portfolio_m1'].items():
            pr = memoria['mercado_atual'].get(m, grids[0]['pm'])
            pnl = ((pr - grids[0]['pm']) / grids[0]['pm']) * 100
            cor = "#10b981" if pnl >= 0 else "#ef4444"
            st.markdown(f"**{m}**: PM ${grids[0]['pm']:.4f} | <span style='color:{cor};'>{pnl:+.2f}%</span>", unsafe_allow_html=True)
    else: st.info("Vazio.")
    st.markdown("</div>", unsafe_allow_html=True)

with p2:
    st.markdown("<div class='panel-box' translate='no'><div class='panel-header'>💼 MOTOR 2 (EXECUTOR VIRTUAL)</div>", unsafe_allow_html=True)
    if memoria['portfolio_m2']:
        for m, grids in memoria['portfolio_m2'].items():
            pr = memoria['mercado_atual'].get(m, grids[0]['pm'])
            pnl = ((pr - grids[0]['pm']) / grids[0]['pm']) * 100
            cor = "#10b981" if pnl >= 0 else "#ef4444"
            st.markdown(f"**{m}**: PM ${grids[0]['pm']:.4f} | <span style='color:{cor};'>{pnl:+.2f}%</span>", unsafe_allow_html=True)
    else: st.info("Vazio.")
    st.markdown("</div>", unsafe_allow_html=True)

with p3:
    st.markdown("<div class='panel-box' translate='no' style='border-color:#ef4444;'><div class='panel-header' style='color:#ef4444;'>🎯 MOTOR 3 (TRADER REAL)</div>", unsafe_allow_html=True)
    if memoria['portfolio_m3_real']:
        for m, grids in memoria['portfolio_m3_real'].items():
            pr = memoria['mercado_atual'].get(m, grids[0]['pm'])
            pnl = ((pr - grids[0]['pm']) / grids[0]['pm']) * 100
            cor = "#10b981" if pnl >= 0 else "#ef4444"
            st.markdown(f"**{m}**: PM ${grids[0]['pm']:.4f} | <span style='color:{cor};'>{pnl:+.2f}%</span><br><span style='font-size:10px;color:#94a3b8;'>Alvo: ${grids[0]['alvo']:.4f} | Stop: ${grids[0]['stop_dyn']:.4f}</span>", unsafe_allow_html=True)
    else: st.info("Nenhuma ordem real aberta pelo M3.")
    st.markdown("</div>", unsafe_allow_html=True)

# Logs
st.markdown("<div class='panel-box' translate='no'><div class='panel-header'>🖥️ TERMINAL DE LOGS DA TRÍADE</div><div class='terminal-box'>", unsafe_allow_html=True)
for l in memoria['terminal_logs'][:20]:
    cor_log = '#10b981' if l['tipo'] == 'buy' else '#ef4444' if l['tipo'] == 'sell' else '#38bdf8' if l['tipo'] == 'info' else '#fbbf24'
    st.markdown(f"<div style='border-bottom:1px solid #1e293b; padding:2px 0;'><span style='color:#64748b;font-size:11px;'>[{l['hora']}]</span> <span style='color: {cor_log}; font-weight:bold; font-size:12px;'>{l['msg']}</span></div>", unsafe_allow_html=True)
st.markdown("</div></div>", unsafe_allow_html=True)

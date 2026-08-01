import streamlit as st
import pandas as pd
import ccxt
import pytz
import time
import threading
import plotly.express as px
from datetime import datetime

# ==========================================
# ⚡ MEGA ROBÔ: AUTOBOLT OMNICORE v5.0 (B2C + DUAL-ENGINE KARV)
# ==========================================
st.set_page_config(page_title="AUTOBOLT OS // DUAL-ENGINE", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")
tz_br = pytz.timezone('America/Sao_Paulo')

# ==========================================
# 1. ESTILIZAÇÃO CSS PREMIUM
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #020617; color: #f8fafc; font-family: 'Inter', sans-serif; }
    .header-box { background: linear-gradient(90deg, #0f172a 0%, #020617 100%); padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); }
    .titulo { color: #ffffff; font-weight: 900; font-family: 'Inter', sans-serif; margin: 0; letter-spacing: 1px; text-transform: uppercase; }
    .subtitulo { color: #94a3b8; font-family: 'Inter', monospace; margin-top: 5px; font-size: 13px; }
    div[data-testid="stButton"] > button { background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%); color: #ffffff; border: none; border-radius: 6px; font-weight: 800; letter-spacing: 0.5px; transition: all 0.3s ease; }
    div[data-testid="stButton"] > button:hover { background: linear-gradient(90deg, #1d4ed8 0%, #1e3a8a 100%); box-shadow: 0 0 10px rgba(59, 130, 246, 0.5); }
    .panel-box { background: #0f172a; border: 1px solid #1e293b; border-radius: 4px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); }
    .panel-header { font-size: 12px; color: #e2e8f0; text-transform: uppercase; font-weight: bold; border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-bottom: 12px; letter-spacing: 1px; }
    .styled-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left; }
    .styled-table th { color: #94a3b8; padding: 12px 8px; border-bottom: 1px solid #1e293b; background: #020617; font-weight:bold; text-transform: uppercase; font-size: 0.75rem; }
    .styled-table td { padding: 12px 8px; border-bottom: 1px solid #1e293b; color: #f1f5f9; font-weight: 500; }
    .terminal-box { background: #000000; border: 1px solid #1e293b; padding: 12px; border-radius: 4px; height: 200px; overflow-y: auto; font-size: 0.85rem; font-family: monospace; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 900 !important; font-size: 1.8rem !important; }
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: 600 !important; font-size: 0.8rem !important; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. VARIÁVEIS GLOBAIS E MEMÓRIA
# ==========================================
TAXA_CORRETORA = 0.001
LIMITE_DRAWDOWN = 0.15
MAX_SLOTS = 10
ALOCACAO_POR_SLOT = 0.05
ALVOS_GLOBAIS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT', 'LINK/USDT', 'AVAX/USDT', 'NEAR/USDT', 'SUI/USDT']

@st.cache_resource
def carregar_memoria():
    return {
        'bot_ativo': False, 'caixa_livre': 10000.00, 'lucro_liquido': 0.0, 'taxas_pagas': 0.0, 
        'pico_patrimonio': 10000.00, 'portfolio_m1': {}, 'portfolio_m2': {}, 'terminal_logs': [], 
        'historico_trades': [], 'mercado_atual': {}, 'radar_ia': [], 'matriz_b2c': [], 
        'vitorias': 0, 'derrotas': 0, 'ultima_att': "Aguardando..."
    }

memoria = carregar_memoria()
quarentena_m1, quarentena_m2 = {}, {}

@st.cache_resource
def iniciar_exchange():
    return ccxt.kucoin({'enableRateLimit': True})

exchange = iniciar_exchange()

def add_log(msg, tipo="info"):
    memoria['terminal_logs'].insert(0, {"hora": datetime.now(tz_br).strftime('%H:%M:%S'), "msg": msg, "tipo": tipo})
    memoria['terminal_logs'] = memoria['terminal_logs'][:30]

def toggle_motor():
    memoria['bot_ativo'] = not memoria['bot_ativo']
    msg = "🚀 DUAL-ENGINE ENGAGED!" if memoria['bot_ativo'] else "🛑 MOTORES PAUSADOS."
    add_log(msg, "buy" if memoria['bot_ativo'] else "warn")

def checar_correlacao_risco(moeda, portfolio):
    grupos_risco = [['SOL/USDT', 'NEAR/USDT', 'AVAX/USDT', 'SUI/USDT'], ['ADA/USDT', 'DOT/USDT'], ['BTC/USDT', 'ETH/USDT']]
    for grupo in grupos_risco:
        if moeda in grupo:
            for m_ativa in portfolio.keys():
                if m_ativa in grupo and m_ativa != moeda: return True
    return False

# ==========================================
# 3. INTELIGÊNCIA AUTOBOLT (CÉREBRO)
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
        velas_4h = exchange.fetch_ohlcv(simbolo, '4h', limit=200)
        velas_15m = exchange.fetch_ohlcv(simbolo, '15m', limit=100)
        
        df_4h = pd.DataFrame(velas_4h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_15m = pd.DataFrame(velas_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        df_15m['RSI'] = calcular_rsi(df_15m['close'], 14)
        df_15m['EMA_20'] = df_15m['close'].ewm(span=20, adjust=False).mean()
        df_4h['EMA_200'] = df_4h['close'].ewm(span=200, adjust=False).mean()
        
        atual = df_15m.iloc[-1]; macro_atual = df_4h.iloc[-1]
        preco = atual['close']; rsi = atual['RSI']; ema_20 = atual['EMA_20']; ema_200_macro = macro_atual['EMA_200']
        volume_24h_usd = atual['volume'] * preco
        stop_loss_sugerido = preco * 0.975 
        
        status = "ALTA PROBABILIDADE"; motivo = "Tendência de Alta & Sem Exaustão Confirmada"; confianca = 85
        
        if volume_24h_usd < 100000: 
            status = "BAIXA LIQUIDEZ"; motivo = "Bloqueio: Volume insatisfatório (Risco de Derrapagem)"; confianca = 0
        elif pd.isna(rsi) or pd.isna(ema_20):
            status = "OBSERVAÇÃO"; motivo = "Aguardando volume histórico"; confianca = 0
        elif preco < ema_200_macro:
            status = "MÉDIA PROBABILIDADE"; motivo = "Bloqueio Macro: Tendência de Baixa no Gráfico 4h"; confianca = 25
        elif rsi >= limite_rsi:
            status = "RISCO DE TOPO"; motivo = f"Quarentena: RSI Micro >= {limite_rsi} (Exaustão)"; confianca = 40
        elif preco > (ema_20 * limite_ema): 
            status = "RISCO DE TOPO"; motivo = f"Quarentena: Preço esticado (> {(limite_ema - 1)*100:.1f}% da EMA)"; confianca = 45

        distancia_ema = ((preco / ema_20) - 1) * 100
        if status == "ALTA PROBABILIDADE" and -1.0 <= distancia_ema <= 0.5:
            confianca += 10; motivo += " | Pullback ideal na EMA 20"

        return {
            "Ativo": simbolo, "Preço": preco, "Confianca": min(99, confianca), "Stop_Loss_Sugerido": stop_loss_sugerido,
            "Veredicto": status, "Justificativa": motivo
        }
    except Exception as e:
        return {"Ativo": simbolo, "Preço": 0, "Confianca": 0, "Stop_Loss_Sugerido": 0, "Veredicto": "FALHA", "Justificativa": str(e)}

# ==========================================
# 4. THREAD CONTÍNUA (DUAL-ENGINE KARV)
# ==========================================
@st.cache_resource
def iniciar_motores_autobolt():
    def loop_operacional():
        while True:
            if not memoria['bot_ativo']: time.sleep(2); continue
            try:
                # 4.1. LEITURA DE PREÇOS
                for p, d in exchange.fetch_tickers(ALVOS_GLOBAIS).items():
                    if d['last']: memoria['mercado_atual'][p] = float(d['last'])

                vp_temp = sum([sum([g['qtd'] * memoria['mercado_atual'].get(m, g['pm']) for g in grids]) for m, grids in memoria['portfolio_m2'].items()]) if memoria['portfolio_m2'] else 0
                patrimonio_atual = memoria['caixa_livre'] + vp_temp
                if patrimonio_atual > memoria['pico_patrimonio']: memoria['pico_patrimonio'] = patrimonio_atual

                # CIRCUIT BREAKER GLOBAL
                dd_atual = ((memoria['pico_patrimonio'] - patrimonio_atual) / memoria['pico_patrimonio']) if memoria['pico_patrimonio'] > 0 else 0
                if dd_atual >= LIMITE_DRAWDOWN:
                    msg_cb = f"🚨 CIRCUIT BREAKER! DD: {dd_atual*100:.1f}%. Motores Desligados."
                    add_log(msg_cb, "sell")
                    for m, grids in list(memoria['portfolio_m2'].items()): memoria['caixa_livre'] += sum([g['qtd'] * memoria['mercado_atual'].get(m, g['pm']) for g in grids])
                    memoria['portfolio_m2'].clear(); memoria['portfolio_m1'].clear(); memoria['bot_ativo'] = False; continue

                agora = datetime.now(tz_br); ts_agora = time.time(); radar_temp = []; matriz_temp = []

                # 4.2. VARREDURA AUTOBOLT (ALIMENTA A MATRIZ E O M1)
                for m in ALVOS_GLOBAIS:
                    analise = analise_autobolt(m)
                    pr = analise['Preço']
                    if pr <= 0: continue
                    
                    matriz_temp.append({
                        "Ativo": m.replace('/USDT', ''), "Preço Atual": f"${pr:.4f}", "Índice de Confiança (%)": analise['Confianca'],
                        "Stop-Loss Sugerido": f"${analise['Stop_Loss_Sugerido']:.4f}", "Veredicto do Algoritmo": analise['Veredicto'],
                        "Justificativa Base": analise['Justificativa'], "_raw_status": analise['Veredicto']
                    })

                    status_radar = "⏳ AGUARDAR"
                    if m in memoria['portfolio_m2']: status_radar = "🟢 EXECUTANDO NO M2"
                    elif m in memoria['portfolio_m1']: status_radar = f"👁️ RASTREANDO NO M1 ({analise['Confianca']}%)"
                    elif m in quarentena_m1 and time.time() < quarentena_m1[m]: status_radar = "🔴 M1 QUARENTENA"
                    else:
                        if analise['Veredicto'] == "ALTA PROBABILIDADE" and len(memoria['portfolio_m1']) < MAX_SLOTS:
                            memoria['portfolio_m1'][m] = [{'pm': pr, 'pico_preco': pr, 'fundo_preco': pr, 'm2_triggered': False, 'ts_compra': ts_agora, 'stop_sugerido': analise['Stop_Loss_Sugerido']}]
                            add_log(f"👁️ M1: Rastreio Iniciado [{m}]. Confiança: {analise['Confianca']}%", "info")
                            status_radar = f"👁️ COMPRA M1 ({analise['Confianca']}%)"
                            
                    radar_temp.insert(0, {"hora": agora.strftime('%H:%M:%S'), "ativo": m, "sinal": status_radar})
                
                memoria['matriz_b2c'] = matriz_temp
                memoria['radar_ia'] = radar_temp[:10]
                memoria['ultima_att'] = agora.strftime('%d/%m/%Y %H:%M:%S')

                # 4.3. MOTOR 1 (BATEDOR AVANÇADO)
                for m, grids in list(memoria['portfolio_m1'].items()):
                    pr = memoria['mercado_atual'].get(m)
                    if not pr: continue
                    g_rem = []
                    for g in grids:
                        g['pico_preco'] = max(g['pico_preco'], pr)
                        g['fundo_preco'] = min(g['fundo_preco'], pr)
                        pnl_atual = (pr - g['pm']) / g['pm']
                        pnl_do_pico = (g['pico_preco'] - g['pm']) / g['pm'] 
                        queda_do_topo = (pr - g['pico_preco']) / g['pico_preco']
                        
                        if pnl_atual <= -0.01 and not g.get('m2_triggered', False):
                            if m not in memoria['portfolio_m2'] and len(memoria['portfolio_m2']) < MAX_SLOTS and not checar_correlacao_risco(m, memoria['portfolio_m2']):
                                tam = patrimonio_atual * ALOCACAO_POR_SLOT
                                if tam > memoria['caixa_livre']: tam = memoria['caixa_livre']
                                if tam >= 5.0:
                                    taxa_compra = tam * TAXA_CORRETORA; memoria['taxas_pagas'] += taxa_compra; memoria['caixa_livre'] -= tam
                                    memoria['portfolio_m2'][m] = [{
                                        'qtd': (tam - taxa_compra)/pr, 'pm': pr, 'pico_preco': pr, 'fundo_preco': pr, 'stop_loss_dyn': g['stop_sugerido'],
                                        'data_compra': agora.strftime('%Y-%m-%d %H:%M:%S'), 'ts_compra': ts_agora, 'taxa_compra': taxa_compra
                                    }]
                                    g['m2_triggered'] = True
                                    add_log(f"🎯 GATILHO M1! [{m}] caiu -1%. M2 executou a compra a ${pr:.4f}!", "buy")

                        vender_m1 = False; tipo_venda_m1 = ""
                        if pnl_do_pico >= 0.0075 and queda_do_topo <= -0.0025: vender_m1 = True; tipo_venda_m1 = "SCALP WIN"
                        elif pnl_atual <= -0.025: vender_m1 = True; tipo_venda_m1 = "STOP LOSS"

                        if vender_m1:
                            add_log(f"👁️ M1 FINALIZADO [{m}]: {tipo_venda_m1} com {pnl_atual*100:+.2f}%", "info")
                            quarentena_m1[m] = ts_agora + ((6 if pnl_atual > 0 else 1) * 3600)
                            g_rem.append(g)
                    for g in g_rem: grids.remove(g)
                    if not grids: del memoria['portfolio_m1'][m]

                # 4.4. MOTOR 2 (EXECUÇÃO DE CAIXA)
                for m, grids in list(memoria['portfolio_m2'].items()):
                    pr = memoria['mercado_atual'].get(m)
                    if not pr: continue
                    g_rem = []
                    for g in grids:
                        g['pico_preco'] = max(g['pico_preco'], pr)
                        g['fundo_preco'] = min(g['fundo_preco'], pr)
                        pnl_atual = (pr - g['pm']) / g['pm']
                        pnl_do_pico = (g['pico_preco'] - g['pm']) / g['pm'] 
                        queda_do_topo = (pr - g['pico_preco']) / g['pico_preco']
                        vender = False; tipo_venda = ""

                        if pnl_do_pico >= 0.0075 and queda_do_topo <= -0.0025: vender = True; tipo_venda = "SCALP WIN (SURF)"
                        elif pr <= g['stop_loss_dyn']: vender = True; tipo_venda = "STOP LOSS DINÂMICO"
                        elif pnl_atual <= -0.03: vender = True; tipo_venda = "STOP LOSS EMERGÊNCIA" # 3% Trava de segurança extra

                        if vender:
                            taxa_venda = (g['qtd'] * pr) * TAXA_CORRETORA; liq = (g['qtd'] * pr) - taxa_venda; l = liq - (g['qtd'] * g['pm'])
                            memoria['taxas_pagas'] += taxa_venda; memoria['caixa_livre'] += liq; memoria['lucro_liquido'] += l
                            add_log(f"💰 M2 {tipo_venda} [{m}]: Lucro +${l:.2f}" if l > 0 else f"🛑 M2 {tipo_venda} [{m}]: Perda -${abs(l):.2f}", "buy" if l > 0 else "sell")
                            if l > 0: memoria['vitorias'] += 1; quarentena_m2[m] = ts_agora + (6 * 3600)
                            else: memoria['derrotas'] += 1; quarentena_m2[m] = ts_agora + (1 * 3600)
                            g_rem.append(g)
                    for g in g_rem: grids.remove(g)
                    if not grids: del memoria['portfolio_m2'][m]

            except Exception as e: add_log(f"⚠️ Erro no Loop: {str(e)[:40]}", "warn")
            time.sleep(15)
    threading.Thread(target=loop_operacional, daemon=True).start()

iniciar_motores_autobolt()

# Loop para Refresh da Tela
time.sleep(0.5)
agora = time.time()
if agora - memoria.get('tela_att', 0) > 3:
    memoria['tela_att'] = agora
    st.rerun()

# ==========================================
# 5. RENDERIZAÇÃO DA INTERFACE INSTITUCIONAL
# ==========================================
col_t, col_b = st.columns([4, 1])
with col_t:
    st.markdown("""
        <div class="header-box" translate="no">
            <h1 class="titulo">⚡ AUTOBOLT OMNICORE v5.0</h1>
            <div class="subtitulo">B2C PREMIUM MATRIX + DUAL-ENGINE EXECUTION</div>
        </div>
    """, unsafe_allow_html=True)
with col_b:
    st.markdown("<br>", unsafe_allow_html=True)
    btn_label = "🛑 PAUSAR MOTORES" if memoria['bot_ativo'] else "🚀 ENGATAR MOTORES"
    st.markdown(f"""<style>div[data-testid="stButton"] > button {{ {'background: linear-gradient(90deg, #ef4444 0%, #b91c1c 100%);' if memoria['bot_ativo'] else ''} }}</style>""", unsafe_allow_html=True)
    if st.button(btn_label, use_container_width=True): toggle_motor(); st.rerun()

# KPIs Financeiros
vp = sum([sum([g['qtd'] * memoria['mercado_atual'].get(m, g['pm']) for g in grids]) for m, grids in memoria['portfolio_m2'].items()]) if memoria['portfolio_m2'] else 0
patrimonio_total_kpi = memoria['caixa_livre'] + vp
dd = ((memoria['pico_patrimonio'] - patrimonio_total_kpi) / memoria['pico_patrimonio']) * 100 if memoria['pico_patrimonio'] > 0 else 0.0

st.write("---")
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: st.metric("Patrimônio Total", f"${patrimonio_total_kpi:,.2f}")
with k2: st.metric("Risco (Drawdown)", f"{dd:.2f}%")
with k3: st.metric("Capital Alocado", f"${vp:,.2f}")
with k4: st.metric("Lucro Líquido", f"${memoria['lucro_liquido']:,.2f}")
with k5: st.metric("Slots M2", f"{len(memoria['portfolio_m2'])} / {MAX_SLOTS}")
with k6: st.metric("Taxa Acerto M2", f"{memoria['vitorias']}W / {memoria['derrotas']}L")

# Matriz B2C
st.write("---")
st.markdown(f"### 📡 MATRIX DE DECISÃO B2C <span style='font-size:12px; color:#64748b; float:right;'>Sincronização: {memoria['ultima_att']}</span>", unsafe_allow_html=True)

def aplicar_cores_tabela(row):
    confianca = row['Índice de Confiança (%)']
    cor = '#10b981' if confianca >= 80 else '#f59e0b' if confianca >= 60 else '#64748b' if confianca == 0 else '#ef4444'
    estilos = ['background-color: #0f172a; color: #f8fafc; border-bottom: 1px solid #1e293b;'] * (len(row) - 1) 
    idx_confianca = row.index.get_loc('Índice de Confiança (%)')
    idx_veredicto = row.index.get_loc('Veredicto do Algoritmo')
    idx_stop = row.index.get_loc('Stop-Loss Sugerido')
    estilos[idx_confianca] = f'background-color: #0f172a; color: {cor}; font-weight: 900; font-size: 15px; border-bottom: 1px solid #1e293b;'
    estilos[idx_veredicto] = f'background-color: #0f172a; color: {cor}; font-weight: bold; border-bottom: 1px solid #1e293b;'
    estilos[idx_stop] = f'background-color: #0f172a; color: #ef4444; font-weight: bold; border-bottom: 1px solid #1e293b;'
    return estilos + ['']

df = pd.DataFrame(memoria['matriz_b2c'])
if not df.empty:
    df_exibicao = df.sort_values(by="Índice de Confiança (%)", ascending=False).reset_index(drop=True)
    df_estilizado = df_exibicao.style.apply(aplicar_cores_tabela, axis=1)
    st.dataframe(df_estilizado, use_container_width=True, hide_index=True, column_config={"_raw_status": None}, height=250)

# Motores Visuais (M1 e M2)
p1, p2 = st.columns(2)
with p1:
    st.markdown("<div class='panel-box' translate='no'><div class='panel-header'>👁️ MOTOR 1: SALA DE OBSERVAÇÃO (GATILHO -1%)</div>", unsafe_allow_html=True)
    if memoria['portfolio_m1']:
        tb_m1 = "<table class='styled-table'><tr><th>Ativo</th><th>PM</th><th>Preço Atual</th><th>PNL Flutuante</th></tr>"
        for m, grids in memoria['portfolio_m1'].items():
            pm_tot = grids[0]['pm']; pr_atual = memoria['mercado_atual'].get(m, pm_tot)
            pnl_m1 = ((pr_atual - pm_tot) / pm_tot) * 100
            cor_pnl = "#ef4444" if pnl_m1 <= 0 else "#10b981"
            tb_m1 += f"<tr><td><b>{m}</b></td><td>${pm_tot:.4f}</td><td>${pr_atual:.4f}</td><td style='color:{cor_pnl}; font-weight:bold;'>{pnl_m1:+.2f}%</td></tr>"
        st.markdown(tb_m1 + "</table></div>", unsafe_allow_html=True)
    else: st.info("Nenhum ativo rastreado pelo M1 no momento."); st.markdown("</div>", unsafe_allow_html=True)

with p2:
    st.markdown("<div class='panel-box' translate='no'><div class='panel-header'>💼 MOTOR 2: CUSTÓDIA ATIVA (EXECUÇÃO)</div>", unsafe_allow_html=True)
    if memoria['portfolio_m2']:
        tb_m2 = "<table class='styled-table'><tr><th>Ativo</th><th>PM</th><th>Preço Atual</th><th>Stop-Loss (Dyn)</th><th>Flutuante PNL</th></tr>"
        for m, grids in memoria['portfolio_m2'].items():
            qtd_tot = sum([g['qtd'] for g in grids]); pm_tot = sum([g['qtd']*g['pm'] for g in grids]) / qtd_tot if qtd_tot > 0 else 0
            pr_atual = memoria['mercado_atual'].get(m, pm_tot)
            stop_dyn = grids[0]['stop_loss_dyn']
            pnl_usd = (qtd_tot * pr_atual) - (qtd_tot * pm_tot)
            pnl_pct = (pnl_usd / (qtd_tot * pm_tot)) * 100 if pm_tot > 0 else 0
            cor_pnl = "#10b981" if pnl_usd >= 0 else "#ef4444"
            tb_m2 += f"<tr><td><b>{m}</b></td><td>${pm_tot:.4f}</td><td>${pr_atual:.4f}</td><td style='color:#ef4444;'>${stop_dyn:.4f}</td><td style='color:{cor_pnl}; font-weight:bold;'>{pnl_pct:+.2f}%</td></tr>"
        st.markdown(tb_m2 + "</table></div>", unsafe_allow_html=True)
    else: st.info("Nenhuma posição executada no M2."); st.markdown("</div>", unsafe_allow_html=True)

# Logs e Telemetria
cl, ca = st.columns([2.5, 1])
with cl:
    logs_html = "".join([f"<div style='margin-bottom:4px; border-bottom:1px solid #1e293b; padding-bottom:2px;'><span style='color:#64748b;font-size:11px;'>[{l['hora']}]</span> <span style='color: {'#10b981' if l['tipo']=='buy' else '#ef4444' if l['tipo']=='sell' else '#38bdf8' if l['tipo']=='info' else '#fbbf24'}; font-weight:bold; font-size:12px;'>{l['msg']}</span></div>" for l in memoria['terminal_logs'][:15]])
    st.markdown(f"<div class='panel-box' translate='no'><div class='panel-header'>🖥️ TERMINAL DE LOGS INSTITUCIONAL</div><div class='terminal-box'>{logs_html}</div></div>", unsafe_allow_html=True)
with ca:
    st.markdown("<div class='panel-box' translate='no'><div class='panel-header'>📡 RASTREAMENTO GLOBAL</div>", unsafe_allow_html=True)
    tb = "<table class='styled-table'><tr><th>Ativo</th><th>Status da Rota</th></tr>"
    for r in memoria['radar_ia']:
        cor_span = "#10b981" if "M2" in r['sinal'] else "#ef4444" if "QUARENTENA" in r['sinal'] else "#f59e0b" if "M1" in r['sinal'] else "#334155"
        tb += f"<tr><td translate='no'><b>{r['ativo'].split('/')[0]}</b></td><td><span translate='no' style='background:{cor_span}; color:#fff; padding:3px 6px; border-radius:2px; font-size:10px; font-weight:bold;'>{r['sinal']}</span></td></tr>"
    st.markdown(tb + "</table></div>", unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import ccxt
import pytz
import time
import threading
import random
import os
import plotly.express as px
from datetime import datetime
from supabase import create_client

# Dependências de IA (Auto-Cura lida com a ausência delas)
try:
    from groq import Groq
    import google.generativeai as gemini
    IA_AVAILABLE = True
except ImportError:
    IA_AVAILABLE = False

# ==========================================
# ⚡ MEGA ROBÔ: LIONBOT SENTINEL // OMNICORE V7.0
# ==========================================
st.set_page_config(page_title="LionBot Sentinel | Auto Bot", page_icon="🦁", layout="wide", initial_sidebar_state="expanded")
tz_br = pytz.timezone('America/Sao_Paulo')
COR_TEMA = "#00ffcc" # Verde Neon LionBot

# ==========================================
# 1. ESTILIZAÇÃO CSS (CYBERPUNK + INSTITUCIONAL)
# ==========================================
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0b0f19; color: #f8fafc; font-family: 'Inter', sans-serif; }}
    .header-box {{ background: linear-gradient(90deg, #161f30 0%, #0b0f19 100%); padding: 20px; border-radius: 10px; border-left: 4px solid {COR_TEMA}; margin-bottom: 20px; border-top: 1px solid #1e293b; box-shadow: 0 0 15px rgba(0, 255, 204, 0.1); }}
    .titulo {{ color: {COR_TEMA}; font-weight: 900; font-family: 'Courier New', monospace; margin: 0; text-align: center; letter-spacing: 2px; text-transform: uppercase; }}
    .subtitulo {{ color: #94a3b8; font-family: monospace; margin-top: 5px; text-align: center; font-size: 13px; }}
    div[data-testid="stButton"] > button {{ background: linear-gradient(90deg, #0f766e 0%, #047857 100%); color: #ffffff; border: 1px solid {COR_TEMA}; border-radius: 6px; font-weight: 800; transition: all 0.3s ease; }}
    div[data-testid="stButton"] > button:hover {{ background: {COR_TEMA}; color: #000000; box-shadow: 0 0 15px rgba(0, 255, 204, 0.6); }}
    .btn-sniper div[data-testid="stButton"] > button {{ background: linear-gradient(90deg, #ef4444 0%, #b91c1c 100%) !important; border: 1px solid #ef4444 !important; font-size: 11px !important; padding: 2px 10px !important; min-height: 30px !important; }}
    .panel-box {{ background: #161f30; border: 1px solid #1e293b; border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
    .panel-header {{ font-size: 12px; color: {COR_TEMA}; text-transform: uppercase; font-weight: bold; border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-bottom: 12px; }}
    .styled-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left; }}
    .styled-table th {{ color: #94a3b8; padding: 10px 8px; border-bottom: 1px solid {COR_TEMA}; background: #0b0f19; font-weight:bold; text-transform: uppercase; }}
    .styled-table td {{ padding: 10px 8px; border-bottom: 1px solid #1e293b; color: #f1f5f9; font-weight: 500; }}
    .terminal-box {{ background: #000000; border: 1px solid {COR_TEMA}; padding: 12px; border-radius: 4px; height: 250px; overflow-y: auto; font-size: 0.85rem; font-family: monospace; box-shadow: inset 0 0 10px rgba(0, 255, 204, 0.1); }}
    div[data-testid="stMetricValue"] {{ color: {COR_TEMA} !important; font-weight: 900 !important; font-size: 1.8rem !important; font-family: 'Courier New', monospace; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MEMÓRIA, SUPABASE & CHAVES
# ==========================================
ALVOS_GLOBAIS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT', 'LINK/USDT', 'AVAX/USDT', 'NEAR/USDT', 'SUI/USDT']
TAXA_CORRETORA = 0.001
ALOCACAO_SIMULADA = 0.05
ALOCACAO_REAL = 0.30 

SUPA_URL = st.secrets.get("SUPABASE_URL", "")
SUPA_KEY = st.secrets.get("SUPABASE_KEY", "")
supabase = create_client(SUPA_URL, SUPA_KEY) if SUPA_URL and SUPA_KEY else None

@st.cache_resource
def carregar_memoria():
    return {
        'bot_ativo': False, 'caixa_livre_simulado': 10000.00, 'caixa_real': 0.0,
        'lucro_liquido_simulado': 0.0, 'portfolio_m1': {}, 'portfolio_m2': {}, 'portfolio_m3_real': {},
        'matriz_b2c': [], 'terminal_logs': [], 'mercado_atual': {}, 'ultima_att': "Aguardando..."
    }
memoria = carregar_memoria()

def salvar_seguranca_duck():
    """🛡️ Módulo de Segurança Sentinel (Supabase Sync)"""
    if supabase:
        try:
            mem_clone = memoria.copy()
            mem_clone['bot_ativo'] = False # Não salva o estado ativo para evitar religação acidental
            supabase.table('lion_state').upsert({'id': 1, 'state': mem_clone}).execute()
        except:
            add_log("Healer Engine: Falha no Supabase. Mantendo dados em RAM.", "warn")

def add_log(msg, tipo="info"):
    memoria['terminal_logs'].insert(0, {"hora": datetime.now(tz_br).strftime('%H:%M:%S'), "msg": msg, "tipo": tipo})
    memoria['terminal_logs'] = memoria['terminal_logs'][:40]

# ==========================================
# 3. GHOST AI & ANTI-BAN POOL
# ==========================================
# GHOST AI: Mascara as requisições CCXT como se fossem de um navegador Chrome humano
headers_ghost = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
}

@st.cache_resource
def iniciar_pool_leitura():
    exchanges = [ccxt.kucoin(), ccxt.bybit(), ccxt.okx()]
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
    raise Exception("Falha nas rotas Ghost.")

# ==========================================
# 4. ORQUESTRADOR NEURAL (7 ESPECIALISTAS)
# ==========================================
def orquestrador_inteligencia(ativo, dados_tec):
    """
    Motor Neural que simula 7 perspectivas:
    Trend, Volatilidade, Baleias, Risco, Sentimento, Momentum, Juiz Sentinel.
    """
    if not IA_AVAILABLE: return dados_tec['score_base'], "Consenso Técnico (IA Offline)"
    
    gemini_key = st.secrets.get("GEMINI_API_KEY", "")
    if not gemini_key: return dados_tec['score_base'], "Consenso Técnico (Chave IA Ausente)"
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""Você é o Conselho Sentinel, formado por 7 especialistas financeiros. 
        Analise os dados deste ativo: {ativo}. Preço: {dados_tec['preco']}. RSI 15m: {dados_tec['rsi']:.1f}. Distância EMA20: {dados_tec['dist_ema']:.2f}%. Volume 24h: Alto.
        Avalie o risco e responda APENAS com um número de 0 a 100 (representando a Confiança) seguido de um traço e UMA frase curta justificando o voto em nome do Conselho."""
        
        resposta = model.generate_content(prompt).text.strip()
        # Esperado: "85 - RSI em zona de sobrevenda com fluxo institucional favorável"
        partes = resposta.split('-', 1)
        score_ia = int(partes[0].strip())
        justificativa = partes[1].strip() if len(partes) > 1 else "Consenso alcançado pela IA."
        return score_ia, justificativa
        
    except Exception as e:
        # Healer Engine atua aqui e volta para a matemática
        return dados_tec['score_base'], "Healer Engine: Falha Neural. Veredicto Técnico aplicado."

# ==========================================
# 5. MATRIZ DE RISCO & CÁLCULOS
# ==========================================
def analise_matriz_risco(simbolo):
    try:
        velas_15m = obter_dados_ghost(simbolo, '15m', 100)
        df_15m = pd.DataFrame(velas_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Matemática
        delta = df_15m['close'].diff()
        gain = delta.where(delta > 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        ema_20 = df_15m['close'].ewm(span=20, adjust=False).mean().iloc[-1]
        preco = df_15m['close'].iloc[-1]
        
        dist_ema = ((preco / ema_20) - 1) * 100
        stop_loss_sugerido = preco * 0.975 
        alvo_surf = preco * 1.0075
        
        # Matriz Matemática (Score Base)
        score_base = 50
        if rsi < 35: score_base += 30
        elif rsi > 70: score_base -= 40
        if -1.0 <= dist_ema <= 0.5: score_base += 15
        
        dados_tec = {'preco': preco, 'rsi': rsi, 'dist_ema': dist_ema, 'score_base': score_base}
        
        # Filtro de Relevância: Só aciona a IA se o ativo estiver promissor matematicamente (> 60)
        if score_base > 60:
            score_final, motivo = orquestrador_inteligencia(simbolo, dados_tec)
        else:
            score_final, motivo = score_base, "Aguardando alinhamento técnico para acionar a IA."
            
        score_final = max(0, min(99, score_final))
        veredicto = "ALTA PROBABILIDADE" if score_final >= 80 else "MÉDIA PROBABILIDADE" if score_final >= 60 else "BAIXA LIQUIDEZ / RISCO"

        return {
            "Ativo": simbolo, "Preço": preco, "Confianca": score_final, 
            "Stop_Loss_Sugerido": stop_loss_sugerido, "Alvo_Sugerido": alvo_surf,
            "Veredicto": veredicto, "Justificativa": motivo
        }
    except Exception as e:
        return {"Ativo": simbolo, "Preço": 0, "Confianca": 0, "Stop_Loss_Sugerido": 0, "Alvo_Sugerido": 0, "Veredicto": "FALHA", "Justificativa": str(e)}

# ==========================================
# 6. MOTOR 3: MESA SNIPER
# ==========================================
def executar_compra_real(moeda, api_key, api_secret, api_pass, dados_analise):
    try:
        ex_real = ccxt.kucoin({'apiKey': api_key, 'secret': api_secret, 'password': api_pass, 'enableRateLimit': True})
        saldo = ex_real.fetch_balance()
        caixa = float(saldo['free'].get('USDT', 0.0))
        
        if caixa < 10:
            st.toast("⚠️ Saldo insuficiente na KuCoin.")
            return False
            
        pr = dados_analise['Preço']
        tamanho_ordem = caixa * ALOCACAO_REAL
        if tamanho_ordem < 5: tamanho_ordem = 5
        
        qtd_alvo = float(ex_real.amount_to_precision(moeda, tamanho_ordem / pr))
        ex_real.create_market_buy_order(moeda, qtd_alvo) # ORDEM REAL
        
        memoria['portfolio_m3_real'][moeda] = [{'qtd': qtd_alvo, 'pm': pr, 'pico_preco': pr, 'stop_dyn': dados_analise['Stop_Loss_Sugerido'], 'alvo': dados_analise['Alvo_Sugerido']}]
        add_log(f"⚡ M3 SNIPER EXECUTADO! Ordem REAL de {moeda} enviada a ${pr:.4f}.", "buy")
        st.toast(f"🎯 Compra de {moeda} executada com sucesso na KuCoin!")
        return True
    except Exception as e:
        add_log(f"❌ M3 HEALER: Erro ao executar - {str(e)[:50]}", "sell")
        st.toast("Erro na API da KuCoin. Verifique as chaves.")
        return False

# ==========================================
# 7. THREAD CONTÍNUA (TRÍADE)
# ==========================================
@st.cache_resource
def iniciar_motores_sentinel():
    def loop_operacional():
        while True:
            if not memoria['bot_ativo']: time.sleep(2); continue
            try:
                agora = datetime.now(tz_br); ts_agora = time.time(); matriz_temp = []
                
                # Leitura Ticker Ghost
                try:
                    for p, d in pool_exchanges[0].fetch_tickers(ALVOS_GLOBAIS).items():
                        if d['last']: memoria['mercado_atual'][p] = float(d['last'])
                except: pass

                for m in ALVOS_GLOBAIS:
                    analise = analise_matriz_risco(m)
                    if analise['Preço'] <= 0: continue
                    
                    matriz_temp.append({
                        "Ativo": m.replace('/USDT', ''), "Preço Atual": f"${analise['Preço']:.4f}", "Índice de Confiança (%)": analise['Confianca'],
                        "Stop-Loss Sugerido": f"${analise['Stop_Loss_Sugerido']:.4f}", "Veredicto do Algoritmo": analise['Veredicto'],
                        "Justificativa Base": analise['Justificativa'], "_raw_status": analise['Veredicto'], "_dados": analise
                    })

                    # M1 (Batedor)
                    if analise['Confianca'] >= 80 and m not in memoria['portfolio_m1'] and m not in memoria['portfolio_m2']:
                        memoria['portfolio_m1'][m] = [{'pm': analise['Preço'], 'pico_preco': analise['Preço'], 'stop_dyn': analise['Stop_Loss_Sugerido']}]
                        add_log(f"👁️ M1: Anomalia detectada em {m}. Monitorando para queda...", "info")

                memoria['matriz_b2c'] = matriz_temp
                memoria['ultima_att'] = agora.strftime('%d/%m/%Y %H:%M:%S')

                # M2 (Executor Simulado)
                for m, grids in list(memoria['portfolio_m1'].items()):
                    pr = memoria['mercado_atual'].get(m)
                    if not pr: continue
                    g_rem = []
                    for g in grids:
                        g['pico_preco'] = max(g['pico_preco'], pr)
                        if ((pr - g['pm']) / g['pm']) <= -0.01:
                            memoria['portfolio_m2'][m] = [{'qtd': (1000)/pr, 'pm': pr, 'pico_preco': pr, 'stop_dyn': g['stop_dyn']}]
                            add_log(f"🎯 M2: Acionamento Simulado em {m} a ${pr:.4f}!", "buy")
                            g_rem.append(g)
                    for g in g_rem: grids.remove(g)
                    if not grids: del memoria['portfolio_m1'][m]

                # M2 Gerenciamento
                for m, grids in list(memoria['portfolio_m2'].items()):
                    pr = memoria['mercado_atual'].get(m)
                    g_rem = []
                    for g in grids:
                        g['pico_preco'] = max(g['pico_preco'], pr)
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
                
                salvar_seguranca_duck() # Backup Supabase

            except Exception as e: add_log(f"⚠️ Healer Engine: Erro no loop {str(e)[:40]}", "warn")
            time.sleep(15) 
    threading.Thread(target=loop_operacional, daemon=True).start()

iniciar_motores_sentinel()

time.sleep(0.5)
if time.time() - memoria.get('tela_att', 0) > 3:
    memoria['tela_att'] = time.time()
    st.rerun()

# ==========================================
# 8. INTERFACE VISUAL (LIONBOT AESTHETICS)
# ==========================================
with st.sidebar:
    st.markdown(f"<h2 style='color:{COR_TEMA}; font-family:Courier New;'>🕹️ PAINEL LIONBOT</h2>", unsafe_allow_html=True)
    
    btn_label = "🛑 DESLIGAR ROBÔ" if memoria['bot_ativo'] else "⚡ LIGAR SENTINEL"
    st.markdown(f"""<style>div[data-testid="stSidebar"] div[data-testid="stButton"] > button {{ {'background: #ef4444;' if memoria['bot_ativo'] else ''} }}</style>""", unsafe_allow_html=True)
    if st.button(btn_label, use_container_width=True): 
        memoria['bot_ativo'] = not memoria['bot_ativo']
        st.toast("Status do Robô alterado!")
        st.rerun()
        
    st.write("---")
    st.markdown("### 🔐 Cofre M3 (Sniper)")
    key_api = st.text_input("KuCoin API Key", type="password")
    sec_api = st.text_input("KuCoin Secret", type="password")
    pass_api = st.text_input("KuCoin Pass", type="password")
    st.write("---")
    if st.button("🔄 FORÇAR REFRESH"): st.rerun()

st.markdown("""
    <div class="header-box" translate="no">
        <h1 class="titulo">🦁 LIONBOT SENTINEL // OMNICORE V7.0</h1>
        <div class="subtitulo">ORQUESTRADOR NEURAL DE 7 CABEÇAS | GHOST AI | MESA SNIPER B2C</div>
    </div>
""", unsafe_allow_html=True)

# KPIs e Gráfico de Horários
col1, col2, col3 = st.columns([1, 1, 1.5])
with col1: 
    st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
    st.metric("Caixa Simulado", f"${memoria['caixa_livre_simulado']:,.2f}")
    st.metric("Lucro Simulado (M2)", f"${memoria['lucro_liquido_simulado']:,.2f}")
    st.markdown("</div>", unsafe_allow_html=True)
with col2: 
    st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
    st.metric("Ativos em Rastreio (M1)", len(memoria['portfolio_m1']))
    st.metric("Ordens Reais Abertas (M3)", len(memoria['portfolio_m3_real']))
    st.markdown("</div>", unsafe_allow_html=True)
with col3:
    # Gráfico de Horários de Investimento
    st.markdown("<div class='panel-box' style='padding:5px;'>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center; font-size:12px; color:{COR_TEMA}; font-weight:bold; margin-bottom:5px;'>⏰ MAPA DE CALOR: MELHORES JANELAS DE OPERAÇÃO</div>", unsafe_allow_html=True)
    df_horas = pd.DataFrame({"Horário": ["00h-04h (Ásia)", "04h-08h (Londres)", "08h-12h (NY)", "12h-16h (NY/BR)", "16h-20h (Fechamento)"], "Oportunidade (%)": [65, 80, 95, 85, 60]})
    fig = px.bar(df_horas, x="Horário", y="Oportunidade (%)", template="plotly_dark", color_discrete_sequence=[COR_TEMA])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=140, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.update_xaxes(showgrid=False, title=None, tickfont=dict(size=9)); fig.update_yaxes(showgrid=False, showticklabels=False, title=None)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Matriz B2C + Motor 3
st.markdown(f"### 📡 MATRIX DE DECISÃO & MESA SNIPER (M3) <span style='font-size:12px; color:#64748b; float:right;'>Sincronização: {memoria['ultima_att']}</span>", unsafe_allow_html=True)

df = pd.DataFrame(memoria['matriz_b2c'])
if not df.empty:
    df_exibicao = df.sort_values(by="Índice de Confiança (%)", ascending=False).reset_index(drop=True)
    
    st.markdown(f"<div style='display:flex; border-bottom:1px solid {COR_TEMA}; padding-bottom:10px; color:#94a3b8; font-size:12px; font-weight:bold; text-transform:uppercase;'><div style='flex:1;'>Ação (M3)</div><div style='flex:1;'>Ativo</div><div style='flex:1;'>Preço</div><div style='flex:1;'>Confiança</div><div style='flex:1.5;'>Veredicto</div><div style='flex:1;'>Stop Dyn</div><div style='flex:2;'>Inteligência Sentinel</div></div>", unsafe_allow_html=True)
    
    for idx, row in df_exibicao.iterrows():
        conf = row['Índice de Confiança (%)']
        cor = COR_TEMA if conf >= 80 else '#f59e0b' if conf >= 60 else '#64748b' if conf == 0 else '#ef4444'
        ativo_ccxt = f"{row['Ativo']}/USDT"
        
        c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 1, 1, 1, 1.5, 1, 2])
        with c1:
            if conf >= 60:
                st.markdown("<div class='btn-sniper'>", unsafe_allow_html=True)
                if st.button("⚡ COMPRAR", key=f"btn_{ativo_ccxt}"):
                    if not key_api: st.error("Insira as chaves na Barra Lateral!")
                    else: executar_compra_real(ativo_ccxt, key_api, sec_api, pass_api, row['_dados'])
                st.markdown("</div>", unsafe_allow_html=True)
            else: st.markdown("<span style='color:#475569; font-size:12px;'>Bloqueado</span>", unsafe_allow_html=True)
        with c2: st.markdown(f"<b>{row['Ativo']}</b>", unsafe_allow_html=True)
        with c3: st.markdown(f"{row['Preço Atual']}", unsafe_allow_html=True)
        with c4: st.markdown(f"<span style='color:{cor}; font-weight:bold; font-size:16px;'>{conf}%</span>", unsafe_allow_html=True)
        with c5: st.markdown(f"<span style='color:{cor}; font-weight:bold;'>{row['Veredicto do Algoritmo']}</span>", unsafe_allow_html=True)
        with c6: st.markdown(f"<span style='color:#ef4444;'>{row['Stop-Loss Sugerido']}</span>", unsafe_allow_html=True)
        with c7: st.markdown(f"<span style='font-size:11px; color:#cbd5e1;'>{row['Justificativa Base']}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='border: 1px solid #161f30; margin: 4px 0;'>", unsafe_allow_html=True)

# Logs Estilo LionBot
st.write("---")
st.markdown("### 📜 HISTÓRICO DE CAÇA (SENTINEL LOGS)")
st.markdown("<div class='terminal-box'>", unsafe_allow_html=True)
if memoria['terminal_logs']:
    for l in memoria['terminal_logs'][:20]:
        cor_log = COR_TEMA if l['tipo'] == 'buy' else '#ef4444' if l['tipo'] == 'sell' else '#38bdf8' if l['tipo'] == 'info' else '#f59e0b'
        st.markdown(f"<div style='border-bottom:1px solid #161f30; padding:4px 0;'><span style='color:#64748b;'>[{l['hora']}]</span> <span style='color: {cor_log}; font-weight:bold;'>{l['msg']}</span></div>", unsafe_allow_html=True)
else:
    st.write("*Nenhuma operação registrada na memória RAM.*")
st.markdown("</div>", unsafe_allow_html=True)

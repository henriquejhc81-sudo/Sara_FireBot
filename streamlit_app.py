import streamlit as st
import ccxt
import time
import random
import pandas as pd
import io
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Sara_Firebolt", page_icon="⚡", layout="wide")

URL = st.secrets.get("SUPABASE_URL", "")
KEY = st.secrets.get("SUPABASE_KEY", "")
supabase = create_client(URL, KEY) if URL and KEY else None

# FUNÇÃO MASTER: Carrega e sincroniza o estado persistente do banco de dados
def carregar_estado_banco():
    estado = {
        'saldo_usdt': 10000.0, 'bot_ativo': False, 'historico': [],
        'ativos': {
            'BTC/USDT': {'saldo': 0.0, 'pm': 0.0, 'ordens': 0, 'ref': 0.0, 'topo': 0.0, 'queda_ia': 0.08, 'lucro_ia': 0.18, 'last_p': 64188.0},
            'ETH/USDT': {'saldo': 0.0, 'pm': 0.0, 'ordens': 0, 'ref': 0.0, 'topo': 0.0, 'queda_ia': 0.12, 'lucro_ia': 0.25, 'last_p': 3450.0}
        }
    }
    if supabase:
        try:
            res = supabase.table("estado_bot").select("*").order("id", desc=True).limit(1).execute()
            if res.data:
                db = res.data[0]
                estado['saldo_usdt'] = db['saldo_usdt']
                estado['bot_ativo'] = db['bot_ativo']
                estado['ativos'] = db['ativos_json']
            
            res_logs = supabase.table("historico_bot").select("created_at, operacao").order("id", desc=False).execute()
            for item in res_logs.data:
                estado['historico'].append({
                    'Data/Hora': datetime.strptime(item['created_at'][:19], '%Y-%m-%dT%H:%M:%S').strftime('%d/%m/%Y %H:%M:%S'),
                    'Texto Visual': item['operacao']
                })
        except: pass
    return estado

def salvar_estado_banco():
    if supabase:
        try:
            dados = {
                "saldo_usdt": st.session_state.saldo_usdt,
                "bot_ativo": st.session_state.bot_ativo,
                "ativos_json": st.session_state.ativos
            }
            supabase.table("estado_bot").insert(dados).execute()
        except: pass

if 'inicializado' not in st.session_state:
    db_estado = carregar_estado_banco()
    st.session_state.saldo_usdt = db_estado['saldo_usdt']
    st.session_state.bot_ativo = db_estado['bot_ativo']
    st.session_state.historico = db_estado['historico']
    st.session_state.ativos = db_estado['ativos']
    st.session_state.historico_precos = []
    st.session_state.inicializado = True

def guardar_log(msg):
    if supabase:
        try:
            supabase.table("historico_bot").insert({"operacao": msg}).execute()
            res = supabase.table("historico_bot").select("id").order("id", desc=True).execute()
            if len(res.data) > 50:
                supabase.table("historico_bot").delete().lt("id", res.data[-1]["id"]).execute()
        except: pass

@st.cache_data(ttl=12)
def analisar_dados_mercado(par):
    try:
        ex = ccxt.binance()
        velas = ex.fetch_ohlcv(par, timeframe='1m', limit=30)
        df = pd.DataFrame(velas, columns=['t', 'o', 'h', 'l', 'c', 'v'])
        df['sma20'] = df['c'].rolling(window=20).mean()
        var_m = ((df['h'] - df['l']) / df['l']).mean() * 100
        return max(0.04, round(var_m * 0.4, 2)), max(0.08, round(var_m * 0.9, 2)), df['sma20'].iloc[-1]
    except: 
        return (0.08, 0.18, None) if par == 'BTC/USDT' else (0.12, 0.25, None)

@st.cache_data(ttl=2)
def pegar_precos_binance():
    try:
        ex = ccxt.binance()
        return ex.fetch_ticker('BTC/USDT')['last'], ex.fetch_ticker('ETH/USDT')['last']
    except: return None, None

p_btc, p_eth = pegar_precos_binance()
if p_btc: st.session_state.ativos['BTC/USDT']['last_p'] = p_btc
if p_eth: st.session_state.ativos['ETH/USDT']['last_p'] = p_eth

sma_tendencia = {}
if st.session_state.bot_ativo:
    for par in ['BTC/USDT', 'ETH/USDT']:
        q, l, s = analisar_dados_mercado(par)
        st.session_state.ativos[par]['queda_ia'] = q
        st.session_state.ativos[par]['lucro_ia'] = l
        sma_tendencia[par] = s

st.session_state.historico_precos.append({'hora': datetime.now().strftime('%H:%M:%S'), 'preco': st.session_state.ativos['BTC/USDT']['last_p']})
if len(st.session_state.historico_precos) > 20: st.session_state.historico_precos.pop(0)

st.markdown(f"""
    <style>
    header, [data-testid="stHeader"] {{ visibility: hidden; height: 0px !important; background: transparent !important; }}
    footer {{ visibility: hidden; }}
    .block-container {{ padding-top: 2rem !important; padding-bottom: 0rem !important; }}
    .stApp {{ background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
    h1 {{ color: #d4af37 !important; text-align: left; font-size: 2.2rem; font-weight: 700; margin-bottom: 15px; margin-top: -10px; }}
    h3 {{ color: #e1b12c !important; font-size: 1.1rem; font-weight: 600; margin-top: 10px; margin-bottom: 10px; }}
    div.stButton > button:first-child {{
        background-color: {"#10b981" if st.session_state.bot_ativo else "#ef4444"} !important; color: white !important; border: none !important;
        padding: 8px 20px !important; font-size: 13px !important; font-weight: 600 !important;
        border-radius: 4px !important; width: auto !important; transition: all 0.2s ease !important; margin-bottom: 10px;
    }}
    div[data-testid="stDownloadButton"] > button {{
        background-color: #161b22 !important; color: #d4af37 !important; 
        border: 1px solid #30363d !important; padding: 6px 14px !important; 
        font-size: 12px !important; font-weight: 600 !important; border-radius: 4px !important; width: 100% !important;
    }}
    .metric-container {{ display: flex; gap: 12px; margin-bottom: 10px; }}
    .metric-card {{ background-color: #161b22; border: 1px solid #30363d; padding: 10px 14px; border-radius: 6px; flex: 1; text-align: left; }}
    .metric-title {{ color: #8b949e; font-size: 0.70rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }}
    .metric-value {{ color: #f0f6fc; font-size: 1.25rem; font-weight: 600; }}
    .ia-banner {{ background-color: #1c1912; border-left: 3px solid #d4af37; padding: 10px 14px; border-radius: 4px; color: #e1b12c; font-size: 0.82rem; font-weight: 500; margin-bottom: 10px; }}
    .log-box {{ background-color: #161b22; border: 1px solid #30363d; padding: 8px 14px; border-radius: 6px; color: #8b949e; font-size: 0.82rem; margin-bottom: 6px; font-family: monospace; }}
    .log-box-buy {{ border-left: 3px solid #10b981; color: #f0f6fc; }}
    .log-box-sell {{ border-left: 3px solid #d4af37; color: #f0f6fc; }}
    </style>
""", unsafe_allow_html=True)

st.title("SARA_FIREBOLT")
txt_btn = "🟢 RADAR MULTI-ATIVO ATIVO" if st.session_state.bot_ativo else "🔴 RADAR MULTI-ATIVO OFFLINE"
if st.button(txt_btn):
    st.session_state.bot_ativo = not st.session_state.bot_ativo
    if st.session_state.bot_ativo:
        for p in st.session_state.ativos:
            st.session_state.ativos[p]['ref'] = st.session_state.ativos[p]['last_p']
            st.session_state.ativos[p]['ordens'] = 0
            st.session_state.ativos[p]['saldo'] = 0.0
            st.session_state.ativos[p]['pm'] = 0.0
            st.session_state.ativos[p]['topo'] = 0.0
    salvar_estado_banco()
    st.rerun()

c_btc = st.session_state.ativos['BTC/USDT']
c_eth = st.session_state.ativos['ETH/US传统'] if 'ETH/US传统' in st.session_state.ativos else st.session_state.ativos['ETH/USDT']
exp_btc = f"{c_btc['saldo']:.4f} BTC (Pm: ${c_btc['pm']:,.2f})" if c_btc['saldo'] > 0 else "0.0000"
exp_eth = f"{c_eth['saldo']:.3f} ETH (Pm: ${c_eth['pm']:,.2f})" if c_eth['saldo'] > 0 else "0.0000"

patrimonio_total_live = st.session_state.saldo_usdt + (c_btc['saldo'] * c_btc['last_p']) + (c_eth['saldo'] * c_eth['last_p'])

st.markdown(f"""
    <div class='metric-container'>
        <div class='metric-card' style='border-color: #d4af37;'>
            <div class='metric-title' style='color: #d4af37;'>💎 Patrimônio Total</div>
            <div class='metric-value' style='color: #d4af37;'>${patrimonio_total_live:,.2f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Disponível USDT</div>
            <div class='metric-value'>${st.session_state.saldo_usdt:,.2f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Posição Bitcoin</div>
            <div class='metric-value'>{exp_btc} | Pr: ${c_btc['last_p']:,.2f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Posição Ethereum</div>
            <div class='metric-value'>{exp_eth} | Pr: ${c_eth['last_p']:,.2f}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

if st.session_state.bot_ativo:
    st.markdown(f"<div class='ia-banner'>✨ MONITORAMENTO DUAL COORDENADO | Alvos IA BTC: Queda -{c_btc['queda_ia']}% / Lucro +{c_btc['lucro_ia']}% [{c_btc['ordens']}/3] | Alvos IA ETH: Queda -{c_eth['queda_ia']}% / Lucro +{c_eth['lucro_ia']}% [{c_eth['ordens']}/3]</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='ia-banner' style='background-color: #211818; border-left-color: #ef4444; color: #f87171;'>💤 SISTEMA EM MODO OCIOSO.</div>", unsafe_allow_html=True)

df_p = pd.DataFrame(st.session_state.historico_precos)
if not df_p.empty:
    fig = go.Figure(go.Scatter(x=df_p['hora'], y=df_p['preco'], mode='lines', line=dict(color='#d4af37', width=1)))
    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=0, b=0), height=15, xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

if st.session_state.bot_ativo:
    for par in ['BTC/USDT', 'ETH/USDT']:
        data = st.session_state.ativos[par]
        p_atual = data['last_p']
        sma = sma_tendencia.get(par, None)
        
        if data['ordens'] < 3:
            diff_c = ((p_atual - data['ref']) / data['ref']) * 100 if data['ref'] > 0 else 0.0
            tend_ok = True if (not sma or p_atual >= sma) else False
            
            if (data['ordens'] == 0 and tend_ok) or (diff_c <= -data['queda_ia'] and tend_ok):
                fatia = 1666.66 if st.session_state.saldo_usdt >= 1666.66 else st.session_state.saldo_usdt
                if fatia > 20:
                    st.session_state.ativos[par]['saldo'] += (fatia / p_atual)
                    st.session_state.saldo_usdt -= fatia
                    st.session_state.ativos[par]['pm'] = fatia / (fatia / p_atual) if data['saldo'] == 0 else p_atual
                    st.session_state.ativos[par]['ordens'] += 1
                    st.session_state.ativos[par]['ref'] = p_atual
                    st.session_state.ativos[par]['topo'] = p_atual
                    
                    t_stamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                    msg_txt = f"🛒 RADAR DUAL [{par}]: Alocação {st.session_state.ativos[par]['ordens']}/3 executada a ${p_atual:,.2f}."
                    st.session_state.historico.append({'Data/Hora': t_stamp, 'Texto Visual': msg_txt})
                    guardar_log(msg_txt)
                    salvar_estado_banco()
                    st.toast(f"⚡ Posição fracionada em {par} montada.")
                    st.rerun()

        if data['saldo'] > 0:
            lucro_p = ((p_atual - data['pm']) / data['pm']) * 100
            if p_atual > data['topo']: st.session_state.ativos[par]['topo'] = p_atual
            rec_topo = ((data['topo'] - p_atual) / data['topo']) * 100
            
            if lucro_p >= data['lucro_ia'] and rec_topo >= 0.04:
                val_liq = data['saldo'] * p_atual
                st.session_state.saldo_usdt += val_liq
                
                t_stamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                msg_txt = f"💰 LIQUIDAÇÃO QUANTUM [{par}]: Total vendido a ${p_atual:,.2f} | Lucro: +{lucro_p:.2f}%"
                st.session_state.historico.append({'Data/Hora': t_stamp, 'Texto Visual': msg_txt})
                guardar_log(msg_txt)
                
                st.session_state.ativos[par]['saldo'] = 0.0
                st.session_state.ativos[par]['pm'] = 0.0
                st.session_state.ativos[par]['ordens'] = 0
                st.session_state.ativos[par]['ref'] = p_atual
                st.session_state.ativos[par]['topo'] = 0.0
                salvar_estado_banco()
                st.toast(f"👑 {par} liquidado no topo!")
                st.rerun()

def gerar_pdf_sara(dados_historico, s_usdt, s_btc, p_btc, s_eth, p_eth):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#d4af37'), spaceAfter=15)
    body_style = ParagraphStyle('Body', parent=styles['BodyText'], fontSize=10, textColor=colors.HexColor('#333333'), leading=14)
    table_hdr = ParagraphStyle('TH', fontSize=9, fontName='Helvetica-Bold', textColor=colors.white)
    table_cell = ParagraphStyle('TC', fontSize=8.5, fontName='Helvetica', textColor=colors.HexColor('#222222'))
    
    val_btc, val_eth = s_btc * p_btc, s_eth * p_eth
    story = [
        Paragraph("RELATÓRIO DE AUDITORIA QUANTITATIVA — SARA_FIREBOLT", title_style),
        Paragraph(f"<b>DATA DE EMISSÃO:</b> {datetime.now().strftime('%d/%m/%Y')} | <b>STATUS:</b> Operacional Ativo", body_style),
        Spacer(1, 12),
        Paragraph(f"• <b>PATRIMÔNIO TOTAL ESTIMADO:</b> ${s_usdt+val_btc+val_eth:,.2f} USD", body_style),
        Paragraph(f"• <b>Garantia Disponível:</b> ${s_usdt:,.2f} USDT", body_style),
        Paragraph(f"• <b>Alocação em Bitcoin (BTC):</b> {s_btc:.4f} BTC (~ ${val_btc:,.2f} USD)", body_style),
        Paragraph(f"• <b>Alocação em Ethereum (ETH):</b> {s_eth:.3f} ETH (~ ${val_eth:,.2f} USD)", body_style),
        Spacer(1, 15), Table([[Paragraph("Data / Hora", table_hdr), Paragraph("Registro", table_hdr)]] + [[Paragraph(r['Data/Hora'], table_cell), Paragraph(r['Texto Visual'], table_cell)] for r in reversed(dados_historico)], colWidths=[110, 470], style=[('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1c1912')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc'))])
    ]
    doc.build(story)
    buffer.seek(0)
    return buffer

if st.session_state.historico:
    c_csv, c_pdf = st.columns(2)
    with c_csv:
        st.download_button(label="📥 Baixar Tabela (CSV)", data=pd.DataFrame(st.session_state.historico).to_csv(index=False, sep=';').encode('utf-8-sig'), file_name="sara_firebolt_financial.csv", mime='text/csv')
    with c_pdf:
        st.download_button(label="📄 Baixar Relatório (PDF)", data=gerar_pdf_sara(st.session_state.historico, st.session_state.saldo_usdt, c_btc['saldo'], c_btc['last_p'], c_eth['saldo'], c_eth['last_p']), file_name="sara_firebolt_report.pdf", mime='application/pdf')
    st.write("")
    for item in reversed(st.session_state.historico):
        st.markdown(f"<div class='log-box { 'log-box-buy' if '🛒' in item['Texto Visual'] else 'log-box-sell' }'>{item['Texto Visual']}</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='log-box'>*Aguardando flutuação matemática.*</div>", unsafe_allow_html=True)

time.sleep(2)
if st.session_state.bot_ativo: st.rerun()

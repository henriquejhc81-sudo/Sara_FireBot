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

if 'saldo_usdt' not in st.session_state:
    st.session_state.saldo_usdt = 10000.0
    st.session_state.historico = []  
    st.session_state.bot_ativo = False
    st.session_state.historico_precos = []
    st.session_state.ativos = {
        'BTC/USDT': {'saldo': 0.0, 'pm': 0.0, 'ordens': 0, 'ref': 0.0, 'topo': 0.0, 'queda_ia': 0.08, 'lucro_ia': 0.18, 'last_p': 64188.0},
        'ETH/USDT': {'saldo': 0.0, 'pm': 0.0, 'ordens': 0, 'ref': 0.0, 'topo': 0.0, 'queda_ia': 0.12, 'lucro_ia': 0.25, 'last_p': 3450.0}
    }

URL = st.secrets.get("SUPABASE_URL", "")
KEY = st.secrets.get("SUPABASE_KEY", "")
supabase = create_client(URL, KEY) if URL and KEY else None

# Sincronização Inicial Inteligente com o Supabase
if supabase and not st.session_state.historico:
    try:
        res = supabase.table("historico_bot").select("created_at, operacao").order("id", desc=False).execute()
        for item in res.data:
            st.session_state.historico.append({
                'Data/Hora': datetime.strptime(item['created_at'][:19], '%Y-%m-%dT%H:%M:%S').strftime('%d/%m/%Y %H:%M:%S'),
                'Texto Visual': item['operacao']
            })
    except: pass

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
    div.stButton > button:first-child:hover {{ background-color: {"#059669" if st.session_state.bot_ativo else "#dc2626"} !important; }}
    .metric-container {{ display: flex; gap: 15px; margin-bottom: 10px; }}
    .metric-card {{ background-color: #161b22; border: 1px solid #30363d; padding: 12px 18px; border-radius: 6px; flex: 1; text-align: left; }}
    .metric-title {{ color: #8b949e; font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }}
    .metric-value {{ color: #f0f6fc; font-size: 1.35rem; font-weight: 600; }}
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
    st.rerun()

c_btc = st.session_state.ativos['BTC/USDT']
c_eth = st.session_state.ativos['ETH/USDT']
exp_btc = f"{c_btc['saldo']:.4f} BTC (Pm: ${c_btc['pm']:,.2f})" if c_btc['saldo'] > 0 else "0.0000"
exp_eth = f"{c_eth['saldo']:.3f} ETH (Pm: ${c_eth['pm']:,.2f})" if c_eth['saldo'] > 0 else "0.0000"

st.markdown(f"""
    <div class='metric-container'>
        <div class='metric-card'>
            <div class='metric-title'>Disponível USDT</div>
            <div class='metric-value'>${st.session_state.saldo_usdt:,.2f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Posição Bitcoin (BTC)</div>
            <div class='metric-value'>{exp_btc} | Pr: ${c_btc['last_p']:,.2f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Posição Ethereum (ETH)</div>
            <div class='metric-value'>{exp_eth} | Pr: ${c_eth['last_p']:,.2f}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

if st.session_state.bot_ativo:
    st.markdown(f"<div class='ia-banner'>✨ MONITORAMENTO DUAL COORDENADO | Alvos IA BTC: Queda -{c_btc['queda_ia']}% / Lucro +{c_btc['lucro_ia']}% [{c_btc['ordens']}/3] | Alvos IA ETH: Queda -{c_eth['queda_ia']}% / Lucro +{c_eth['lucro_ia']}% [{c_eth['ordens']}/3]</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='ia-banner' style='background-color: #211818; border-left-color: #ef4444; color: #f87171;'>💤 SISTEMA EM MODO OCIOSO. Alvos institucionais e leitura quântica dual desativados.</div>", unsafe_allow_html=True)

# Lógica Interna Multi-Ativo
if st.session_state.bot_ativo:
    for par in ['BTC/USDT', 'ETH/USDT']:
        data = st.session_state.ativos[par]
        p_atual = data['last_p']
        sma = sma_tendencia.get(par, None)
        
        if data['ordens'] < 3:
            diff_c = ((p_atual - data['ref']) / data['ref']) * 100
            tend_ok = True if (not sma or p_atual >= sma) else False
            
            if (data['ordens'] == 0 and tend_ok) or (diff_c <= -data['queda_ia'] and tend_ok):
                fatia = 1666.66 if st.session_state.saldo_usdt >= 1666.66 else st.session_state.saldo_usdt
                if fatia > 20:
                    qtd_a = fatia / p_atual
                    custo_t = (data['saldo'] * data['pm']) + fatia
                    st.session_state.ativos[par]['saldo'] += qtd_a
                    st.session_state.saldo_usdt -= fatia
                    st.session_state.ativos[par]['pm'] = custo_t / st.session_state.ativos[par]['saldo']
                    st.session_state.ativos[par]['ordens'] += 1
                    st.session_state.ativos[par]['ref'] = p_atual
                    st.session_state.ativos[par]['topo'] = p_atual
                    
                    t_stamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                    msg_txt = f"🛒 RADAR DUAL [{par}]: Alocação {st.session_state.ativos[par]['ordens']}/3 executada a ${p_atual:,.2f}. Pm: ${st.session_state.ativos[par]['pm']:,.2f}"
                    st.session_state.historico.append({'Data/Hora': t_stamp, 'Texto Visual': msg_txt})
                    guardar_log(msg_txt)
                    st.toast(f"⚡ Posição fracionada em {par} montada.")
                    st.rerun()

        if data['saldo'] > 0:
            lucro_p = ((p_atual - data['pm']) / data['pm']) * 100
            if p_atual > data['topo']: st.session_state.ativos[par]['topo'] = p_atual
            rec_topo = ((data['topo'] - p_atual) / data['topo']) * 100
            
            if lucro_p >= data['lucro_ia'] and rec_topo >= 0.04:
                val_liq = data['saldo'] * p_atual
                luc_liq = val_liq - (data['ordens'] * 1666.66)
                st.session_state.saldo_usdt += val_liq
                
                t_stamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                msg_txt = f"💰 LIQUIDAÇÃO QUANTUM [{par}]: Total vendido a ${p_atual:,.2f} | Surfou lucro de +{lucro_p:.2f}% (Retorno Líquido: ${luc_liq:,.2f})"
                st.session_state.historico.append({'Data/Hora': t_stamp, 'Texto Visual': msg_txt})
                guardar_log(msg_txt)
                
                st.session_state.ativos[par]['saldo'] = 0.0
                st.session_state.ativos[par]['pm'] = 0.0
                st.session_state.ativos[par]['ordens'] = 0
                st.session_state.ativos[par]['ref'] = p_atual
                st.session_state.ativos[par]['topo'] = 0.0
                st.toast(f"👑 {par} liquidado no topo!")
                st.rerun()

# --- FUNÇÃO GERADORA DE PDF HARVARD-STYLE ---
def gerar_pdf_harvard(dados_historico):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#d4af37'), spaceAfter=15)
    body_style = ParagraphStyle('Body', parent=styles['BodyText'], fontSize=10, textColor=colors.HexColor('#333333'), leading=14)
    table_hdr = ParagraphStyle('TH', fontSize=9, fontName='Helvetica-Bold', textColor=colors.white)
    table_cell = ParagraphStyle('TC', fontSize=8.5, fontName='Helvetica', textColor=colors.HexColor('#222222'))
    
    story = [
        Paragraph("HARVARD QUANTITATIVE TRADING REPORT", title_style),
        Paragraph(f"<b>PROJECT:</b> SARA_FIREBOLT | <b>DATE:</b> {datetime.now().strftime('%d/%m/%Y')} | <b>STATUS:</b> Active", body_style),
        Spacer(1, 15),
        Paragraph("<b>EXECUTIVE SUMMARY:</b> This document contains the audit trail of assets allocated by the quantitative multi-asset engine.", body_style),
        Spacer(1, 15)
    ]
    
    table_data = [[Paragraph("Timestamp", table_hdr), Paragraph("Operation Details", table_hdr)]]
    for row in reversed(dados_historico):
        table_data.append([Paragraph(row['Data/Hora'], table_cell), Paragraph(row['Texto Visual'], table_cell)])
        
    t = Table(table_data, colWidths=[110, 440])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1c1912')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- SEÇÃO VISUAL: GRÁFICOS DE RENTABILIDADE & EXPORTAÇÕES ---
st.markdown("### Histórico de Caça")

if st.session_state.historico:
    c_csv, c_pdf = st.columns(2)
    with c_csv:
        df_logs = pd.DataFrame(st.session_state.historico)
        csv_d = df_logs.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button(label="📥 Baixar Tabela de Auditoria (CSV)", data=csv_d, file_name="sara_firebolt_financial.csv", mime='text/csv')
    with c_pdf:
        pdf_data = gerar_pdf_harvard(st.session_state.historico)
        st.download_button(label="📄 Baixar Relatório Harvard (PDF)", data=pdf_data, file_name="sara_firebolt_report.pdf", mime='application/pdf')
        
    st.write("")
    for item in reversed(st.session_state.historico):
        c_cor = "log-box-buy" if "🛒" in item['Texto Visual'] else "log-box-sell"
        st.markdown(f"<div class='log-box {c_cor}'>{item['Texto Visual']}</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='log-box'>*Nenhuma operação realizada pelo algoritmo matemático nesta sessão.*</div>", unsafe_allow_html=True)

time.sleep(2)
if st.session_state.bot_ativo: st.rerun()

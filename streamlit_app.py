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
            'BTC/USDT': {'saldo': 0.0, 'pm': 0.0, 'ordens': 0, 'ref': 0.0, 'topo': 0.0, 'queda_ia': 0.15, 'lucro_ia': 0.30, 'last_p': 64188.0},
            'ETH/USDT': {'saldo': 0.0, 'pm': 0.0, 'ordens': 0, 'ref': 0.0, 'topo': 0.0, 'queda_ia': 0.20, 'lucro_ia': 0.35, 'last_p': 3450.0},
            'SOL/USDT': {'saldo': 0.0, 'pm': 0.0, 'ordens': 0, 'ref': 0.0, 'topo': 0.0, 'queda_ia': 0.25, 'lucro_ia': 0.40, 'last_p': 160.0}
        }
    }
    if supabase:
        try:
            res = supabase.table("estado_bot").select("*").order("id", desc=True).limit(1).execute()
            if res.data:
                db = res.data[0]
                estado['saldo_usdt'] = db['saldo_usdt']
                estado['bot_ativo'] = db['bot_ativo']
                
                db_ativos = db['ativos_json']
                if 'SOL/USDT' not in db_ativos:
                    db_ativos['SOL/USDT'] = {'saldo': 0.0, 'pm': 0.0, 'ordens': 0, 'ref': 0.0, 'topo': 0.0, 'queda_ia': 0.25, 'lucro_ia': 0.40, 'last_p': 160.0}
                estado['ativos'] = db_ativos
            
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
        ex = ccxt.kucoin({'enableRateLimit': True})
        velas = ex.fetch_ohlcv(par, timeframe='1m', limit=30)
        df = pd.DataFrame(velas, columns=['t', 'o', 'h', 'l', 'c', 'v'])
        df['sma20'] = df['c'].rolling(window=20).mean()
        var_m = ((df['h'] - df['l']) / df['l']).mean() * 100
        return max(0.04, round(var_m * 0.4, 2)), max(0.08, round(var_m * 0.9, 2)), df['sma20'].iloc[-1]
    except: 
        if par == 'BTC/USDT': return (0.15, 0.30, None)
        elif par == 'ETH/USDT': return (0.20, 0.35, None)
        else: return (0.25, 0.40, None) 

@st.cache_data(ttl=2)
def pegar_precos_binance():
    try:
        ex = ccxt.kucoin()
        return ex.fetch_ticker('BTC/USDT')['last'], ex.fetch_ticker('ETH/USDT')['last'], ex.fetch_ticker('SOL/USDT')['last']
    except: return None, None, None

p_btc, p_eth, p_sol = pegar_precos_binance()
if p_btc: st.session_state.ativos['BTC/USDT']['last_p'] = p_btc
if p_eth: st.session_state.ativos['ETH/USDT']['last_p'] = p_eth
if p_sol: st.session_state.ativos['SOL/USDT']['last_p'] = p_sol

sma_tendencia = {}
if st.session_state.bot_ativo:
    for par in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        q, l, s = analisar_dados_mercado(par)
        # st.session_state.ativos[par]['queda_ia'] = q  # Removido para forçar o alvo fixo conservador
        # st.session_state.ativos[par]['lucro_ia'] = l  # Removido para forçar o alvo fixo conservador
        sma_tendencia[par] = s

st.session_state.historico_precos.append({'hora': datetime.now().strftime('%H:%M:%S'), 'preco': st.session_state.ativos['BTC/USDT']['last_p']})
if len(st.session_state.historico_precos) > 20: st.session_state.historico_precos.pop(0)

st.markdown(f"""
    <style>
    header, [data-testid="stHeader"] {{ visibility: hidden; height: 0px !important; background: transparent !important; }}
    footer {{ visibility: hidden; }}
    .stSpinner {{ display: none !important; }} 
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
    .metric-container {{ display: flex; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }}
    .metric-card {{ background-color: #161b22; border: 1px solid #30363d; padding: 10px 14px; border-radius: 6px; flex: 1; text-align: left; min-width: 200px; }}
    .metric-title {{ color: #8b949e; font-size: 0.70rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }}
    .metric-value {{ color: #f0f6fc; font-size: 1.20rem; font-weight: 600; }}
    .ia-banner {{ background-color: #1c1912; border-left: 3px solid #d4af37; padding: 10px 14px; border-radius: 4px; color: #e1b12c; font-size: 0.82rem; font-weight: 500; margin-bottom: 10px; }}
    .log-box {{ background-color: #161b22; border: 1px solid #30363d; padding: 8px 14px; border-radius: 6px; color: #8b949e; font-size: 0.82rem; margin-bottom: 6px; font-family: monospace; }}
    .log-box-buy {{ border-left: 3px solid #10b981; color: #f0f6fc; }}
    .log-box-sell {{ border-left: 3px solid #d4af37; color: #f0f6fc; }}
    </style>
""", unsafe_allow_html=True)

st.title("SARA_FIREBOLT")

txt_btn = "🟢 RADAR MULTI-ATIVO ATIVO" if st.session_state.bot_ativo else "🔴 RADAR MULTI-ATIVO OFFLINE"
if st.button(txt_btn):
    # CORREÇÃO CRÍTICA: Apenas inverte o estado. Remoção do bloco que zerava a memória do bot.
    st.session_state.bot_ativo = not st.session_state.bot_ativo
    
    # Se estiver religando, atualizamos o "ref" (Preço de Referência) para não comprar errado baseado num preço velho.
    if st.session_state.bot_ativo:
        for p in st.session_state.ativos:
            st.session_state.ativos[p]['ref'] = st.session_state.ativos[p]['last_p']
    
    salvar_estado_banco()
    st.rerun()

c_btc = st.session_state.ativos['BTC/USDT']
c_eth = st.session_state.ativos['ETH/USDT'] 
c_sol = st.session_state.ativos['SOL/USDT'] 

exp_btc = f"{c_btc['saldo']:.4f} BTC" if c_btc['saldo'] > 0 else "0.0000"
exp_eth = f"{c_eth['saldo']:.3f} ETH" if c_eth['saldo'] > 0 else "0.0000"
exp_sol = f"{c_sol['saldo']:.2f} SOL" if c_sol['saldo'] > 0 else "0.00"

patrimonio_total_live = st.session_state.saldo_usdt + (c_btc['saldo'] * c_btc['last_p']) + (c_eth['saldo'] * c_eth['last_p']) + (c_sol['saldo'] * c_sol['last_p'])

st.markdown(f"""
    <div class='metric-container'>
        <div class='metric-card' style='border-color: #d4af37; flex: 1.2;'>
            <div class='metric-title' style='color: #d4af37;'>💎 Patrimônio / Caixa</div>
            <div class='metric-value' style='color: #d4af37;'>${patrimonio_total_live:,.2f} | ${st.session_state.saldo_usdt:,.2f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Bitcoin</div>
            <div class='metric-value'>{exp_btc} | ${c_btc['last_p']:,.2f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Ethereum</div>
            <div class='metric-value'>{exp_eth} | ${c_eth['last_p']:,.2f}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-title'>Solana</div>
            <div class='metric-value'>{exp_sol} | ${c_sol['last_p']:,.2f}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

if st.session_state.bot_ativo:
    st.markdown(f"<div class='ia-banner'>✨ MONITORAMENTO TRIPLO INSTITUCIONAL | BTC: Queda -{c_btc['queda_ia']}% [{c_btc['ordens']}/3] | ETH: Queda -{c_eth['queda_ia']}% [{c_eth['ordens']}/3] | SOL: Queda -{c_sol['queda_ia']}% [{c_sol['ordens']}/3]</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='ia-banner' style='background-color: #211818; border-left-color: #ef4444; color: #f87171;'>💤 SISTEMA EM MODO OCIOSO. Memória de operações retida na nuvem.</div>", unsafe_allow_html=True)

df_p = pd.DataFrame(st.session_state.historico_precos)
if not df_p.empty:
    fig = go.Figure(go.Scatter(x=df_p['hora'], y=df_p['preco'], mode='lines', line=dict(color='#d4af37', width=1)))
    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=0, b=0), height=15, xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

if st.session_state.bot_ativo:
    for par in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        data = st.session_state.ativos[par]
        p_atual = data['last_p']
        sma = sma_tendencia.get(par, None)
        
        # LÓGICA DE COMPRA
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
                    msg_txt = f"🛒 RADAR MULTI [{par}]: Alocação {st.session_state.ativos[par]['ordens']}/3 executada a ${p_atual:,.2f}."
                    st.session_state.historico.append({'Data/Hora': t_stamp, 'Texto Visual': msg_txt})
                    guardar_log(msg_txt)
                    salvar_estado_banco()
                    st.toast(f"⚡ Posição montada em {par}.")
                    st.rerun()
                    
        # LÓGICA DE VENDA (Com Trailing Stop)
        if data['saldo'] > 0:
            lucro_p = ((p_atual - data['pm']) / data['pm']) * 100
            
            if p_atual > data['topo']: 
                st.session_state.ativos[par]['topo'] = p_atual
                
            rec_topo = ((data['topo'] - p_atual) / data['topo']) * 100
            
            trailing_stop_acionado = lucro_p > 0.10 and rec_topo >= 0.20
            
            if (lucro_p >= data['lucro_ia'] and rec_topo >= 0.04) or trailing_stop_acionado:
                val_liq = data['saldo'] * p_atual
                st.session_state.saldo_usdt += val_liq
                
                tipo_venda = "TRAILING STOP" if trailing_stop_acionado else "QUANTUM"
                t_stamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                msg_txt = f"💰 LIQUIDAÇÃO {tipo_venda} [{par}]: Vendido a ${p_atual:,.2f} | Lucro: +{lucro_p:.2f}%"
                st.session_state.historico.append({'Data/Hora': t_stamp, 'Texto Visual': msg_txt})
                guardar_log(msg_txt)
                
                st.session_state.ativos[par]['saldo'] = 0.0
                st.session_state.ativos[par]['pm'] = 0.0
                st.session_state.ativos[par]['ordens'] = 0
                st.session_state.ativos[par]['ref'] = p_atual
                st.session_state.ativos[par]['topo'] = 0.0
                salvar_estado_banco()
                st.toast(f"👑 {par} liquidado com sucesso!")
                st.rerun()

# EVOLUÇÃO: Relatório Forense e Institucional de Alta Precisão
def gerar_pdf_sara(dados_historico, s_usdt, c_btc, c_eth, c_sol):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1c1912'), alignment=1, spaceAfter=10)
    sub_title_style = ParagraphStyle('H2', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#666666'), alignment=1, spaceAfter=20)
    header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#d4af37'), spaceAfter=8)
    body_style = ParagraphStyle('Body', parent=styles['BodyText'], fontSize=9, textColor=colors.HexColor('#333333'), leading=14)
    table_hdr = ParagraphStyle('TH', fontSize=8.5, fontName='Helvetica-Bold', textColor=colors.white)
    table_cell = ParagraphStyle('TC', fontSize=8, fontName='Helvetica', textColor=colors.HexColor('#222222'))
    
    # Cálculos Forenses
    val_btc = c_btc['saldo'] * c_btc['last_p']
    val_eth = c_eth['saldo'] * c_eth['last_p']
    val_sol = c_sol['saldo'] * c_sol['last_p']
    patrimonio_total = s_usdt + val_btc + val_eth + val_sol
    
    exp_crypto = ((val_btc + val_eth + val_sol) / patrimonio_total) * 100 if patrimonio_total > 0 else 0
    exp_fiat = (s_usdt / patrimonio_total) * 100 if patrimonio_total > 0 else 0
    
    pnl_btc = ((c_btc['last_p'] - c_btc['pm']) / c_btc['pm'] * 100) if c_btc['pm'] > 0 else 0
    pnl_eth = ((c_eth['last_p'] - c_eth['pm']) / c_eth['pm'] * 100) if c_eth['pm'] > 0 else 0
    pnl_sol = ((c_sol['last_p'] - c_sol['pm']) / c_sol['pm'] * 100) if c_sol['pm'] > 0 else 0

    story = [
        Paragraph("<b>RELATÓRIO DE INTELIGÊNCIA FINANCEIRA E EXPOSIÇÃO</b>", title_style),
        Paragraph(f"SARA_FIREBOLT MULTI-ASSET ENGINE | Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", sub_title_style),
        
        Paragraph("<b>1. RESUMO PATRIMONIAL E RISCO DE EXPOSIÇÃO</b>", header_style),
        Paragraph(f"• <b>Net Worth Estimado:</b> ${patrimonio_total:,.2f} USD", body_style),
        Paragraph(f"• <b>Caixa Ocioso (Reserva de Liquidez):</b> ${s_usdt:,.2f} USDT ({exp_fiat:.1f}%)", body_style),
        Paragraph(f"• <b>Capital Exposto em Ativos Variáveis:</b> ${val_btc+val_eth+val_sol:,.2f} USD ({exp_crypto:.1f}%)", body_style),
        Spacer(1, 10),
        
        Paragraph("<b>2. DISTRIBUIÇÃO E PNL NÃO-REALIZADO</b>", header_style),
        Paragraph(f"• <b>[BTC/USDT]</b> {c_btc['saldo']:.4f} BTC | Pm: ${c_btc['pm']:,.2f} | Atual: ${c_btc['last_p']:,.2f} | <b>PNL: {pnl_btc:+.2f}%</b>", body_style),
        Paragraph(f"• <b>[ETH/USDT]</b> {c_eth['saldo']:.4f} ETH | Pm: ${c_eth['pm']:,.2f} | Atual: ${c_eth['last_p']:,.2f} | <b>PNL: {pnl_eth:+.2f}%</b>", body_style),
        Paragraph(f"• <b>[SOL/USDT]</b> {c_sol['saldo']:.2f} SOL | Pm: ${c_sol['pm']:,.2f} | Atual: ${c_sol['last_p']:,.2f} | <b>PNL: {pnl_sol:+.2f}%</b>", body_style),
        Spacer(1, 15),
        
        Paragraph("<b>3. REGISTRO DE AUDITORIA DE TRANSAÇÕES</b>", header_style),
    ]
    
    if dados_historico:
        tabela_dados = [[Paragraph("Data / Hora", table_hdr), Paragraph("Descrição do Evento", table_hdr)]] 
        tabela_dados += [[Paragraph(r['Data/Hora'], table_cell), Paragraph(r['Texto Visual'], table_cell)] for r in reversed(dados_historico)]
        tabela_pdf = Table(tabela_dados, colWidths=[110, 420], repeatRows=1)
        tabela_pdf.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#d4af37')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#060913')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        story.append(tabela_pdf)
    else:
        story.append(Paragraph("<i>Nenhuma transação registrada no escopo atual.</i>", body_style))
        
    doc.build(story)
    buffer.seek(0)
    return buffer

if st.session_state.historico:
    c_csv, c_pdf = st.columns(2)
    with c_csv:
        st.download_button(label="📥 Baixar Tabela (CSV)", data=pd.DataFrame(st.session_state.historico).to_csv(index=False, sep=';').encode('utf-8-sig'), file_name="sara_firebolt_financial.csv", mime='text/csv')
    with c_pdf:
        st.download_button(label="📄 Baixar Relatório Forense (PDF)", data=gerar_pdf_sara(st.session_state.historico, st.session_state.saldo_usdt, c_btc, c_eth, c_sol), file_name="sara_firebolt_forensic_report.pdf", mime='application/pdf')
    st.write("")
    for item in reversed(st.session_state.historico):
        st.markdown(f"<div class='log-box { 'log-box-buy' if '🛒' in item['Texto Visual'] else 'log-box-sell' }'>{item['Texto Visual']}</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='log-box'>*Aguardando flutuação matemática.*</div>", unsafe_allow_html=True)

time.sleep(2)
if st.session_state.bot_ativo: st.rerun()

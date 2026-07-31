import streamlit as st
import pandas as pd
import pytz
from datetime import datetime
from supabase import create_client

# ==========================================
# 📊 TERMINAL DO INVESTIDOR // AUDITORIA B2C
# ==========================================
st.set_page_config(page_title="Terminal de Oportunidades | B2C", layout="wide", initial_sidebar_state="collapsed")
tz_br = pytz.timezone('America/Sao_Paulo')

# ESTILIZAÇÃO CSS
st.markdown("""
    <style>
    .stApp { background-color: #020617; color: #f8fafc; font-family: 'Inter', sans-serif; }
    .header-box { padding: 20px; background: linear-gradient(90deg, #0f172a 0%, #020617 100%); border-left: 5px solid #10b981; border-radius: 6px; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); }
    .title-text { color: #10b981; font-size: 24px; font-weight: 900; letter-spacing: 1px; margin: 0; text-transform: uppercase; }
    .subtitle-text { color: #94a3b8; font-size: 13px; font-family: monospace; margin-top: 5px; }
    .disclaimer { text-align: center; color: #475569; font-size: 11px; margin-top: 40px; font-family: monospace; }
    </style>
""", unsafe_allow_html=True)

# CONEXÃO SUPABASE SEGURA (STREAMLIT CLOUD)
SUPA_URL = st.secrets.get("SUPABASE_URL", "")
SUPA_KEY = st.secrets.get("SUPABASE_KEY", "")
supabase = None
try:
    if SUPA_URL and SUPA_KEY:
        supabase = create_client(SUPA_URL.strip().rstrip('/'), SUPA_KEY.strip())
except Exception as e:
    st.error(f"Erro de conexão: {e}")

@st.cache_resource(ttl=15)
def carregar_dados_ecossistema():
    dados = {"mestre": {}, "karv": {}, "ultima_att": "Aguardando..."}
    if supabase:
        try:
            res_m = supabase.table('duck_state').select("state").eq('id', 999).execute()
            if res_m.data: dados["mestre"] = res_m.data[0]['state']
            
            res_k = supabase.table('karv_state').select("state").eq('id', 1).execute()
            if res_k.data: dados["karv"] = res_k.data[0]['state']
            
            dados["ultima_att"] = datetime.now(tz_br).strftime('%d/%m/%Y %H:%M:%S')
        except: pass
    return dados

def calcular_indice_confianca(moeda, sinal_mestre, dados_karv):
    confianca = 0
    motivos = []
    
    if sinal_mestre.get('score', 0) >= 75:
        confianca += 40
        motivos.append("Fundamento Técnico")
    
    if sinal_mestre.get('smart_money', False):
        confianca += 25
        motivos.append("Fluxo Institucional")
        
    if sinal_mestre.get('squeeze', False):
        confianca += 15
        motivos.append("Compressão Squeeze")
        
    if dados_karv and moeda in dados_karv.get('portfolio', {}):
        confianca += 15
        motivos.append("Auditoria K-Node")
        
    confianca = min(99, confianca)
    justificativa = " | ".join(motivos) if motivos else "Aguardando alinhamento de fatores."
    
    veredicto = "ALTA PROBABILIDADE" if confianca >= 80 else "MÉDIA PROBABILIDADE" if confianca >= 60 else "OBSERVAÇÃO"
    return confianca, veredicto, justificativa

def aplicar_cores_tabela(row):
    confianca = row['Índice de Confiança (%)']
    if confianca >= 80:
        cor = '#10b981'
    elif confianca >= 60:
        cor = '#f59e0b'
    else:
        cor = '#64748b'
        
    estilos = [''] * len(row)
    idx_confianca = row.index.get_loc('Índice de Confiança (%)')
    idx_veredicto = row.index.get_loc('Veredicto do Algoritmo')
    
    estilos[idx_confianca] = f'color: {cor}; font-weight: bold; font-size: 14px;'
    estilos[idx_veredicto] = f'color: {cor}; font-weight: bold;'
    
    return estilos

# RENDERIZAÇÃO
ecossistema = carregar_dados_ecossistema()

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("""
        <div class="header-box" translate="no">
            <h1 class="title-text">MATRIZ DE OPORTUNIDADES</h1>
            <div class="subtitle-text">MONITORAMENTO DE DADOS ALGORÍTMICOS B2C</div>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 ATUALIZAR MATRIZ", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()
    st.markdown(f"<div style='text-align:center; color:#64748b; font-size:11px; margin-top:5px;'>Última Sincronização:<br>{ecossistema['ultima_att']}</div>", unsafe_allow_html=True)

sinais_mestre = ecossistema.get("mestre", {}).get("sinais", {})
dados_karv = ecossistema.get("karv", {})
dados_tabela = []

if sinais_mestre:
    for moeda, dados_sinal in sinais_mestre.items():
        if not dados_sinal.get('bloqueio_sistemico', False):
            confianca, veredicto, justificativa = calcular_indice_confianca(moeda, dados_sinal, dados_karv)
            if confianca >= 40:
                dados_tabela.append({
                    "Ativo": moeda.replace('/USDT', ''),
                    "Preço Atual": f"${dados_sinal.get('preco_atual', 0.0):.4f}",
                    "Índice de Confiança (%)": confianca,
                    "Veredicto do Algoritmo": veredicto,
                    "Justificativa Base": justificativa
                })

if dados_tabela:
    df = pd.DataFrame(dados_tabela)
    df = df.sort_values(by="Índice de Confiança (%)", ascending=False).reset_index(drop=True)
    df_estilizado = df.style.apply(aplicar_cores_tabela, axis=1)
    
    st.dataframe(df_estilizado, use_container_width=True, hide_index=True, height=400)
else:
    st.info("O mercado está sendo escaneado. O algoritmo não detectou alinhamentos técnicos suficientes neste momento.")

st.markdown("<div class='disclaimer'>AVISO LEGAL: Este sistema fornece análises algorítmicas baseadas em probabilidade matemática. Criptomoedas são ativos de risco. O Índice de Confiança não representa garantia de lucros absolutos.</div>", unsafe_allow_html=True)

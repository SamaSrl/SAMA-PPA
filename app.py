import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Configurazione ottimizzata per mobile e PC
st.set_page_config(page_title="Simulatore FV & PPA Pro", layout="wide")

# --- SISTEMA DI AUTENTICAZIONE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state["password"] == "sama2026": 
        st.session_state.authenticated = True
        del st.session_state["password"]  
    else:
        st.session_state.authenticated = False
        st.error("❌ Password errata!")

if not st.session_state.authenticated:
    st.title("🔒 Accesso Riservato")
    st.text_input("Password:", type="password", key="password", on_change=check_password)
    st.stop() 

# --- TITOLO PRINCIPALE ---
st.title("📊 Business Plan Fotovoltaico in PPA")
st.write("Simulatore avanzato con gestione Diritto di Superficie e calcolo Weekend.")

# --- INPUT DATI (Sidebar per lasciare spazio ai TAB) ---
st.sidebar.header("⚙️ Configurazione Iniziale")

# Organizzazione degli input in Expander nella Sidebar per il mobile
with st.sidebar.expander("📝 1. Consumi ANNUALI Cliente", expanded=True):
    f1_anno = st.number_input("Consumo F1 (kWh/anno)", value=15000, step=1000)
    f2_anno = st.number_input("Consumo F2 (kWh/anno)", value=12000, step=1000)
    f3_anno = st.number_input("Consumo F3 (kWh/anno)", value=10000, step=1000)

with st.sidebar.expander("☀️ 2. Dati Impianto FV", expanded=False):
    kwp = st.number_input("Potenza Impianto (kWp)", value=20.0, step=1.0)
    prod_specifica = st.number_input("Produttività (kWh/kWp)", value=1300, step=50)

with st.sidebar.expander("💶 3. Tariffe (€/kWh)", expanded=False):
    tariffa_cliente_attuale = st.number_input("Tariffa attuale Cliente", value=0.28, step=0.01)
    tariffa_vendita_tua = st.number_input("Tariffa tua vendita (PPA)", value=0.16, step=0.01)
    prezzo_ritiro_dedicato = st.number_input("Prezzo vendita in Rete (RID)", value=0.07, step=0.01)

# --- CREAZIONE DEI TAB RICHIESTI ---
tab_contratto, tab_analisi_annuale, tab_vantaggio_totale = st.tabs([
    "🤝 Accordo & Diritto di Superficie", 
    "📅 Analisi Economica Annuale", 
    "🚀 Vantaggio Totale a Lungo Termine"
])

# --- TAB 1: DIRITTO DI SUPERFICIE ---
with tab_contratto:
    st.subheader("📋 Condizioni del Diritto di Superficie (Affitto Tetto)")
    st.write("Inserisci i dati economici dell'accordo di locazione/diritto di superficie.")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        canone_superficie_anno = st.number_input("Canone Annuale Diritto di Superficie (€/anno)", value=1500, step=100)
    with col_c2:
        durata_contratto = st.number_input("Durata del Diritto di Superficie (Anni)", value=20, step=1)

# --- ELABORAZIONE MATEMATICA (Modello feriale + weekend) ---
ore = np.arange(0, 24)
f1_mese = f1_anno / 12
f2_mese = f2_anno / 12
f3_mese = f3_anno / 12

# 1. Profilo Consumo Giorno Feriale (Lavorativo)
profilo_consumo_feriale = np.zeros(24)
for h in ore:
    if 8 <= h < 19: profilo_consumo_feriale[h] = f1_mese / 21 / 11 # 21 giorni feriali medi al mese
    elif (7 <= h < 8) or (19 <= h < 23): profilo_consumo_feriale[h] = f2_mese / 21 / 5
    else: profilo_consumo_feriale[h] = f3_mese / 21 / 8

# 2. Profilo Consumo Weekend (Attività ridotta al 20%, ma comunque presente)
profilo_consumo_weekend = profilo_consumo_feriale * 0.20

# 3. Profilo Produzione FV (Uguale sia feriale che weekend)
produzione_totale_anno = kwp * prod_specifica
produzione_giorno_medio = produzione_totale_anno / 365
profilo_produzione = np.zeros(24)
for h in ore:
    if 6 <= h <= 18:
        profilo_produzione[h] = (produzione_giorno_medio / 7.5) * np.sin(np.pi * (h - 6) / 12) ** 2

# Incroci Feriali (261 giorni/anno)
autoconsumo_feriale_giorno = np.minimum(profilo_consumo_feriale, profilo_produzione)
immessa_feriale_giorno = np.maximum(0, profilo_produzione - autoconsumo_feriale_giorno)

# Incroci Weekend (104 giorni/anno)
autoconsumo_weekend_giorno = np.minimum(profilo_consumo_weekend, profilo_produzione)
immessa_weekend_giorno = np.maximum(0, profilo_produzione - autoconsumo_weekend_giorno)

# Bilancio Annuale Complessivo
autoconsumo_anno = (np.sum(autoconsumo_feriale_giorno) * 261) + (np.sum(autoconsumo_weekend_giorno) * 104)
immessa_anno = (np.sum(immessa_feriale_giorno) * 261) + (np.sum(immessa_weekend_giorno) * 104)

# Correzione di sicurezza
if autoconsumo_anno > produzione_totale_anno:
    autoconsumo_anno = produzione_totale_anno
    immessa_anno = 0

# --- CALCOLI ECONOMICI ---
# Lato Cliente
risparmio_energetico_cliente_anno = autoconsumo_anno * (tariffa_cliente_attuale - tariffa_vendita_tua)
guadagno_totale_cliente_anno = risparmio_energetico_cliente_anno + canone_superficie_anno

# Lato Tuo (Investitore)
ricavo_da_cliente_anno = autoconsumo_anno * tariffa_vendita_tua
ricavo_da_rete_anno = immessa_anno * prezzo_ritiro_dedicato
tuo_guadagno_lordo_anno = ricavo_da_cliente_anno + ricavo_da_rete_anno - canone_superficie_anno


# --- TAB 2: ANALISI ANNUALE ---
with tab_analisi_annuale:
    st.subheader("💰 Bilancio Economico Annuale")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.info(f"**GUADAGNO TOTALE CLIENTE:**\n### € {guadagno_totale_cliente_anno:.2f} / anno")
        st.write(f"• Risparmio in bolletta: € {risparmio_energetico_cliente_anno:.2f}")
        st.write(f"• Canone d'affitto tetto percepito: € {canone_superficie_anno:.2f}")
        
    with col_r2:
        st.success(f"**IL TUO GUADAGNO NETTO (Meno Affitto):**\n### € {tuo_guadagno_lordo_anno:.2f} / anno")
        st.write(f"• Vendita energia al cliente: € {ricavo_da_cliente_anno:.2f}")
        st.write(f"• Vendita eccedenze in rete (RID): € {ricavo_da_rete_anno:.2f}")

    # Grafici delle due curve per mostrare la differenza feriale/weekend
    st.markdown("---")
    st.subheader("📈 Confronto Curve di Carico")
    
    g1, g2 = st.columns(2)
    with g1:
        st.caption("Giorno Feriale (Lavorativo)")
        fig_f = go.Figure()
        fig_f.add_trace(go.Scatter(x=ore, y=profilo_consumo_feriale, name="Consumo", line=dict(color='red')))
        fig_f.add_trace(go.Scatter(x=ore, y=profilo_produzione, name="Produzione FV", line=dict(color='green', dash='dash')))
        fig_f.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250, legend=dict(orientation="h", y=1.2))
        st.plotly_chart(fig_f, use_container_width=True, config={'displayModeBar': False})
        
    with g2:
        st.caption("Giorno Festivo / Weekend (Consumo ridotto)")
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=ore, y=profilo_consumo_weekend, name="Consumo", line=dict(color='red')))
        fig_w.add_trace(go.Scatter(x=ore, y=profilo_produzione, name="Produzione FV", line=dict(color='green', dash='dash')))
        fig_w.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250, legend=dict(orientation="h", y=1.2))
        st.plotly_chart(fig_w, use_container_width=True, config={'displayModeBar': False})


# --- TAB 3: VANTAGGIO TOTALE CONTRATTO ---
with tab_vantaggio_totale:
    st.subheader(f"🚀 Proiezione Finanziaria su {durata_contratto} Anni")
    
    vantaggio_cumulato_cliente = guadagno_totale_cliente_anno * durata_contratto
    tuo_ricavo_cumulato = tuo_guadagno_lordo_anno * durata_contratto
    
    st.warning(f"### 🤝 Valore Complessivo del Contratto PPA")
    
    c_v1, c_v2 = st.columns(2)
    with c_v1:
        st.metric(label=f"Beneficio Economico Totale per il Cliente", value=f"€ {vantaggio_cumulato_cliente:.2f}")
        st.write(f"In {durata_contratto} anni il cliente azzera i rischi d'investimento e ottiene un ricavo/risparmio netto cumulato pari a questa cifra.")
        
    with c_v2:
        st.metric(label=f"Tuo Ricavo Netto Cumulato (Pre-Ammortamento)", value=f"€ {tuo_ricavo_cumulato:.2f}")
        st.write(f"Questa è la cifra lorda totale che incasserai nell'arco dei {durata_contratto} anni, al netto del pagamento dei canoni di affitto superficiali.")

    # Tabella riassuntiva finale
    st.markdown("---")
    st.subheader("📊 Tabella di Riepilogo")
    
    dati_tabella = {
        "Soggetto": ["Cliente Finale (Azienda)", "Tu (Investitore Fotovoltaico)"],
        "Guadagno Annuo (€)": [f"€ {guadagno_totale_cliente_anno:.2f}", f"€ {tuo_guadagno_lordo_anno:.2f}"],
        f"Totale su {durata_contratto} Anni (€)": [f"€ {vantaggio_cumulato_cliente:.2f}", f"€ {tuo_ricavo_cumulato:.2f}"]
    }
    df = pd.DataFrame(dati_tabella)
    st.table(df)

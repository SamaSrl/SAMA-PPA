import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import json
import os

# Configurazione Mobile-First
st.set_page_config(page_title="Gestione PPA Fotovoltaico", layout="wide")

# --- FILE DI MEMORIA LOCALE ---
DB_FILE = "simulazioni.json"

def carica_simulazioni():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def salva_simulazione(nome, dati):
    simulazioni = carica_simulazioni()
    simulazioni[nome] = dati
    with open(DB_FILE, "w") as f:
        json.dump(simulazioni, f, indent=4)

def elimina_simulazione(nome):
    simulazioni = carica_simulazioni()
    if nome in simulazioni:
        del simulazioni[nome]
        with open(DB_FILE, "w") as f:
            json.dump(simulazioni, f, indent=4)

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

# ---------------------------------------------------------
# MENU LATERALE A SCOMPARSA (Ottimizzato per Mobile)
# ---------------------------------------------------------
with st.sidebar:
    st.header("📁 Menu Gestionale")
    menu = st.radio("Seleziona Azione:", ["Nuova Simulazione", "Archivio Impianti", "🔒 Area Riservata Sama"], index=0)
    st.markdown("---")

# ---------------------------------------------------------
# FUNZIONE DI CALCOLO ENERGETICO (Unificata per precisione feriale/weekend)
# ---------------------------------------------------------
def esegui_calcoli_energetici(f1, f2, f3, kwp, prod):
    ore = np.arange(0, 24)
    f1_m = f1 / 12
    f2_m = f2 / 12
    f3_m = f3 / 12

    p_cons_feriale = np.zeros(24)
    for h in ore:
        if 8 <= h < 19: p_cons_feriale[h] = f1_m / 21 / 11 
        elif (7 <= h < 8) or (19 <= h < 23): p_cons_feriale[h] = f2_m / 21 / 5
        else: p_cons_feriale[h] = f3_m / 21 / 8

    p_cons_weekend = p_cons_feriale * 0.20
    
    p_prod = np.zeros(24)
    tot_anno_prod = kwp * prod
    g_medio = tot_anno_prod / 365
    for h in ore:
        if 6 <= h <= 18:
            p_prod[h] = (g_medio / 7.5) * np.sin(np.pi * (h - 6) / 12) ** 2

    # Incroci energetici
    autocons_feriale = np.minimum(p_cons_feriale, p_prod)
    immessa_feriale = np.maximum(0, p_prod - autocons_feriale)
    
    autocons_weekend = np.minimum(p_cons_weekend, p_prod)
    immessa_weekend = np.maximum(0, p_prod - autocons_weekend)
    
    autocons_a = (np.sum(autocons_feriale) * 261) + (np.sum(autocons_weekend) * 104)
    immessa_a = (np.sum(immessa_feriale) * 261) + (np.sum(immessa_weekend) * 104)
    
    if autocons_a > tot_anno_prod:
        autocons_a = tot_anno_prod
        immessa_a = 0
        
    return ore, p_cons_feriale, p_cons_weekend, p_prod, autocons_a, immessa_a

# ---------------------------------------------------------
# SCHERMATA 1: NUOVA SIMULAZIONE / CALCOLATORE
# ---------------------------------------------------------
if menu == "Nuova Simulazione":
    st.title("📊 Simulatore Risparmio Fotovoltaico")
    nome_cliente = st.text_input("👤 Nome Cliente / Azienda o Impianto", placeholder="Es. Rossi SRL - Milano")

    st.markdown("---")
    st.subheader("⚙️ Inserimento Dati")

    with st.expander("Fasce Consumo ANNUALI (kWh/anno)", expanded=True):
        f1_anno = st.number_input("Consumo in F1", value=15000, step=1000)
        f2_anno = st.number_input("Consumo in F2", value=12000, step=1000)
        f3_anno = st.number_input("Consumo in F3", value=10000, step=1000)

    with st.expander("Dati Impianto Fotovoltaico", expanded=False):
        kwp = st.number_input("Potenza Impianto Proposto (kWp)", value=20.0, step=1.0)
        prod_specifica = st.number_input("Produttività (kWh/kWp)", value=1300, step=50)

    with st.expander("Tariffe Energia (€/kWh)", expanded=False):
        tariffa_cliente_attuale = st.number_input("Tariffa attuale Cliente", value=0.28, step=0.01)
        tariffa_vendita_tua = st.number_input("Nuova tariffa energia da Fotovoltaico", value=0.16, step=0.01)

    with st.expander("Accordo Diritto di Superficie", expanded=False):
        canone_superficie_anno = st.number_input("Canone Annuale riconosciuto al Cliente (€/anno)", value=1500, step=100)
        durata_contratto = st.number_input("Durata del Contratto (Anni)", value=20, step=1)

    with st.sidebar:
        st.subheader("💾 Gestione Scheda")
        if st.button("💾 SALVA SIMULAZIONE", use_container_width=True, type="primary"):
            if nome_cliente.strip() == "":
                st.error("⚠️ Inserisci un nome prima!")
            else:
                payload = {
                    "f1": f1_anno, "f2": f2_anno, "f3": f3_anno,
                    "kwp": kwp, "prod": prod_specifica,
                    "tariffa_c": tariffa_cliente_attuale, "tariffa_v": tariffa_vendita_tua,
                    "canone": canone_superficie_anno, "durata": durata_contratto
                }
                salva_simulazione(nome_cliente, payload)
                st.success(f"Salvata: {nome_cliente}")

        if st.button("🗑️ ELIMINA SIMULAZIONE", use_container_width=True):
            if nome_cliente.strip() == "":
                st.warning("Scrivi il nome da cancellare.")
            else:
                elimina_simulazione(nome_cliente)
                st.success(f"Rimossa: {nome_cliente}")

    # Esegui calcoli energetici
    ore, p_cons_feriale, p_cons_weekend, p_prod, autoconsumo_anno, _ = esegui_calcoli_energetici(f1_anno, f2_anno, f3_anno, kwp, prod_specifica)

    risparmio_energetico_anno = autoconsumo_anno * (tariffa_cliente_attuale - tariffa_vendita_tua)
    guadagno_totale_cliente_anno = risparmio_energetico_anno + canone_superficie_anno
    vantaggio_cumulato_cliente_totale = guadagno_totale_cliente_anno * durata_contratto

    # --- SEZIONE RISULTATI CLIENTE ---
    st.markdown("---")
    st.subheader("🎯 Benefici Economici per il Cliente")
    tab_annuale, tab_totale, tab_grafici = st.tabs(["📅 Vantaggio Annuale", "🚀 Vantaggio nei Anni", "📈 Curve di Carico"])

    with tab_annuale:
        st.info(f"**GUADAGNO + RISPARMIO ANNUALE:**\n### € {guadagno_totale_cliente_anno:.2f} / anno")
        st.write(f"• **Risparmio sulla bolletta:** € {risparmio_energetico_anno:.2f}/anno")
        st.write(f"• **Entrata fissa da Diritto di Superficie:** € {canone_superficie_anno:.2f}/anno")

    with tab_totale:
        st.warning(f"**BENEFICIO ECONOMICO TOTALE CONTRATTO:**\n### € {vantaggio_cumulato_cliente_totale:.2f}")
        dati_tabella = {
            "Voce di Guadagno": ["Risparmio Energetico Pulito", "Canone Diritto di Superficie", "VALORE TOTALE RISERVATO"],
            "Su Base Annua": [f"€ {risparmio_energetico_anno:.2f}", f"€ {canone_superficie_anno:.2f}", f"€ {guadagno_totale_cliente_anno:.2f}"],
            f"Totale su {durata_contratto} Anni": [f"€ {risparmio_energetico_anno * durata_contratto:.2f}", f"€ {canone_superficie_anno * durata_contratto:.2f}", f"€ {vantaggio_cumulato_cliente_totale:.2f}"]
        }
        st.table(pd.DataFrame(dati_tabella))

    with tab_grafici:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ore, y=p_cons_feriale, name="Consumo Feriale (kW)", line=dict(color='#FF4B4B', width=2)))
        fig.add_trace(go.Scatter(x=ore, y=p_cons_weekend, name="Consumo Weekend (kW)", line=dict(color='#636EFA', width=2, dash='dot')))
        fig.add_trace(go.Scatter(x=ore, y=p_prod, name="Produzione FV (kW)", line=dict(color='#00CC96', width=2)))
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.1), height=300)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ---------------------------------------------------------
# SCHERMATA 2: ARCHIVIO IMPIANTI SIMULATI
# ---------------------------------------------------------
elif menu == "Archivio Impianti":
    st.title("📁 Archivio Impianti Simulati")
    simulazioni = carica_simulazioni()

    if not simulazioni:
        st.info("L'archivio è vuoto. Salva una simulazione nel menu a comparsa per vederla qui.")
    else:
        scelta_cliente = st.selectbox("Seleziona Cliente:", list(simulazioni.keys()))
        if scelta_cliente:
            d = simulazioni[scelta_cliente]
            _, _, _, _, autocons_a, _ = esegui_calcoli_energetici(d["f1"], d["f2"], d["f3"], d["kwp"], d["prod"])

            risp_a = autocons_a * (d["tariffa_c"] - d["tariffa_v"])
            guad_a = risp_a + d["canone"]
            tot_a = guad_a * d["durata"]

            st.markdown("---")
            st.success(f"### Dati Economici Riservati: {scelta_cliente}")
            st.info(f"**VANTAGGIO ANNUALE:** € {guad_a:.2f} / anno (Risparmio: € {risp_a:.2f} | Affitto: € {d['canone']:.2f})")
            st.warning(f"**VANTAGGIO SULLA DURATA ({d['durata']} anni):** € {tot_a:.2f}")

            dati_tab_salvata = {
                "Parametro d'Impianto": ["Potenza FV (kWp)", "Produzione Specifica", "Consumo Annuo F1", "Consumo Annuo F2", "Consumo Annuo F3"],
                "Valore Impostato": [f"{d['kwp']} kWp", f"{d['prod']} kWh/kWp", f"{d['f1']} kWh", f"{d['f2']} kWh", f"{d['f3']} kWh"]
            }
            st.table(pd.DataFrame(dati_tab_salvata))

            with st.sidebar:
                st.subheader("🗑️ Azione Archivio")
                if st.button(f"🗑️ ELIMINA DEFINITIVAMENTE", type="secondary", use_container_width=True):
                    elimina_simulazione(scelta_cliente)
                    st.success(f"Eliminato!")
                    st.rerun()

# ---------------------------------------------------------
# SCHERMATA 3: AREA RISERVATA SAMA (NUOVA)
# ---------------------------------------------------------
elif menu == "🔒 Area Riservata Sama":
    st.title("🔒 Area Riservata Sama - Controllo Ricavi")
    simulazioni = carica_simulazioni()

    if not simulazioni:
        st.info("Nessun impianto in archivio. Crea e salva una simulazione per vederla qui.")
    else:
        st.subheader("📊 Analisi Margini e Business Plan Interno")
        scelta_sama = st.selectbox("Seleziona Pratica Cliente:", list(simulazioni.keys()))
        
        if scelta_sama:
            d = simulazioni[scelta_sama]
            
            # --- TAB INTERNI DI INSERIMENTO TARIFFE RICAVO SAMA ---
            with st.expander("💰 Configurazione Tariffe Interne (Sama)", expanded=True):
                prezzo_rid = st.number_input("Prezzo Energia in Rete (RID) [€/kWh]", value=0.07, step=0.01)
                scelta_cer = st.radio("Presenza Comunità Energetica (CER)?", ["NO", "SÌ"], horizontal=True)
                
                if scelta_cer == "SÌ":
                    tariffa_cer = st.number_input("Incentivo Tariffa CER spettante a te [€/kWh]", value=0.11, step=0.01)
                else:
                    tariffa_cer = 0.0

            # --- LOGICA DI CALCOLO INTERNA ---
            _, _, _, _, autocons_a, immessa_a = esegui_calcoli_energetici(d["f1"], d["f2"], d["f3"], d["kwp"], d["prod"])
            
            # Voci di ricavo
            ricavo_da_cliente_ppa = autocons_a * d["tariffa_v"]
            ricavo_da_eccedenze_rid = immessa_a * prezzo_rid
            ricavo_da_cer = immessa_a * tariffa_cer if scelta_cer == "SÌ" else 0.0
            
            # Formula Finale: Vendita Cliente + RID + CER - Affitto Diritto di Superficie
            tua_entrata_lorda_annuale = ricavo_da_cliente_ppa + ricavo_da_eccedenze_rid + ricavo_da_cer
            tuo_margine_netto_annuale = tua_entrata_lorda_annuale - d["canone"]
            tuo_margine_contratto_totale = tuo_margine_netto_annuale * d["durata"]

            # --- DISPLAY BUSINESS PLAN INTERNO ---
            st.markdown("---")
            st.subheader(f"📈 Rendimento Finanziario Impianto: {scelta_sama}")
            
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                st.metric(label="Tuo Guadagno Netto Annuale", value=f"€ {tuo_margine_netto_annuale:.2f} / anno")
                st.caption(f"Già sottratto il canone d'affitto dovuto al cliente di € {d['canone']:.2f}")
            with c_s2:
                st.metric(label=f"Tuo Ricavo Cumulato su {d['durata']} Anni", value=f"€ {tuo_margine_contratto_totale:.2f}")
                st.caption("Margine complessivo pre-ammortamento costo d'impianto.")

            # Tabella di scomposizione economica interna
            st.markdown("---")
            st.write("📊 **Dettaglio Economico Analitico (Sama):**")
            
            voci_conto_economico = {
                "Voce Finanziaria": [
                    "1. Vendita Energia al Cliente (PPA)", 
                    "2. Vendita Eccedenze in Rete (RID)", 
                    f"3. Contributo CER ({scelta_cer})",
                    "4. Costo Diritto di Superficie (Affitto)",
                    "MARGINE NETTO SAMA"
                ],
                "Impatto Annuo (€)": [
                    f"+ € {ricavo_da_cliente_ppa:.2f}",
                    f"+ € {ricavo_da_eccedenze_rid:.2f}",
                    f"+ € {ricavo_da_cer:.2f}",
                    f"- € {d['canone']:.2f}",
                    f"€ {tuo_margine_netto_annuale:.2f}"
                ],
                f"Totale su {d['durata']} Anni (€)": [
                    f"+ € {ricavo_da_cliente_ppa * d['durata']:.2f}",
                    f"+ € {ricavo_da_eccedenze_rid * d['durata']:.2f}",
                    f"+ € {ricavo_da_cer * d['durata']:.2f}",
                    f"- € {d['canone'] * d['durata']:.2f}",
                    f"€ {tuo_margine_contratto_totale:.2f}"
                ]
            }
            st.table(pd.DataFrame(voci_conto_economico))
            
            # Dati energetici di supporto per il calcolo interno
            st.info(f"⚡ **Dati di Flusso Energetico:** Produzione Totale: {d['kwp']*d['prod']:.0f} kWh/anno | Autoconsumata da Cliente: {autocons_a:.0f} kWh ({autocons_a/(d['kwp']*d['prod'])*100:.1f}%) | Immessa in Rete (RID/CER): {immessa_a:.0f} kWh")

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
    menu = st.radio("Seleziona Azione:", ["Nuova Simulazione", "Archivio Impianti"], index=0)
    st.markdown("---")

# ---------------------------------------------------------
# SCHERMATA 1: NUOVA SIMULAZIONE / CALCOLATORE
# ---------------------------------------------------------
if menu == "Nuova Simulazione":
    st.title("📊 Simulatore Risparmio Fotovoltaico")
    
    # Campo Nome principale in alto
    nome_cliente = st.text_input("👤 Nome Cliente / Azienda o Impianto", placeholder="Es. Rossi SRL - Milano")

    st.markdown("---")
    st.subheader("⚙️ Inserimento Dati")

    with st.expander("Fasce Consumo ANNUALI (kWh/anno)", expanded=True):
        f1_anno = st.number_input("Consumo in F1", value=15000, step=1000)
        f2_anno = st.number_input("Consumo in F2", value=12000, step=1000)
        f3_anno = st.number_input("Consumo in F3", value=10000, step=1000)

    with st.expander("Dati Impianto Fotovoltaico", expanded=False):
        kwp = st.number_input("Potenza Impianto (kWp)", value=20.0, step=1.0)
        prod_specifica = st.number_input("Produttività (kWh/kWp)", value=1300, step=50)

    with st.expander("Tariffe Energia (€/kWh)", expanded=False):
        tariffa_cliente_attuale = st.number_input("Tariffa attuale Cliente", value=0.28, step=0.01)
        tariffa_vendita_tua = st.number_input("Nuova tariffa PPA", value=0.16, step=0.01)

    with st.expander("Accordo Diritto di Superficie", expanded=False):
        canone_superficie_anno = st.number_input("Canone Annuale (€/anno)", value=1500, step=100)
        durata_contratto = st.number_input("Durata Contratto (Anni)", value=20, step=1)

    # Spostiamo i pulsanti di gestione nel menu laterale per non distrarre il cliente sulla pagina
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

    # --- MATEMATICA E CALCOLI ---
    ore = np.arange(0, 24)
    f1_mese = f1_anno / 12
    f2_mese = f2_anno / 12
    f3_mese = f3_anno / 12

    profilo_consumo_feriale = np.zeros(24)
    for h in ore:
        if 8 <= h < 19: profilo_consumo_feriale[h] = f1_mese / 21 / 11 
        elif (7 <= h < 8) or (19 <= h < 23): profilo_consumo_feriale[h] = f2_mese / 21 / 5
        else: profilo_consumo_feriale[h] = f3_mese / 21 / 8

    profilo_consumo_weekend = profilo_consumo_feriale * 0.20
    produzione_totale_anno = kwp * prod_specifica
    produzione_giorno_medio = produzione_totale_anno / 365
    profilo_produzione = np.zeros(24)
    for h in ore:
        if 6 <= h <= 18:
            profilo_produzione[h] = (produzione_giorno_medio / 7.5) * np.sin(np.pi * (h - 6) / 12) ** 2

    autoconsumo_feriale_giorno = np.minimum(profilo_consumo_feriale, profilo_produzione)
    autoconsumo_weekend_giorno = np.minimum(profilo_consumo_weekend, profilo_produzione)
    autoconsumo_anno = (np.sum(autoconsumo_feriale_giorno) * 261) + (np.sum(autoconsumo_weekend_giorno) * 104)
    
    if autoconsumo_anno > produzione_totale_anno:
        autoconsumo_anno = produzione_totale_anno

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
        fig.add_trace(go.Scatter(x=ore, y=profilo_consumo_feriale, name="Consumo Feriale (kW)", line=dict(color='#FF4B4B', width=2)))
        fig.add_trace(go.Scatter(x=ore, y=profilo_consumo_weekend, name="Consumo Weekend (kW)", line=dict(color='#636EFA', width=2, dash='dot')))
        fig.add_trace(go.Scatter(x=ore, y=profilo_produzione, name="Produzione FV (kW)", line=dict(color='#00CC96', width=2)))
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.1), height=300)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ---------------------------------------------------------
# SCHERMATA 2: ARCHIVIO IMPIANTI SIMULATI
# ---------------------------------------------------------
elif menu == "Archivio Impianti":
    st.title("📁 Archivio Impianti Simulati")
    simulazioni = carica_simulazioni()

    if not simulazioni:
        st.info("L'archivio è vuoto. Apri il menu laterale, seleziona 'Nuova Simulazione' e salvala per vederla qui.")
    else:
        st.write("Seleziona una simulazione salvata dal menu a tendina qui sotto.")
        
        scelta_cliente = st.selectbox("Seleziona Cliente:", list(simulazioni.keys()))
        
        if scelta_cliente:
            d = simulazioni[scelta_cliente]
            
            # Ricalcolo rapido per l'archivio
            ore = np.arange(0, 24)
            f1_m = d["f1"] / 12
            f2_m = d["f2"] / 12
            f3_m = d["f3"] / 12

            p_cons_feriale = np.zeros(24)
            for h in ore:
                if 8 <= h < 19: p_cons_feriale[h] = f1_m / 21 / 11 
                elif (7 <= h < 8) or (19 <= h < 23): p_cons_feriale[h] = f2_m / 21 / 5
                else: p_cons_feriale[h] = f3_m / 21 / 8

            p_cons_weekend = p_cons_feriale * 0.20
            p_prod = np.zeros(24)
            g_medio = (d["kwp"] * d["prod"]) / 365
            for h in ore:
                if 6 <= h <= 18:
                    p_prod[h] = (g_medio / 7.5) * np.sin(np.pi * (h - 6) / 12) ** 2

            autocons_feriale = np.minimum(p_cons_feriale, p_prod)
            autocons_weekend = np.minimum(p_cons_weekend, p_prod)
            autocons_a = (np.sum(autocons_feriale) * 261) + (np.sum(autocons_weekend) * 104)

            risp_a = autocons_a * (d["tariffa_c"] - d["tariffa_v"])
            guad_a = risp_a + d["canone"]
            tot_a = guad_a * d["durata"]

            st.markdown("---")
            st.success(f"### Dati Economici Riservati: {scelta_cliente}")
            
            st.info(f"**VANTAGGIO ANNUALE:** € {guad_a:.2f} / anno (Risparmio: € {risp_a:.2f} | Affitto: € {d['canone']:.2f})")
            st.warning(f"**VANTAGGIO SULLA DURATA ({d['durata']} anni):** € {tot_a:.2f}")

            # Tabella riassuntiva
            dati_tab_salvata = {
                "Parametro d'Impianto": ["Potenza FV (kWp)", "Produzione Specifica", "Consumo Annuo F1", "Consumo Annuo F2", "Consumo Annuo F3"],
                "Valore Impostato": [f"{d['kwp']} kWp", f"{d['prod']} kWh/kWp", f"{d['f1']} kWh", f"{d['f2']} kWh", f"{d['f3']} kWh"]
            }
            st.table(pd.DataFrame(dati_tab_salvata))

            # Aggiungiamo il tasto cancella anche nella sidebar quando siamo in modalità archivio
            with st.sidebar:
                st.subheader("🗑️ Azione Archivio")
                if st.button(f"🗑️ ELIMINA DEFINITIVAMENTE", type="secondary", use_container_width=True):
                    elimina_simulazione(scelta_cliente)
                    st.success(f"Eliminato!")
                    st.rerun()

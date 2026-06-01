import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Simulatore FV & PPA", layout="wide")

# --- SISTEMA DI AUTENTICAZIONE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    # MODIFICA QUI: Metti la password che desideri al posto di 'FvPpa2026'
    if st.session_state["password"] == "sama2026": 
        st.session_state.authenticated = True
        del st.session_state["password"]  # Svuota la memoria per sicurezza
    else:
        st.session_state.authenticated = False
        st.error("❌ Password errata!")

if not st.session_state.authenticated:
    st.title("🔒 Accesso Riservato")
    st.write("Questo simulatore è protetto. Inserisci la password per sbloccarlo.")
    st.text_input("Password:", type="password", key="password", on_change=check_password)
    st.stop() # Blocca l'app qui finché la password non è corretta

# --- DA QUI IN POI PARTE IL TUO CODICE DI PRIMA ---
st.title("📊 Simulatore Impianto Fotovoltaico in PPA")
st.write("Inserisci i dati per calcolare il profilo di consumo, la produzione e i ricavi.")

# --- SIDEBAR: INPUT DATI ---
st.sidebar.header("1. Dati di Consumo (Mensili/Annuali)")
f1 = st.sidebar.number_input("Consumo in F1 (kWh)", value=1200)
f2 = st.sidebar.number_input("Consumo in F2 (kWh)", value=1000)
f3 = st.sidebar.number_input("Consumo in F3 (kWh)", value=800)

st.sidebar.header("2. Dati Impianto Fotovoltaico")
kwp = st.sidebar.number_input("Potenza Impianto (kWp)", value=6.0)
pr = st.sidebar.slider("Performance Ratio (PR)", 0.70, 0.90, 0.80)
ore_equivalenti = st.sidebar.number_input("Ore di sole equivalenti giornaliere medie", value=3.5)

st.sidebar.header("3. Tariffe ed Economia")
tariffa_cliente_attuale = st.sidebar.number_input("Tariffa attuale del cliente (€/kWh)", value=0.30)
tariffa_vendita_tua = st.sidebar.number_input("Tua tariffa di vendita al cliente (€/kWh)", value=0.18)
prezzo_ritiro_dedicato = st.sidebar.number_input("Prezzo vendita in rete RID (€/kWh)", value=0.08)

# --- ELABORAZIONE DATI ---
ore = np.arange(0, 24)

profilo_consumo = np.zeros(24)
for h in ore:
    if 8 <= h < 19:
        profilo_consumo[h] = f1 / 30 / 11 
    elif (7 <= h < 8) or (19 <= h < 23):
        profilo_consumo[h] = f2 / 30 / 5
    else:
        profilo_consumo[h] = f3 / 30 / 8

produzione_totale_giorno = kwp * ore_equivalenti * pr
profilo_produzione = np.zeros(24)
for h in ore:
    if 6 <= h <= 18:
        profilo_produzione[h] = (produzione_totale_giorno / 7.5) * np.sin(np.pi * (h - 6) / 12) ** 2

autoconsumo = np.minimum(profilo_consumo, profilo_produzione)
energia_immessa_in_rete = profilo_produzione - autoconsumo

# --- CALCOLI ECONOMICI ---
energia_autoconsumata_mese = np.sum(autoconsumo) * 30
energia_immessa_mese = np.sum(energia_immessa_in_rete) * 30

risparmio_cliente = energia_autoconsumata_mese * (tariffa_cliente_attuale - tariffa_vendita_tua)
ricavo_da_cliente = energia_autoconsumata_mese * tariffa_vendita_tua
ricavo_da_rete = energia_immessa_mese * prezzo_ritiro_dedicato
guadagno_tuo_totale = ricavo_da_cliente + ricavo_da_rete

# --- GRAFICI E RISULTATI ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Curve Giornaliere Simulate (Media Mensile)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ore, y=profilo_consumo, name="Consumo Cliente (kW)", line=dict(color='red')))
    fig.add_trace(go.Scatter(x=ore, y=profilo_produzione, name="Produzione FV (kW)", line=dict(color='green', dash='dash')))
    fig.add_trace(go.Scatter(x=ore, y=autoconsumo, name="Autoconsumo (kW)", fill='tozeroy', line=dict(color='orange')))
    fig.update_layout(xaxis_title="Ora del giorno", yaxis_title="Potenza (kW)")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("💰 Analisi Economica Mensile Stimata")
    st.metric(label="Risparmio Netto del Cliente", value=f"€ {risparmio_cliente:.2f} / mese")
    st.write(f"Il cliente ha ridotto la bolletta comprando da te {energia_autoconsumata_mese:.0f} kWh.")
    st.markdown("---")
    st.metric(label="Il Tuo Ricavo Lordo Totale", value=f"€ {guadagno_tuo_totale:.2f} / mese")
    st.write(f"• Vendita al cliente: € {ricavo_da_cliente:.2f}")
    st.write(f"• Vendita in rete (RID): € {ricavo_da_rete:.2f}")

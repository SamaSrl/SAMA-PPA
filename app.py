import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Configurazione ottimizzata per mobile (layout wide ma responsivo)
st.set_page_config(page_title="Simulatore FV & PPA", layout="wide")

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
    st.write("Questo simulatore è protetto. Inserisci la password per sbloccarlo.")
    st.text_input("Password:", type="password", key="password", on_change=check_password)
    st.stop() 

# --- TITOLO PRINCIPALE ---
st.title("📊 Simulatore FV & PPA")
st.write("Calcolo rapido profilato per smartphone e PC.")

# --- INPUT DATI (Raggruppati in BOX espandibili per risparmiare spazio su mobile) ---
with st.expander("📝 1. Consumi Bolletta Cliente (Fasce F1, F2, F3)", expanded=True):
    f1 = st.number_input("Consumo mensile F1 (kWh)", value=1200, step=100)
    f2 = st.number_input("Consumo mensile F2 (kWh)", value=1000, step=100)
    f3 = st.number_input("Consumo mensile F3 (kWh)", value=800, step=100)

with st.expander("☀️ 2. Dati Impianto Fotovoltaico", expanded=False):
    kwp = st.number_input("Potenza Impianto (kWp)", value=6.0, step=0.5)
    pr = st.slider("Performance Ratio (PR)", 0.90, 1.10, 1.30, step=0.05)
    ore_equivalenti = st.number_input("Ore di sole equivalenti medie giornaliere", value=8.5, step=0.1)

with st.expander("💶 3. Tariffe ed Economia (€/kWh)", expanded=False):
    tariffa_cliente_attuale = st.number_input("Tariffa attuale del cliente", value=0.30, step=0.01)
    tariffa_vendita_tua = st.number_input("Tua tariffa di vendita al cliente (PPA)", value=0.18, step=0.01)
    prezzo_ritiro_dedicato = st.number_input("Prezzo vendita eccedenze in rete (RID)", value=0.08, step=0.01)

# --- ELABORAZIONE DATI MATEMATICI ---
ore = np.arange(0, 24)

# Simulazione profilo di consumo orario medio giornaliero
profilo_consumo = np.zeros(24)
for h in ore:
    if 8 <= h < 19:
        profilo_consumo[h] = f1 / 30 / 11 
    elif (7 <= h < 8) or (19 <= h < 23):
        profilo_consumo[h] = f2 / 30 / 5
    else:
        profilo_consumo[h] = f3 / 30 / 8

# Simulazione profilo di produzione FV giornaliero
produzione_totale_giorno = kwp * ore_equivalenti * pr
profilo_produzione = np.zeros(24)
for h in ore:
    if 6 <= h <= 18:
        profilo_produzione[h] = (produzione_totale_giorno / 7.5) * np.sin(np.pi * (h - 6) / 12) ** 2

# Calcolo incroci energetici
autoconsumo = np.minimum(profilo_consumo, profilo_produzione)
energia_immessa_in_rete = np.maximum(0, profilo_produzione - autoconsumo)

# Proiezione Economica Mensile
energia_autoconsumata_mese = np.sum(autoconsumo) * 30
energia_immessa_mese = np.sum(energia_immessa_in_rete) * 30

risparmio_cliente = energia_autoconsumata_mese * (tariffa_cliente_attuale - tariffa_vendita_tua)
ricavo_da_cliente = energia_autoconsumata_mese * tariffa_vendita_tua
ricavo_da_rete = energia_immessa_mese * prezzo_ritiro_dedicato
guadagno_tuo_totale = ricavo_da_cliente + ricavo_da_rete

# --- SEZIONE RISULTATI (Layout verticale ideale per Mobile) ---
st.markdown("---")
st.subheader("💰 Risultati Economici Mensili")

# Visualizzazione card affiancate su PC, incolonnate su Mobile automaticamente
m1, m2 = st.columns(2)
with m1:
    st.info(f"**RISPARMIO CLIENTE:**\n### € {risparmio_cliente:.2f} / mese")
    st.caption(f"Energia fornita da te e autoconsumata: {energia_autoconsumata_mese:.0f} kWh/mese")

with m2:
    st.success(f"**IL TUO GUADAGNO LORDO:**\n### € {guadagno_tuo_totale:.2f} / mese")
    st.caption(f"Dettaglio: € {ricavo_da_cliente:.2f} da cliente | € {ricavo_da_rete:.2f} da rete (RID)")

# --- GRAFICO OTTIMIZZATO PER SCHERMI STRETTI ---
st.markdown("---")
st.subheader("📈 Curva Oraria Giornaliera Media")

fig = go.Figure()
fig.add_trace(go.Scatter(x=ore, y=profilo_consumo, name="Consumo (kW)", line=dict(color='#FF4B4B', width=2)))
fig.add_trace(go.Scatter(x=ore, y=profilo_produzione, name="Produzione FV (kW)", line=dict(color='#00CC96', width=2, dash='dash')))
fig.add_trace(go.Scatter(x=ore, y=autoconsumo, name="Autoconsumo (kW)", fill='tozeroy', line=dict(color='#FFA15A', width=0)))

# Trucco Mobile: Spostiamo la legenda in alto e riduciamo i margini per non stringere il grafico
fig.update_layout(
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    xaxis=dict(title="Ora del giorno", tickmode="linear", tick0=0, dtick=4),
    yaxis=dict(title="Potenza (kW)"),
    height=350 # Altezza fissa ideale per lo scrolling da smartphone
)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

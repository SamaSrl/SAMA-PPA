import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Configurazione ottimizzata per mobile e PC
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
st.title("📊 Simulatore FV & PPA (Calcolo Annuale)")
st.write("Profilazione e stima economica basata su dati di consumo annuali e produttività specifica.")

# --- INPUT DATI ---
with st.expander("📝 1. Consumi ANNUALI Bolletta Cliente (kWh/anno)", expanded=True):
    f1_anno = st.number_input("Consumo Annuo F1 (kWh)", value=15000, step=1000)
    f2_anno = st.number_input("Consumo Annuo F2 (kWh)", value=12000, step=1000)
    f3_anno = st.number_input("Consumo Annuo F3 (kWh)", value=10000, step=1000)

with st.expander("☀️ 2. Dati Impianto Fotovoltaico", expanded=False):
    kwp = st.number_input("Potenza Impianto (kWp)", value=20.0, step=1.0)
    prod_specifica = st.number_input("Produttività Annuale (kWh/kWp)", value=1300, step=50, help="Esempio: 1100 al Nord, 1300 al Centro, 1450 al Sud")

with st.expander("💶 3. Tariffe ed Economia (€/kWh)", expanded=False):
    tariffa_cliente_attuale = st.number_input("Tariffa attuale del cliente", value=0.28, step=0.01)
    tariffa_vendita_tua = st.number_input("Tua tariffa di vendita al cliente (PPA)", value=0.16, step=0.01)
    prezzo_ritiro_dedicato = st.number_input("Prezzo vendita eccedenze in rete (RID)", value=0.07, step=0.01)

# --- ELABORAZIONE DATI MATEMATICI ---
# Calcoliamo i dati medi mensili e giornalieri per la simulazione delle curve
f1_mese = f1_anno / 12
f2_mese = f2_anno / 12
f3_mese = f3_anno / 12

ore = np.arange(0, 24)

# 1. Simulazione profilo di consumo orario medio giornaliero (base mensile)
profilo_consumo = np.zeros(24)
for h in ore:
    if 8 <= h < 19:
        profilo_consumo[h] = f1_mese / 30 / 11 
    elif (7 <= h < 8) or (19 <= h < 23):
        profilo_consumo[h] = f2_mese / 30 / 5
    else:
        profilo_consumo[h] = f3_mese / 30 / 8

# 2. Simulazione profilo di produzione FV annuale riportato al giorno medio
# Produzione totale annua = kWp * kWh/kWp
produzione_totale_anno = kwp * prod_specifica
produzione_giorno_medio = produzione_totale_anno / 365

profilo_produzione = np.zeros(24)
for h in ore:
    if 6 <= h <= 18:
        # Curva a campana basata sulla produzione del giorno medio
        profilo_produzione[h] = (produzione_giorno_medio / 7.5) * np.sin(np.pi * (h - 6) / 12) ** 2

# 3. Calcolo incroci energetici giornalieri medi
autoconsumo_giorno = np.minimum(profilo_consumo, profilo_produzione)
energia_immessa_giorno = np.maximum(0, profilo_produzione - autoconsumo_giorno)

# 4. Proiezione su base ANNUALI complessiva
autoconsumo_anno = np.sum(autoconsumo_giorno) * 365
immessa_anno = np.sum(energia_immessa_giorno) * 365

# Se per errore matematico l'autoconsumo calcolato supera la produzione reale, lo limitiamo
if autoconsumo_anno > produzione_totale_anno:
    autoconsumo_anno = produzione_totale_anno
    immessa_anno = 0

# --- CALCOLO GUADAGNI ANNUALI ---
risparmio_cliente_anno = autoconsumo_anno * (tariffa_cliente_attuale - tariffa_vendita_tua)
ricavo_da_cliente_anno = autoconsumo_anno * tariffa_vendita_tua
ricavo_da_rete_anno = immessa_anno * prezzo_ritiro_dedicato
guadagno_tuo_anno = ricavo_da_cliente_anno + ricavo_da_rete_anno

# --- SEZIONE RISULTATI ECONOMICI (ANNUALI) ---
st.markdown("---")
st.subheader("💰 Analisi Economica Annuale Stimata")

m1, m2 = st.columns(2)
with m1:
    st.info(f"**RISPARMIO NETTO CLIENTE:**\n### € {risparmio_cliente_anno:.2f} / anno")
    st.write(f"• Risparmio mensile medio: € {risparmio_cliente_anno/12:.2f}")
    st.caption(f"Energia totale acquistata da te: {autoconsumo_anno:.0f} kWh/anno")

with m2:
    st.success(f"**IL TUO GUADAGNO LORDO:**\n### € {guadagno_tuo_anno:.2f} / anno")
    st.write(f"• Ricavo mensile medio: € {guadagno_tuo_anno/12:.2f}")
    st.caption(f"Dettaglio ricavi:\n\n Vendita a cliente: € {ricavo_da_cliente_anno:.2f}\n\n Vendita in rete (RID): € {ricavo_da_rete_anno:.2f}")

# --- GRAFICO ---
st.markdown("---")
st.subheader("📈 Curva Oraria Giornaliera Media (Rapportata al mese)")

fig = go.Figure()
fig.add_trace(go.Scatter(x=ore, y=profilo_consumo, name="Consumo (kW)", line=dict(color='#FF4B4B', width=2)))
fig.add_trace(go.Scatter(x=ore, y=profilo_produzione, name="Produzione FV (kW)", line=dict(color='#00CC96', width=2, dash='dash')))
fig.add_trace(go.Scatter(x=ore, y=autoconsumo_giorno, name="Autoconsumo (kW)", fill='tozeroy', line=dict(color='#FFA15A', width=0)))

fig.update_layout(
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis=dict(title="Ora del giorno", tickmode="linear", tick0=0, dtick=4),
    yaxis=dict(title="Potenza (kW)"),
    height=350
)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

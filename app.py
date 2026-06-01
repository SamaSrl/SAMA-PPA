import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Configurazione ottimizzata per Mobile: layout fluido e compatto
st.set_page_config(page_title="Simulatore Benefici Cliente FV", layout="wide")

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
st.title("📊 Simulatore Risparmio Fotovoltaico")
st.write("Calcola il vantaggio economico totale per il cliente finale.")

# --- INSERIMENTO DATI UNIFICATO (Tutto nella pagina principale, ottimizzato smartphone) ---
st.subheader("⚙️ Inserimento Dati")

with st.expander("📝 1. Consumi ANNUALI del Cliente (kWh/anno)", expanded=True):
    f1_anno = st.number_input("Consumo Annuo in F1", value=15000, step=1000)
    f2_anno = st.number_input("Consumo Annuo in F2", value=12000, step=1000)
    f3_anno = st.number_input("Consumo Annuo in F3", value=10000, step=1000)

with st.expander("☀️ 2. Dati Impianto Fotovoltaico", expanded=False):
    kwp = st.number_input("Potenza Impianto Proposto (kWp)", value=20.0, step=1.0)
    prod_specifica = st.number_input("Produttività Specifica Annuale (kWh/kWp)", value=1300, step=50)

with st.expander("💶 3. Tariffe Energia (€/kWh)", expanded=False):
    tariffa_cliente_attuale = st.number_input("Tariffa attuale in bolletta del Cliente", value=0.28, step=0.01)
    tariffa_vendita_tua = st.number_input("Nuova tariffa energia da Fotovoltaico", value=0.16, step=0.01)

with st.expander("🤝 4. Accordo Diritto di Superficie / Affitto", expanded=False):
    canone_superficie_anno = st.number_input("Canone Annuale riconosciuto al Cliente (€/anno)", value=1500, step=100)
    durata_contratto = st.number_input("Durata del Contratto (Anni)", value=20, step=1)

# --- ELABORAZIONE MATEMATICA (Modello feriale + weekend) ---
ore = np.arange(0, 24)
f1_mese = f1_anno / 12
f2_mese = f2_anno / 12
f3_mese = f3_anno / 12

# Profilo Consumo Giorno Feriale (261 giorni/anno)
profilo_consumo_feriale = np.zeros(24)
for h in ore:
    if 8 <= h < 19: profilo_consumo_feriale[h] = f1_mese / 21 / 11 
    elif (7 <= h < 8) or (19 <= h < 23): profilo_consumo_feriale[h] = f2_mese / 21 / 5
    else: profilo_consumo_feriale[h] = f3_mese / 21 / 8

# Profilo Consumo Weekend (104 giorni/anno) - Ridotto all'20% del feriale
profilo_consumo_weekend = profilo_consumo_feriale * 0.20

# Profilo Produzione FV Giornaliero Medio
produzione_totale_anno = kwp * prod_specifica
produzione_giorno_medio = produzione_totale_anno / 365
profilo_produzione = np.zeros(24)
for h in ore:
    if 6 <= h <= 18:
        profilo_produzione[h] = (produzione_giorno_medio / 7.5) * np.sin(np.pi * (h - 6) / 12) ** 2

# Calcolo Autoconsumo (Energia che il cliente compra dal FV risparmiando)
autoconsumo_feriale_giorno = np.minimum(profilo_consumo_feriale, profilo_produzione)
autoconsumo_weekend_giorno = np.minimum(profilo_consumo_weekend, profilo_produzione)

autoconsumo_anno = (np.sum(autoconsumo_feriale_giorno) * 261) + (np.sum(autoconsumo_weekend_giorno) * 104)

if autoconsumo_anno > produzione_totale_anno:
    autoconsumo_anno = produzione_totale_anno

# --- CALCOLO VANTAGGI ECONOMICI CLIENTE ---
risparmio_energetico_anno = autoconsumo_anno * (tariffa_cliente_attuale - tariffa_vendita_tua)
guadagno_totale_cliente_anno = risparmio_energetico_anno + canone_superficie_anno
vantaggio_cumulato_cliente_totale = guadagno_totale_cliente_anno * durata_contratto

# --- SEZIONE RISULTATI (Visualizzazione a TAB, pulita su Mobile) ---
st.markdown("---")
st.subheader("🎯 Benefici Economici per il Cliente")

tab_annuale, tab_totale, tab_grafici = st.tabs([
    "📅 Vantaggio Annuale", 
    "🚀 Vantaggio negli Anni", 
    "📈 Curve di Carico"
])

with tab_annuale:
    st.info(f"**GUADAGNO + RISPARMIO ANNUALE:**\n### € {guadagno_totale_cliente_anno:.2f} / anno")
    st.write(f"• **Risparmio sulla bolletta:** € {risparmio_energetico_anno:.2f}/anno (grazie a {autoconsumo_anno:.0f} kWh autoconsumati)")
    st.write(f"• **Entrata fissa da Diritto di Superficie:** € {canone_superficie_anno:.2f}/anno")

with tab_totale:
    st.warning(f"**BENEFICIO ECONOMICO TOTALE CONTRATTO:**\n### € {vantaggio_cumulato_cliente_totale:.2f}")
    st.write(f"Valore economico complessivo generato per il cliente nei **{durata_contratto} anni** di durata del diritto di superficie, senza alcun costo di investimento iniziale.")
    
    # Tabella riassuntiva pulita
    st.markdown("---")
    dati_tabella = {
        "Voce di Guadagno": ["Risparmio Energetico Pulito", "Canone Diritto di Superficie", "VALORE TOTALE RISERVATO"],
        "Su Base Annua": [f"€ {risparmio_energetico_anno:.2f}", f"€ {canone_superficie_anno:.2f}", f"€ {guadagno_totale_cliente_anno:.2f}"],
        f"Totale su {durata_contratto} Anni": [f"€ {risparmio_energetico_anno * durata_contratto:.2f}", f"€ {canone_superficie_anno * durata_contratto:.2f}", f"€ {vantaggio_cumulato_cliente_totale:.2f}"]
    }
    st.table(pd.DataFrame(dati_tabella))

with tab_grafici:
    st.write("Confronto della simulazione dei consumi reali tra i giorni lavorativi e il weekend.")
    
    # Grafico unico ma interattivo per non occupare spazio verticale eccessivo su smartphone
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ore, y=profilo_consumo_feriale, name="Consumo Feriale (kW)", line=dict(color='#FF4B4B', width=2)))
    fig.add_trace(go.Scatter(x=ore, y=profilo_consumo_weekend, name="Consumo Weekend (kW)", line=dict(color='#636EFA', width=2, dash='dot')))
    fig.add_trace(go.Scatter(x=ore, y=profilo_produzione, name="Produzione FV (kW)", line=dict(color='#00CC96', width=2)))
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(title="Ora", tickmode="linear", tick0=0, dtick=4),
        yaxis=dict(title="Potenza (kW)"),
        height=300
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

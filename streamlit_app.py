from utils import sidebar_global, verificar_autenticacao
import streamlit as st
import pandas as pd

# --- Conexão com Supabase ---
supabase = verificar_autenticacao()

# --- Configuração da Página ---
st.set_page_config(page_title="Dashboard",layout="wide")
sidebar_global()

# --- Página ---
st.title("OFFICEFLOW")
st.write("Gerenciador de ativos de TI para pequenas e médias empresas.")
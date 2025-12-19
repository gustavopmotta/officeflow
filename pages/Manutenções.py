from utils import sidebar_global, verificar_autenticacao
import streamlit as st
import pandas as pd
import datetime

# --- Conexão com Supabase ---
supabase = verificar_autenticacao()

# --- Configuração da Pagina ---
st.set_page_config(page_title="Manutenções", layout="wide")
sidebar_global()

# --- Função de Carregamento ---
st.title("Manutenções")
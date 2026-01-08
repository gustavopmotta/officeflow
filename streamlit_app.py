import streamlit as st
import pandas as pd
import plotly.express as px
from utils import sidebar_global, verificar_autenticacao
from st_pages import get_nav_from_toml, add_page_title

# --- Conexão com supabase ---
supabase = verificar_autenticacao()

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="OfficeFlow")
sidebar_global()

# --- Configuração de todas as Páginas ---
dashboard = st.Page("pages/Dashboard.py", title="- Visão Geral", default=True)

ativos      = st.Page("pages/Ativos.py", title="- Gestão de Ativos")
movim       = st.Page("pages/Movimentações.py", title="- Registrar Movimentação")
manutencoes = st.Page("pages/Manutenções.py", title="- Controle de Manutenções")

cad_geral   = st.Page("pages/Cadastro_Geral.py", title="- Cadastros Gerais")
cad_compras = st.Page("pages/Cadastro_de_Compras.py", title="- Registro de Compras")
usuarios    = st.Page("pages/Usuários.py", title="- Gestão de Usuários")

pg = st.navigation(
    {
        "Principal": [dashboard],
        "Operacional": [ativos, movim, manutencoes],
        "Administração": [cad_geral, cad_compras, usuarios],
    }
)

pg.run()
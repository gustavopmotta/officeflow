import streamlit as st
import pandas as pd
import plotly.express as px
from utils import verificar_autenticacao

# --- Conexão com supabase ---
supabase = verificar_autenticacao()

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="OfficeFlow")
st.logo("assets/logo_officeflow.png", icon_image="assets/logo_officeflow.png")

# --- Configuração de todas as Páginas ---
dashboard = st.Page("pages/Dashboard.py", title="> Visão Geral", default=True)

ativos      = st.Page("pages/Ativos.py", title="> Gestão de Ativos")
movim       = st.Page("pages/Movimentações.py", title="> Registrar Movimentação")
manutencoes = st.Page("pages/Manutenções.py", title="> Controle de Manutenções")

cad_geral   = st.Page("pages/Cadastro_Geral.py", title="> Cadastros Gerais")
cad_compras = st.Page("pages/Cadastro_de_Compras.py", title="> Registro de Compras")
usuarios    = st.Page("pages/Usuários.py", title="> Gestão de Usuários")

ex_im_dados = st.Page("pages/Importar_Exportar.py", title="> Importar/Exportar Dados")
backup = st.Page("pages/Backup.py", title="> Backup Geral")

pg = st.navigation(
    {
        "Principal": [dashboard],
        "Operacional": [ativos, movim, manutencoes],
        "Administração": [cad_geral, cad_compras, usuarios],
        "Banco de Dados": [ex_im_dados, backup]
    }
)

pg.run()

# --- Configuração da Barra Latera ---
with st.sidebar:       
    if st.session_state.user:
        nome = st.session_state.user.get("nome", st.session_state.user.get("email"))
        st.write(f"Usuário: **{nome}**")
    
        if st.button("Sair"):
            st.session_state.user = None
            st.rerun()
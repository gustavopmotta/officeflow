import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- Conexão com Supabase (Repetir a mesma lógica do app.py) ---
# Isso usa o cache do Streamlit para manter uma única conexão.
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- Funções para Carregar Dados Auxiliares ---
# Usamos cache de dados para não buscar no banco a cada interação
def carregar_opcoes():
    """Busca dados das tabelas auxiliares para preencher os selectbox."""
    modelos = supabase.table("modelos").select("id, nome").execute().data
    setores = supabase.table("setores").select("id, nome").execute().data
    status = supabase.table("status").select("id, nome").execute().data
    estados = supabase.table("estados").select("id, nome").execute().data
    
    return modelos, setores, status, estados

# --- Página de Cadastro ---
st.title("Cadastrar Novo Ativo")

# Carrega os dados para os dropdowns
try:
    modelos, setores, status, estados = carregar_opcoes()

    # --- Criar Mapeamentos ---
    # Precisamos de um dicionário (map) para converter o NOME selecionado
    # de volta para o ID que será salvo no banco.
    # Ex: 'Notebook Dell' -> 14
    modelos_map = {m['nome']: m['id'] for m in modelos}
    setores_map = {s['nome']: s['id'] for s in setores}
    status_map = {s['nome']: s['id'] for s in status}
    estados_map = {e['nome']: e['id'] for e in estados}

    # --- Formulário de Cadastro ---
    with st.form("form_cadastro_ativo", clear_on_submit=True):
        st.subheader("Informações do Ativo")
        
        # --- Inputs do Formulário ---
        serial_input = st.text_input("Serial Number (ou Patrimônio)", key="serial")
        
        # Usamos .keys() para mostrar os nomes no dropdown
        modelo_selecionado = st.selectbox("Modelo", options=modelos_map.keys())
        setor_selecionado = st.selectbox("Setor (Local)", options=setores_map.keys())
        status_selecionado = st.selectbox("Status", options=status_map.keys())
        estado_selecionado = st.selectbox("Estado", options=estados_map.keys())

        # --- Botão de Envio ---
        submitted = st.form_submit_button("Cadastrar Ativo")

    # --- Lógica de Submissão (Fora do 'with st.form') ---
    if submitted:
        if not serial_input:
            st.error("O campo 'Serial' é obrigatório.")
        else:
            # Converter os NOMES selecionados de volta para IDs
            try:
                modelo_id = modelos_map[modelo_selecionado]
                local_id = setores_map[setor_selecionado] # FK correta é 'local_id'
                status_id = status_map[status_selecionado]
                estado_id = estados_map[estado_selecionado]
                
                # Montar o objeto de inserção
                novo_ativo = {
                    "serial": serial_input,
                    "modelo_id": modelo_id,
                    "local_id": local_id,
                    "status_id": status_id,
                    "estado_id": estado_id
                    # 'criado_em' será preenchido automaticamente pelo Supabase (se configurado)
                }
                
                # Inserir no Supabase
                response = supabase.table("ativos").insert(novo_ativo).execute()
                
                if response.data:
                    st.success("Ativo cadastrado com sucesso!")
                else:
                    # Tenta mostrar o erro específico do banco
                    st.error(f"Erro ao cadastrar: {response.error.message}")
                    
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar os dados: {e}")

except Exception as e:
    st.error(f"Não foi possível carregar as opções de cadastro: {e}")
    st.info("Verifique a conexão e se as tabelas 'modelos', 'setores', 'status' e 'estados' existem.")
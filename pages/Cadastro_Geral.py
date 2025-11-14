import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- Conexão com Supabase ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- Função de Carregamento ---
@st.cache_data
def carregar_opcoes_modelo():
    """Busca marcas e categorias para o formulário de Modelos."""
    marcas = supabase.table("marcas").select("id, nome").execute().data
    categorias = supabase.table("categorias").select("id, nome").execute().data
    return marcas, categorias

# --- Título da Página ---
st.title("Cadastro Geral (Auxiliares)")
st.info("Utilize esta página para gerenciar os itens que aparecem nos menus suspensos do cadastro de ativos.")

# --- Carregar Dados para o Formulário de Modelos ---
try:
    marcas_data, categorias_data = carregar_opcoes_modelo()
    
    marcas_map = {m['nome']: m['id'] for m in marcas_data}
    categorias_map = {c['nome']: c['id'] for c in categorias_data}

except Exception as e:
    st.error(f"Erro ao carregar dados auxiliares: {e}")
    # Define mapas vazios se houver falha para evitar que o app quebre
    marcas_map = {}
    categorias_map = {}

# --- Criar Abas (Tabs) ---
tab_marcas, tab_categorias, tab_setores, tab_modelos = st.tabs([
    "Cadastrar Marcas", 
    "Cadastrar Categorias", 
    "Cadastrar Setores", 
    "Cadastrar Modelos"
])

# --- Aba 1: Marcas ---
with tab_marcas:
    st.subheader("Cadastrar Nova Marca")
    with st.form("form_marca", clear_on_submit=True):
        nome_marca = st.text_input("Nome da Marca")
        submitted_marca = st.form_submit_button("Salvar Marca")

    if submitted_marca:
        if not nome_marca:
            st.error("Por favor, preencha o nome da marca.")
        else:
            try:
                response = supabase.table("marcas").insert({"nome": nome_marca}).execute()
                if response.data:
                    st.cache_data.clear() # Limpa o cache para atualizar o form de modelos
                    st.rerun()  # Recarrega a página para atualizar os dados
                else:
                    st.error(f"Erro ao salvar: {response.error.message}")
            except Exception as e:
                st.error(f"Erro: {e}")

# --- Aba 2: Categorias ---
with tab_categorias:
    st.subheader("Cadastrar Nova Categoria")
    with st.form("form_categoria", clear_on_submit=True):
        nome_categoria = st.text_input("Nome da Categoria")
        submitted_categoria = st.form_submit_button("Salvar Categoria")

    if submitted_categoria:
        if not nome_categoria:
            st.error("Por favor, preencha o nome da categoria.")
        else:
            try:
                response = supabase.table("categorias").insert({"nome": nome_categoria}).execute()
                if response.data:
                    st.cache_data.clear() # Limpa o cache para atualizar o form de modelos
                    st.rerun()  # Recarrega a página para atualizar os dados
                else:
                    st.error(f"Erro ao salvar: {response.error.message}")
            except Exception as e:
                st.error(f"Erro: {e}")

# --- Aba 3: Setores ---
with tab_setores:
    st.subheader("Cadastrar Novo Setor (Local)")
    with st.form("form_setor", clear_on_submit=True):
        nome_setor = st.text_input("Nome do Setor")
        submitted_setor = st.form_submit_button("Salvar Setor")

    if submitted_setor:
        if not nome_setor:
            st.error("Por favor, preencha o nome do setor.")
        else:
            try:
                response = supabase.table("setores").insert({"nome": nome_setor}).execute()
                if response.data:
                    st.success(f"Setor '{nome_setor}' cadastrado com sucesso!")
                    # Não precisa limpar o cache aqui, pois setores não são usados em "Modelos"
                else:
                    st.error(f"Erro ao salvar: {response.error.message}")
            except Exception as e:
                st.error(f"Erro: {e}")

# --- Aba 4: Modelos (Depende de Marcas e Categorias) ---
with tab_modelos:
    st.subheader("Cadastrar Novo Modelo")
    
    if not marcas_map or not categorias_map:
        st.warning("É necessário cadastrar ao menos uma Marca e uma Categoria antes de cadastrar um Modelo.")
    else:
        with st.form("form_modelo", clear_on_submit=True):
            nome_modelo = st.text_input("Nome do Modelo (ex: 'Latitude 5490', 'Magic Mouse 2')")
            
            # Menus suspensos com dados carregados no início
            marca_selecionada = st.selectbox("Marca do Modelo", options=marcas_map.keys())
            categoria_selecionada = st.selectbox("Categoria do Modelo", options=categorias_map.keys())
            
            submitted_modelo = st.form_submit_button("Salvar Modelo")

        if submitted_modelo:
            if not nome_modelo:
                st.error("Por favor, preencha o nome do modelo.")
            else:
                try:
                    # Converter nomes selecionados de volta para IDs
                    marca_id = marcas_map[marca_selecionada]
                    categoria_id = categorias_map[categoria_selecionada]
                    
                    novo_modelo = {
                        "nome": nome_modelo,
                        "marca_id": marca_id,
                        "categoria_id": categoria_id
                    }
                    
                    response = supabase.table("modelos").insert(novo_modelo).execute()
                    
                    if response.data:
                        st.success(f"Modelo '{nome_modelo}' cadastrado com sucesso!")
                    else:
                        st.error(f"Erro ao salvar: {response.error.message}")
                        
                except Exception as e:
                    st.error(f"Erro: {e}")
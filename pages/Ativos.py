import streamlit as st
from supabase import create_client, Client
import pandas as pd

@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

st.title("Gerenciar Ativos")
st.set_page_config(page_title="Gerenciar Ativos", layout="wide")

tab_lista, tab_cadastro = st.tabs(["Lista de Ativos", "Cadastrar Novo Ativo"])

def carregar_opcoes():
    modelos = supabase.table("modelos").select("id, categoria_id, nome").execute().data
    categorias = supabase.table("categorias").select("id, nome").execute().data
    setores = supabase.table("setores").select("id, nome").execute().data
    status = supabase.table("status").select("id, nome").execute().data
    estados = supabase.table("estados").select("id, nome").execute().data
    
    return modelos, categorias, setores, status, estados

def carregar_ativos():
    try:
        response = supabase.table("ativos").select(
            """
            id,
            serial,
            status:status_id(nome),
            estados:estado_id(nome),
            modelos(nome, marcas(nome), categorias(nome)),
            setores(nome)
            """
        ).execute()

        print("DEBUG: Resposta do Supabase:", response)
        return response.data
    
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        print(f"Erro detalhado da API: {e}")
        return []

def processar_dados(dados_brutos):
    """Transforma os dados brutos do Supabase em um DataFrame limpo."""
    if not dados_brutos:

        return pd.DataFrame()

    # Converte a lista de dicionários em um DataFrame do Pandas
    df = pd.DataFrame(dados_brutos)

    # 1. Achatar colunas simples (ex: {'nome': 'Em Uso'} -> 'Em Uso')
    # O .get('nome') é seguro e retorna None se a chave 'nome' não existir
    df['status'] = df['status'].apply(lambda x: x.get('nome') if isinstance(x, dict) else x)
    df['estados'] = df['estados'].apply(lambda x: x.get('nome') if isinstance(x, dict) else x)
    df['setores'] = df['setores'].apply(lambda x: x.get('nome') if isinstance(x, dict) else x)

    # 2. Achatar coluna complexa 'modelos'
    df['modelo'] = df['modelos'].apply(lambda x: x.get('nome') if isinstance(x, dict) else None)
    
    # .get('marcas', {}) retorna um dict vazio se 'marcas' não existir, evitando erros
    df['marca'] = df['modelos'].apply(lambda x: x.get('marcas', {}).get('nome') if isinstance(x, dict) else None)
    df['categoria'] = df['modelos'].apply(lambda x: x.get('categorias', {}).get('nome') if isinstance(x, dict) else None)

    # 3. Limpar, reordenar e renomear colunas
    
    # Remover a coluna 'modelos' original, que continha o objeto
    df = df.drop(columns=['modelos'])
    
    # Definir a ordem e os nomes que queremos exibir
    colunas_finais = {
        'id': 'ID',
        'serial': 'Serial',
        'modelo': 'Modelo',
        'marca': 'Marca',
        'categoria': 'Categoria',
        'status': 'Status',
        'estados': 'Estado',
        'setores': 'Setor'
    }
    
    # Filtra o DataFrame para ter apenas as colunas desejadas e as renomeia
    df_limpo = df[colunas_finais.keys()].rename(columns=colunas_finais)

    return df_limpo

with tab_cadastro:
    try:
        modelos, categorias, setores, status, estados = carregar_opcoes()

        # --- Criar Mapeamentos ---
        # Precisamos de um dicionário (map) para converter o NOME selecionado
        # de volta para o ID que será salvo no banco.
        # Ex: 'Notebook Dell' -> 14
        categorias_map = {c['nome']: c['id'] for c in categorias}
        setores_map = {s['nome']: s['id'] for s in setores}
        status_map = {s['nome']: s['id'] for s in status}
        estados_map = {e['nome']: e['id'] for e in estados}

        if not categorias_map:
            st.error("É necessário cadastrar ao menos uma Categoria antes de cadastrar um Ativo.")

        else:
        # --- Formulário de Cadastro ---
            st.subheader("1. Categoria do Ativo")
            categoria_selecionada = st.selectbox("Categoria do Ativo", options=categorias_map.keys(), label_visibility="collapsed")

            if categoria_selecionada:
                # Encontra o ID da categoria selecionada
                categoria_id_selecionada = categorias_map[categoria_selecionada]

                # Cria uma lista de modelos que pertencem a essa categoria
                modelos_filtrados = [
                    m for m in modelos 
                    if m.get('categoria_id') == categoria_id_selecionada
                ]
                # Cria o mapa apenas com os modelos filtrados
                modelos_filtrados_map = {m['nome']: m['id'] for m in modelos_filtrados}
            else:
                # Se nenhuma categoria for selecionada, o mapa de modelos fica vazio
                modelos_filtrados_map = {}

            st.subheader("2. Informações do Ativo")   
            with st.form("form_cadastro_ativo", clear_on_submit=True):


                # --- Inputs do Formulário ---
                serial_input = st.text_input("Serial Number (ou Patrimônio)", key="serial")

                # Usamos .keys() para mostrar os nomes no dropdown
                modelo_selecionado = st.selectbox("Modelo", options=modelos_filtrados_map.keys())
                setor_selecionado = st.selectbox("Setor", options=setores_map.keys())
                status_selecionado = st.selectbox("Status", options=status_map.keys())
                estado_selecionado = st.selectbox("Estado", options=estados_map.keys())

                # --- Botão de Envio ---
                submitted = st.form_submit_button("Cadastrar Ativo")

            # --- Lógica de Submissão (Fora do 'with st.form') ---
            if submitted:
                if not serial_input or not modelo_selecionado:
                    st.error("Os campos 'Serial' e 'Modelo' são obrigatórios.")
                else:
                    # Converter os NOMES selecionados de volta para IDs
                    try:
                        novo_ativo = {
                            "serial": serial_input,
                            # 7. Modificado: Usamos o mapa filtrado para obter o ID
                            "modelo_id": modelos_filtrados_map[modelo_selecionado], 
                            "local_id": setores_map[setor_selecionado],
                            "status_id": status_map[status_selecionado],
                            "estado_id": estados_map[estado_selecionado]
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

with tab_lista:
    st.subheader("Lista de Ativos Cadastrados")

    dados_brutos = carregar_ativos()
    df_ativos = processar_dados(dados_brutos)

    if df_ativos.empty:
        st.info("Nenhum ativo cadastrado encontrado.")
    else:
        st.data_editor(df_ativos, num_rows="dynamic", height="stretch", width="stretch")
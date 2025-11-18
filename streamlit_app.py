from supabase import create_client, Client
import streamlit as st
import pandas as pd

st.title("OFFICEFLOW")
st.write(
    "Gerenciador de ativos de TI para pequenas e médias empresas."
)

@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

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

st.set_page_config(page_title="Dashboard",layout="wide")
st.title("Dashboard de Ativos")

ativos_data = carregar_ativos()

if ativos_data:
    df_processado = processar_dados(ativos_data)
    st.dataframe(df_processado, use_container_width=True)
else:
    st.info("Nenhum ativo cadastrado.")
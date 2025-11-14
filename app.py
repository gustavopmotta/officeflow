from supabase import create_client, Client
import streamlit as st

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
    # A mágica está no select!
    # Ele busca 'ativos' e já traz os dados das tabelas relacionadas
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
        # Traz o erro para a tela do Streamlit
        print(f"Erro detalhado da API: {e}")
        return []

st.set_page_config(layout="wide")
st.title("Dashboard de Ativos")

ativos_data = carregar_ativos()

if ativos_data:
    # st.dataframe é ótimo para exibir tabelas
    st.dataframe(ativos_data)
else:
    st.info("Nenhum ativo cadastrado.")
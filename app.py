from supabase import create_client, Client
import streamlit as st

@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

st.title("OFFICEFLOW")
st.write(
    "Gerenciador de ativos de TI para pequenas e médias empresas."
)

def carregar_ativos():
    # A mágica está no select!
    # Ele busca 'ativos' e já traz os dados das tabelas relacionadas
    response = supabase.table("ativos").select(
        """
        id,
        serial_number,
        status,
        categorias(nome),
        modelos(nome, marcas(nome)),
        setores(nome)
        """
    ).execute()
    return response.data

st.set_page_config(layout="wide")
st.title("Dashboard de Ativos 📊")

ativos_data = carregar_ativos()

if ativos_data:
    # st.dataframe é ótimo para exibir tabelas
    st.dataframe(ativos_data)
else:
    st.info("Nenhum ativo cadastrado.")
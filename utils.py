from supabase import create_client, Client
import streamlit as st
import bcrypt
import time

# --- 1. Centralizando a Conexão ---
@st.cache_resource()
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def verificar_autenticacao():
    try:
        client = init_connection()
    except Exception as e:
        st.error(f"Erro de conexão com Supabase: {e}")
        st.stop()

    # Verifica se existe sessão
    if "user" not in st.session_state:
        st.session_state.user = None

    # Se não estiver logado, mostra tela de login
    if st.session_state.user is None:
        st.set_page_config(layout="centered")
        # Esconder barra lateral
        st.markdown(
            """
            <style>
                [data-testid="stSidebar"] {display: none;}
                [data-testid="stSidebarCollapsedControl"] {display: none;}
            </style>
            """,
            unsafe_allow_html=True
        )

        # Layout da tela de login
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("OFFICEFLOW")
            st.header("Login")
            
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email")
                password = st.text_input("Senha", type="password")
                
                submitted = st.form_submit_button("Entrar", use_container_width=True)
            
            if submitted:
                # 1. Busca o usuário pelo email na tabela customizada
                response = client.table("user_sistema").select("*").eq("email", email).execute()
                
                usuario_encontrado = response.data
                
                if not usuario_encontrado:
                    st.error("Usuário não encontrado.")
                else:
                    user_data = usuario_encontrado[0]
                    stored_hash = user_data["senha_hash"]
                    
                    # 2. Verifica a senha usando bcrypt
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                        st.session_state.user = {
                            "email": user_data["email"],
                            "nome": user_data["nome"],
                            "id": user_data["id"],
                        }
                        st.success(f"Bem-vindo, {user_data['nome']}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
        
        # Para a execução aqui se não estiver logado
        st.stop()
    
    return client # Retorna o cliente para ser usado nas páginas

# --- Barra lateral Global do Site ---
def sidebar_global():
    with st.sidebar:
        st.markdown("### OFFICEFLOW")
        
        if st.session_state.user:
            nome = st.session_state.user.get("nome", st.session_state.user.get("email"))
            st.write(f"Usuário: **{nome}**")
        
            if st.button("Sair"):
                st.session_state.user = None
                st.rerun()
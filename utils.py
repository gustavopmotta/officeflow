import streamlit as st
from supabase import create_client, Client
import time

# --- 1. Centralizando a Conexão ---
# Movemos o init_connection para cá para reutilizar em todo lugar
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def verificar_autenticacao():
    client = init_connection()

    # Verifica se existe sessão
    if "user" not in st.session_state:
        st.session_state.user = None

    # Se não estiver logado, mostra tela de login
    if st.session_state.user is None:
        
        # Layout da tela de login
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("## 🔒 OfficeFlow Login")
            st.info("Acesso restrito a administradores.")
            
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            
            entrar = st.button("Entrar no Sistema", use_container_width=True)

            if entrar:
                try:
                    # Tenta fazer login no Supabase Auth
                    auth_response = client.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    
                    # Se der certo, salva o usuário na sessão
                    st.session_state.user = auth_response.user
                    st.success("Login realizado com sucesso!")
                    time.sleep(1)
                    st.rerun() # Recarrega a página para entrar no app
                    
                except Exception as e:
                    st.error("Email ou senha incorretos.")
        
        # COMANDO CRUCIAL: Para a execução aqui se não estiver logado
        st.stop()
    
    return client # Retorna o cliente para ser usado nas páginas

# --- Barra lateral Global do Site ---
def sidebar_global():
    with st.sidebar:
        st.markdown("### OfficeFlow")
        st.caption("Sistema de Gestão de Ativos")
        
        st.divider()
        
        st.markdown("Desenvolvido pela TI")
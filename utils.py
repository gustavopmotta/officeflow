import supabase
import streamlit as st
import os
import bcrypt
import time

# --- 1. Centralizando a Conexão ---
@st.cache_resource()
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return supabase.create_client(url, key)

def criar_usuario_admin(supabase, nome, email, senha_plana):
    try:
        salt = bcrypt.gensalt()
        senha_hash = bcrypt.hashpw(senha_plana.encode('utf-8'), salt)
        
        senha_hash_str = senha_hash.decode('utf-8')

        dados_insert = {
            "nome": nome,
            "email": email.strip().lower(),
            "senha_hash": senha_hash_str
        }

        response = supabase.table("user_sistema").insert(dados_insert).execute()
        
        if response.data:
            return True, "Usuário registrado com sucesso!"
        else:
            return False, "Erro desconhecido ao registrar usuário."
            
    except Exception as e:
        return False, f"Erro no banco de dados: {e}"

def atualizar_senha_usuario(supabase, usuario_id, nova_senha_plana):
    try:      
        # Gera o novo hash
        salt = bcrypt.gensalt()
        senha_hash = bcrypt.hashpw(nova_senha_plana.encode('utf-8'), salt)
        senha_hash_str = senha_hash.decode('utf-8')

        # Atualiza apenas a coluna 'senha_hash' no banco, buscando pelo ID
        response = supabase.table("user_sistema").update({
            "senha_hash": senha_hash_str
        }).eq("id", usuario_id).execute()
        
        if response.data:
            return True, "Senha atualizada com sucesso!"
        else:
            return False, "Erro ao atualizar a senha no banco."
            
    except Exception as e:
        return False, f"Erro no banco de dados: {e}"

def verificar_autenticacao():
    try:
        client = init_connection()
    except Exception as e:
        st.error(f"Erro de conexão com Supabase: {e}")
        st.stop()

    if "user" not in st.session_state:
        st.session_state.user = None
        
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

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("assets/logo_officeflow.png", width="stretch")
            
            with st.form("login_form", clear_on_submit=False):
                st.header("Login")
                email = st.text_input("Email")
                password = st.text_input("Senha", type="password")
                
                submitted = st.form_submit_button("Entrar", use_container_width=True)
            
            if submitted:
                response = client.table("user_sistema").select("*").eq("email", email).execute()
                
                usuario_encontrado = response.data
                
                if not usuario_encontrado:
                    st.error("Usuário não encontrado.")
                else:
                    user_data = usuario_encontrado[0]
                    stored_hash = user_data["senha_hash"]
                    
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
        
        st.stop()
    
    return client
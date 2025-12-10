from utils import sidebar_global, verificar_autenticacao
import streamlit as st
import pandas as pd

# --- Conexão com Supabase ---
supabase = verificar_autenticacao()

# --- Configuração da Pagina ---
st.set_page_config(page_title="Cadastro Geral", layout="wide")
sidebar_global()

# --- Função de Carregamento ---
st.title("Gestão de Usuários")

# --- Identificação de Dados ---
usuarios = supabase.table("usuarios").select("id, nome, email, setor_id").order("nome").execute().data
setores = supabase.table("setores").select("id, nome").order("nome").execute().data
setores_map = {s['nome']: s['id'] for s in setores}
nome_setores = list(setores_map.keys())

# --- Cadastro de Usuário ---
with st.form("form_usuario", clear_on_submit=True):
    st.subheader("Cadastrar Usuário")
    nome_usuario = st.text_input("Nome do Usuário")
    email_usuario = st.text_input("Email do Usuário")
    setor_selecionado = st.selectbox("Setor do Usuário", options=setores_map.keys())
    
    if st.form_submit_button("Salvar Usuário"):
        # Validação
        if not nome_usuario:
            st.error("O campo 'Nome do Usuário' é obrigatório.")
        else:
            # Traduz o nome do setor para setor_id
            setor_usuario = setores_map[setor_selecionado]
            novo_usuario_dados = {
                "nome": nome_usuario,
                "email": email_usuario,
                "setor_id": setor_usuario,
            }
            supabase.table("usuarios").insert(novo_usuario_dados).execute()
            st.success(f"Usuário '{nome_usuario}' cadastrado!")
            st.cache_data.clear()
            st.rerun()

st.divider()

# --- Gerenciamento de Usuário ---
try:
    df_users = pd.DataFrame(usuarios)
except Exception as e:
    st.error(f"Erro ao carregar usuários: {e}")
    st.stop()

# --- Formulário ---
with st.form("form_edit_users"):
    st.subheader("Editar Usuários:")
    edited_df_users = st.data_editor(
        df_users, key="editor_usuarios", 
        num_rows="fixed",
        width="stretch",

        column_config={
            "id": None,
            "nome": st.column_config.TextColumn("Nome",required=True),
            "email": st.column_config.TextColumn("Email"),

            "setor_id": st.column_config.SelectboxColumn(
                "Setor",
                options=nome_setores,
                required=True
            )
        }
    )
    submit_edit_users = st.form_submit_button("Salvar Alterações")

# --- Confirmação ---
if submit_edit_users:
    try:
        updates_count = 0
        for index, row in edited_df_users.iterrows():
            item_id = row["id"]
            # Traduz os nomes de volta para IDs
            dados_para_salvar = {
                "nome": row["nome"],
                "email": row["email"],
                "setor_id": setores_map[row["setor_id"]]
            }

            original_row = df_users.iloc[index]
            if not row.equals(original_row):
                supabase.table("usuarios").update(dados_para_salvar).eq("id", item_id).execute()
                updates_count += 1

        if updates_count > 0:
            st.success(f"{updates_count} alterações salvas com sucesso!")
            st.cache_data.clear()
        else:
            st.info("Nenhuma alteração detectada.")

    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        st.info("Verifique se algum campo obrigatório (Nome, Setor) ficou vazio.")
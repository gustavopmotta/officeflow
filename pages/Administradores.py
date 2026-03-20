import utils
import streamlit as st
import pandas as pd

# --- Conexão com Supabase ---
supabase = utils.verificar_autenticacao()

# --- Função para carregar administradores ---
def carregar_administradores():
    try: 
        response = supabase.table("user_sistema").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao carregar administradores: {e}")
        return None
    
@st.dialog("Cadastrar Novo Usuário")
def modal_novo_usuario():
    st.markdown("A senha será criptografada (`bcrypt`) antes de ser salva no banco.")
    
    novo_nome = st.text_input("Nome Completo")
    novo_email = st.text_input("E-mail")
    nova_senha = st.text_input("Senha de Acesso", type="password")
    
    if st.button("Registrar Usuário", icon=":material/check:", width="stretch"):
        if not novo_nome or not novo_email or not nova_senha:
            st.warning("Preencha todos os campos, incluindo a senha.")
        elif len(nova_senha) < 6:
            st.warning("A senha deve ter pelo menos 6 caracteres.")
        else:
            with st.spinner("Gerando hash e salvando..."):
                sucesso, mensagem = utils.criar_usuario_admin(
                    supabase, 
                    novo_nome, 
                    novo_email, 
                    nova_senha
                )
                
                if sucesso:
                    st.success(mensagem)
                    st.rerun()
                else:
                    st.error(mensagem)

@st.dialog("Alterar Senha")
def modal_alterar_senha(usuario_id, usuario_nome):
    st.markdown(f"Definindo nova senha para **{usuario_nome}**.")
    
    nova_senha = st.text_input("Digite a nova senha", type="password")
    
    if st.button("Salvar Nova Senha", width="stretch"):
        if not nova_senha:
            st.warning("A senha não pode ficar em branco.")
        elif len(nova_senha) < 6:
            st.warning("A senha deve ter pelo menos 6 caracteres.")
        else:
            with st.spinner("Atualizando senha..."):
                sucesso, mensagem = utils.atualizar_senha_usuario(supabase, usuario_id, nova_senha)
                if sucesso:
                    st.success(mensagem)
                    st.rerun()
                else:
                    st.error(mensagem)

# --- Página de Gerenciamento de Administradores ---
col_titulo, col_botao = st.columns([3, 1])

with col_titulo:
    st.title("Gerenciamento de Usuários")
    st.markdown("Visualize e gerencie os acessos ao sistema OfficeFlow.")

with col_botao:
    st.write("")
    st.write("")

    if st.button("Novo Usuário", icon=":material/add:", width="stretch"):
        modal_novo_usuario()

st.subheader("Usuários Cadastrados")
    
dados_administradores = carregar_administradores()

if dados_administradores:
    df_administradores = pd.DataFrame(dados_administradores)
    
    colunas_exibicao = {
        "id": None,
        "nome": st.column_config.TextColumn("Nome Completo"),
        "email": st.column_config.TextColumn("E-mail"),
        "senha_hash": None
    }

    evento_selecao = st.dataframe(
        df_administradores,
        width="stretch",
        hide_index=True,
        column_config=colunas_exibicao,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # --- Lógica do clique na linha ---
    linhas_selecionadas = evento_selecao.selection.rows
    
    if linhas_selecionadas:
        indice = linhas_selecionadas[0]
        usuario_selecionado = df_administradores.iloc[indice]
        
        with st.container(border=True):
            cols_painel = st.columns([3, 1])
            cols_painel[0].markdown(f"Usuário selecionado: **{usuario_selecionado['nome']}**")
            
            if cols_painel[1].button("Alterar Senha", width="stretch"):
                modal_alterar_senha(int(usuario_selecionado['id']), usuario_selecionado['nome'])
    
    st.caption(f"Total de {len(df_administradores)} usuários registrados.")
else:
    st.info("Nenhum usuário encontrado na tabela.")
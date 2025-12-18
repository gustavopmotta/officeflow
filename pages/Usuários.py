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

# --- Criação de Abas ---
cadastro_tab, gerenciar_tab = st.tabs(["Cadastrar / Editar", "Gerenciar"])

# --- Identificação de Dados ---
ativos_data = supabase.table("ativos").select("*, modelos(nome, marcas(nome)), status(nome)").execute().data
usuarios_data = supabase.table("usuarios").select("id, nome, email, setor_id").order("nome").execute().data
setores_data = supabase.table("setores").select("id, nome").order("nome").execute().data
status_data = supabase.table("status").select("id", "nome").order("nome").execute().data

# Mapeamento Nome -> ID (Para salvar)
setores_map = {s['nome']: s['id'] for s in setores_data}
status_map = {s['nome']: s['id'] for s in status_data}

nome_setores = list(setores_map.keys())
nome_status = list(status_map.keys())

# Mapeamento ID -> Nome (Para exibir na tabela)
id_to_nome_map = {s['id']: s['nome'] for s in setores_data}

# --- ABA 01: Cadastro/Edição de Usuário ---
with cadastro_tab:
    with st.form("form_usuario", clear_on_submit=True):
        st.subheader("Cadastrar Usuário")
        nome_usuario = st.text_input("Nome do Usuário")
        email_usuario = st.text_input("Email do Usuário")
        setor_selecionado = st.selectbox("Setor do Usuário", options=nome_setores)

        if st.form_submit_button("Salvar Usuário"):
            if not nome_usuario:
                st.error("O campo 'Nome do Usuário' é obrigatório.")
            else:
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
        df_users = pd.DataFrame(usuarios_data)

        # CORREÇÃO 1: Traduzir os IDs para Nomes ANTES de criar o editor
        # Se houver um ID no banco que não tem nome correspondente, preenchemos com vazio para não dar erro
        if not df_users.empty:
            df_users['setor_id'] = df_users['setor_id'].map(id_to_nome_map).fillna("")

    except Exception as e:
        st.error(f"Erro ao carregar usuários: {e}")
        st.stop()

    # --- Formulário ---
    with st.form("form_edit_users"):
        st.subheader("Editar Usuários:")

        edited_df_users = st.data_editor(
            df_users, 
            key="editor_usuarios", 
            num_rows="fixed",
            width="stretch",
            column_config={
                "id": None, # Esconde o ID
                "nome": st.column_config.TextColumn("Nome", required=True),
                "email": st.column_config.TextColumn("Email"),
                "setor_id": st.column_config.SelectboxColumn(
                    "Setor",
                    options=nome_setores, # As opções são Nomes
                    required=True
                )
            }
        )
        submit_edit_users = st.form_submit_button("Salvar Alterações")

    # --- Confirmação ---
    if submit_edit_users:
        try:
            updates_count = 0

            # Iterar sobre o dataframe editado
            for index, row in edited_df_users.iterrows():
                item_id = row["id"]

                # Recupera a linha original para comparar mudanças
                original_row = df_users.iloc[index]

                # Só processa se houver diferença entre a linha editada e a original
                if not row.equals(original_row):

                    # CORREÇÃO 2: Verificar se o setor é válido antes de buscar no mapa
                    nome_setor_atual = row["setor_id"]

                    if nome_setor_atual in setores_map:
                        # Traduz de volta: Nome -> ID
                        id_setor_salvar = setores_map[nome_setor_atual]

                        dados_para_salvar = {
                            "nome": row["nome"],
                            "email": row["email"],
                            "setor_id": id_setor_salvar
                        }

                        supabase.table("usuarios").update(dados_para_salvar).eq("id", item_id).execute()
                        updates_count += 1
                    else:
                        st.warning(f"Setor '{nome_setor_atual}' inválido para o usuário {row['nome']}.")

            if updates_count > 0:
                st.success(f"{updates_count} alterações salvas com sucesso!")
                st.cache_data.clear()
                # Aguarda um pouco e recarrega para atualizar a tabela visualmente com os dados do banco
                st.rerun()
            else:
                st.info("Nenhuma alteração detectada.")

        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# --- ABA 02: Gerenciamento de Usuários ---
with gerenciar_tab:
    # --- Mapeamento de Dados
    usuarios_map = {u["nome"]: u["id"] for u in usuarios_data}

    # --- Inicio da Aba ---
    st.subheader("1. Selecione um usuário para gerenciar")
    
    # --- Criação de Colunas
    col1, col2 = st.columns(2, width="stretch", vertical_alignment="top")
    
    # --- Coluna da Esquerda ---
    with col1:
        usuario_selecionado = st.selectbox(
            "Usuário",
            options=usuarios_map.keys()
            )

        id_usuario_alvo = usuarios_map[usuario_selecionado]
    
        ativos_filtrados = []
        for ativo in ativos_data:
            raw_uid = ativo.get("usuario_id")

            if isinstance(raw_uid, dict):
                uid_ativo = raw_uid.get("id")
            else:
                uid_ativo = raw_uid

            if uid_ativo == id_usuario_alvo:
                ativos_filtrados.append(ativo)

        if ativos_filtrados:
            # Preparando dados para exibição bonita (sem IDs soltos)
            df_display = []

            for a in ativos_filtrados:
                # Tratamento seguro para Marca e Modelo (igual fizemos antes)
                dados_modelo = a.get('modelos') if isinstance(a.get('modelos'), dict) else {}
                dados_marca = dados_modelo.get('marcas') if isinstance(dados_modelo.get('marcas'), dict) else {}
                dados_status = a.get('status') if isinstance(a.get('status'), dict) else {}

                df_display.append({
                    "Serial": a.get('serial'),
                    "Marca": dados_marca.get('nome', 'S/M'),
                    "Modelo": dados_modelo.get('nome', 'S/M'),
                    "Status": dados_status.get('nome', 'S/M')
                })

                st.subheader("Ativos:")
                st.dataframe(pd.DataFrame(df_display), width="stretch")
        else:
            st.info("Nenhum ativo encontrado para este usuário.")
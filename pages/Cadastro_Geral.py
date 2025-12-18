from utils import sidebar_global, verificar_autenticacao
import streamlit as st
import pandas as pd

# --- Conexão com Supabase ---
supabase = verificar_autenticacao()

# --- Configuração da Pagina ---
st.set_page_config(page_title="Cadastro Geral", layout="wide")
sidebar_global()

# --- Função de Carregamento ---
def carregar_opcoes_modelo():
    marcas = supabase.table("marcas").select("id, nome").execute().data
    categorias = supabase.table("categorias").select("id, nome").execute().data
    return marcas, categorias

# --- Título da Página ---
st.title("Cadastro Geral")
st.info("Utilize esta página para gerenciar os itens que aparecem nos menus suspensos do cadastro de ativos.")

# --- Carregar Dados para o Formulário de Modelos ---
try:
    marcas_data, categorias_data = carregar_opcoes_modelo()
    
    marcas_map = {m['nome']: m['id'] for m in marcas_data}
    categorias_map = {c['nome']: c['id'] for c in categorias_data}

except Exception as e:
    st.error(f"Erro ao carregar dados auxiliares: {e}")
    # Define mapas vazios se houver falha para evitar que o app quebre
    marcas_map = {}
    categorias_map = {}

# --- Crias abas principais ---
tab_cadastro, tab_geral = st.tabs(["Cadastro Geral","Gerenciar"])

# --- Cadastro ---
with tab_cadastro:
    st.subheader("Cadastrar Novo Modelo")

    # --- Aba 0: Modelos ---
    if not marcas_map or not categorias_map:
        st.warning("É necessário cadastrar ao menos uma Marca e uma Categoria antes de cadastrar um Modelo.")
    else:
        with st.form("form_modelo", clear_on_submit=True):
            nome_modelo = st.text_input("Nome do Modelo")
            marca_selecionada = st.selectbox("Marca do Modelo", options=marcas_map.keys())
            categoria_selecionada = st.selectbox("Categoria do Modelo", options=categorias_map.keys())
            submitted_modelo = st.form_submit_button("Salvar Modelo")

        if submitted_modelo:
            if not nome_modelo:
                st.error("Por favor, preencha o nome do modelo.")
            else:
                try:
                    # Converter nomes selecionados de volta para IDs
                    marca_id = marcas_map[marca_selecionada]
                    categoria_id = categorias_map[categoria_selecionada]
                    novo_modelo = {
                        "nome": nome_modelo,
                        "marca_id": marca_id,
                        "categoria_id": categoria_id
                    }
                    response = supabase.table("modelos").insert(novo_modelo).execute()
                    if response.data:
                        st.success(f"Modelo '{nome_modelo}' cadastrado com sucesso!")
                    else:
                        st.error(f"Erro ao salvar: {response.error.message}")
                except Exception as e:
                    st.error(f"Erro: {e}")

    # --- Criar Abas (Marcas, Categorias, Lojas) ---
    col_marcas, col_categorias, col_loja = st.columns(3)

    # --- Aba 1: Marcas ---
    with col_marcas:
        st.subheader("Cadastrar Nova Marca")
        with st.form("form_marca", clear_on_submit=True):
            nome_marca = st.text_input("Nome da Marca")
            submitted_marca = st.form_submit_button("Salvar Marca")
        if submitted_marca:
            if not nome_marca:
                st.error("Por favor, preencha o nome da marca.")
            else:
                try:
                    response = supabase.table("marcas").insert({"nome": nome_marca}).execute()
                    if response.data:
                        st.cache_data.clear() # Limpa o cache para atualizar o form de modelos
                        st.rerun()  # Recarrega a página para atualizar os dados
                    else:
                        st.error(f"Erro ao salvar: {response.error.message}")
                except Exception as e:
                    st.error(f"Erro: {e}")

    # --- Aba 2: Categorias ---
    with col_categorias:
        st.subheader("Cadastrar Nova Categoria")
        with st.form("form_categoria", clear_on_submit=True):
            nome_categoria = st.text_input("Nome da Categoria")
            submitted_categoria = st.form_submit_button("Salvar Categoria")
        if submitted_categoria:
            if not nome_categoria:
                st.error("Por favor, preencha o nome da categoria.")
            else:
                try:
                    response = supabase.table("categorias").insert({"nome": nome_categoria}).execute()
                    if response.data:
                        st.cache_data.clear() # Limpa o cache para atualizar o form de modelos
                        st.rerun()  # Recarrega a página para atualizar os dados
                    else:
                        st.error(f"Erro ao salvar: {response.error.message}")
                except Exception as e:
                    st.error(f"Erro: {e}")

    # --- Aba 3: Lojas ---
    with col_loja:
        st.subheader("Cadastrar Nova Loja")
        with st.form("form_loja", clear_on_submit=True):
            nome_loja = st.text_input("Nome da Loja")
            submitted_loja = st.form_submit_button("Salvar Loja")
        if submitted_loja:
            if not nome_loja:
                st.error("Por favor, preencha o nome da loja.")
            else:
                try:
                    response = supabase.table("lojas").insert({"nome": nome_loja}).execute()
                    if response.data:
                        st.cache_data.clear()
                    else:
                        st.error(f"Erro ao salvar: {response.error.message}")
                except Exception as e:
                    st.error(f"Erro: {e}")

# --- Gerenciamento ---
with tab_geral:
    st.header("Visualizar e Editar Cadastros Gerais")
    st.info("Aqui você pode visualizar e editar os nomes de Marcas e Categorias existentes.")

    ger_marcas, ger_categorias, ger_lojas, ger_modelos = st.tabs(["Marcas","Categorias","Lojas","Modelos"])

    # --- 1. SEÇÃO MARCAS ---
    with ger_marcas:
        # --- 1a. Carregar Marcas ---
        @st.cache_data
        def carregar_marcas():
            data = supabase.table("marcas").select("id, nome").order("nome").execute().data
            return pd.DataFrame(data)
        
        try:
            df_marcas = carregar_marcas()
        except Exception as e:
            st.error(f"Erro ao carregar marcas: {e}")
            st.stop()

        # --- 1b. Editar Marcas (Data Editor) ---
        with st.form("form_edit_marcas"):
            st.write("Visualizar e Editar Marcas:")
            edited_df_marcas = st.data_editor(
                df_marcas,
                key="editor_marcas", # Chave única
                num_rows="fixed",
                disabled=["id"],
                width="stretch"
            )
            submit_edit_marcas = st.form_submit_button("Salvar Alterações de Marcas")

        if submit_edit_marcas:
            updates_count = 0

            for index, row in edited_df_marcas.iterrows():
                original_row = df_marcas.iloc[index]

                if not row.equals(original_row):
                    item_id = row["id"]
                    updates = row.to_dict(); del updates["id"]

                    try:
                        supabase.table("marcas").update(updates).eq("id", item_id).execute()
                        updates_count += 1
                    except Exception as e:
                        st.error(f"Erro ao atualizar marca ID {item_id}: {e}")

            if updates_count > 0:
                st.success(f"{updates_count} marca(s) atualizada(s)!")
                st.cache_data.clear()
            else:
                st.info("Nenhuma alteração detectada em Marcas.")

    # --- 2. SEÇÃO CATEGORIAS ---
    with ger_categorias:
        # --- 2a. Carregar Categorias ---
        @st.cache_data
        def carregar_categorias():
            data = supabase.table("categorias").select("id, nome").order("nome").execute().data
            return pd.DataFrame(data)
        
        try:
            df_categorias = carregar_categorias()
        except Exception as e:
            st.error(f"Erro ao carregar categorias: {e}")
            st.stop()

        # --- 2b. Editar Categorias (Data Editor) ---
        with st.form("form_edit_categorias"):
            st.write("Visualizar e Editar Categorias:")
            edited_df_cats = st.data_editor(
                df_categorias,
                key="editor_categorias", # Chave única
                num_rows="fixed",
                disabled=["id"],
                width="stretch"
            )
            submit_edit_cats = st.form_submit_button("Salvar Alterações de Categorias")
        if submit_edit_cats:
            updates_count = 0

            for index, row in edited_df_cats.iterrows():
                original_row = df_categorias.iloc[index]

                if not row.equals(original_row):
                    item_id = row["id"]
                    updates = row.to_dict(); del updates["id"]

                    try:
                        supabase.table("categorias").update(updates).eq("id", item_id).execute()
                        updates_count += 1
                    except Exception as e:
                        st.error(f"Erro ao atualizar categoria ID {item_id}: {e}")

            if updates_count > 0:
                st.success(f"{updates_count} categoria(s) atualizada(s)!")
                st.cache_data.clear()
            else:
                st.info("Nenhuma alteração detectada em Categorias.")

    # --- 3. SEÇÃO LOJAS ---
    with ger_lojas:
        @st.cache_data
        def carregar_lojas():
            data = supabase.table("lojas").select("id, nome").order("nome").execute().data
            return pd.DataFrame(data)
        
        try:
            df_lojas = carregar_lojas()
        except Exception as e:
            st.error(f"Erro ao carregar lojas: {e}")
            st.stop()

        with st.form("form_edit_lojas"): # form_edit_lojas
            st.write("Editar Lojas:")
            edited_df_lojas = st.data_editor( # edited_df_lojas
                df_lojas, key="editor_lojas", num_rows="fixed",
                disabled=["id"], width="stretch"
            )
            submit_edit_lojas = st.form_submit_button("Salvar Alterações de Lojas")

        if submit_edit_lojas:
            updates_count = 0

            for index, row in edited_df_lojas.iterrows():
                original_row = df_lojas.iloc[index]

                if not row.equals(original_row):
                    item_id = row["id"]
                    updates = row.to_dict(); del updates["id"]

                    try:
                        supabase.table("lojas").update(updates).eq("id", item_id).execute()
                        updates_count += 1
                    except Exception as e:
                        st.error(f"Erro ao atualizar loja ID {item_id}: {e}")
            
            if updates_count > 0:
                st.success(f"{updates_count} loja(s) atualizada(s)!")
                st.cache_data.clear()
            else:
                st.info("Nenhuma alteração detectada em Lojas.")

    # --- 4. SEÇÃO MODELOS ---
    with ger_modelos:
        # --- 4a. Carregar Todos os Dados de Modelos ---
        @st.cache_data
        def carregar_dados_modelos_completos():
            modelos = supabase.table("modelos").select("id, nome, categoria_id, marca_id").order("nome").execute().data
            marcas = supabase.table("marcas").select("id, nome").order("nome").execute().data
            categorias = supabase.table("categorias").select("id, nome").order("nome").execute().data
            return modelos, marcas, categorias
        
        try:
            modelos_data, marcas_data, categorias_data = carregar_dados_modelos_completos()

            # --- 4b. Criar Mapeamentos de Tradução ---
            marcas_map = {m['nome']: m['id'] for m in marcas_data}
            categorias_map = {c['nome']: c['id'] for c in categorias_data}
            marcas_map_inv = {m['id']: m['nome'] for m in marcas_data}
            categorias_map_inv = {c['id']: c['nome'] for c in categorias_data}

            # Listas de nomes para os dropdowns
            lista_nomes_marcas = list(marcas_map.keys())
            lista_nomes_categorias = list(categorias_map.keys())
        except Exception as e:
            st.error(f"Erro ao carregar dados dos modelos: {e}")
            st.stop()

        st.subheader("Editar Modelos Existentes")
        
        # --- 4c. FILTRO DE CATEGORIA (Externo) ---
        categoria_filtro_nome = st.selectbox(
            "1. Filtrar por Categoria", 
            options=lista_nomes_categorias,
            index=None,
            placeholder="Selecione uma categoria para ver os modelos...",
            key="filtro_cat_modelos_edit"
        )

        # --- 4d. O DATA EDITOR (Aparece se filtrar) ---
        if categoria_filtro_nome:
            categoria_filtro_id = categorias_map[categoria_filtro_nome]
            modelos_filtrados = [
                m for m in modelos_data if m.get('categoria_id') == categoria_filtro_id
            ]
            if not modelos_filtrados:
                st.info("Nenhum modelo encontrado para esta categoria.")
                st.stop()

            df_para_editar = pd.DataFrame(modelos_filtrados)
            df_para_editar['marca'] = df_para_editar['marca_id'].map(marcas_map_inv)
            df_para_editar['categoria'] = df_para_editar['categoria_id'].map(categorias_map_inv)

            with st.form("form_edit_modelo"):
                st.write(f"Editando Modelos da Categoria: **{categoria_filtro_nome}**")

                edited_df = st.data_editor(
                    df_para_editar,
                    key="editor_modelos",
                    column_config={
                        "id": None,
                        "categoria_id": None,
                        "marca_id": None,

                        "nome": st.column_config.TextColumn("Modelo", required=True),

                        "marca": st.column_config.SelectboxColumn(
                            "Marca",
                            options=lista_nomes_marcas,
                            required=True
                        ),

                        "categoria": st.column_config.SelectboxColumn(
                            "Categoria",
                            options=lista_nomes_categorias,
                            required=True
                        )
                    },
                    num_rows="fixed",
                    width="stretch",
                    hide_index=True,
                )

                submitted_edit = st.form_submit_button("Salvar Alterações de Modelos")
            if submitted_edit:
                try:
                    updates_count = 0

                    for index, row in edited_df.iterrows():
                        item_id = row["id"]

                        dados_para_salvar = {
                            "nome": row["nome"],
                            "marca_id": marcas_map[row["marca"]],
                            "categoria_id": categorias_map[row["categoria"]]
                        }

                        if pd.isna(item_id):
                            supabase.table("modelos").insert(dados_para_salvar).execute()
                            updates_count += 1
                        else:
                            original_row = df_para_editar.iloc[index]

                            if not row.equals(original_row):
                                supabase.table("modelos").update(dados_para_salvar).eq("id", item_id).execute()
                                updates_count += 1

                    if updates_count > 0:
                        st.success(f"{updates_count} alterações salvas com sucesso!")
                        st.cache_data.clear()
                    else:
                        st.info("Nenhuma alteração detectada.")

                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
                    st.info("Verifique se algum campo obrigatório (Marca, Categoria) ficou vazio.")
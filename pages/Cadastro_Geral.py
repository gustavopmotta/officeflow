import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- Conexão com Supabase ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- Função de Carregamento ---
@st.cache_data
def carregar_opcoes_modelo():
    marcas = supabase.table("marcas").select("id, nome").execute().data
    categorias = supabase.table("categorias").select("id, nome").execute().data
    return marcas, categorias

# --- Título da Página ---
st.title("Cadastro Geral")
st.info("Utilize esta página para gerenciar os itens que aparecem nos menus suspensos do cadastro de ativos.")
st.set_page_config(page_title="Cadastro Geral", layout="wide")

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

tab_cadastro, tab_geral = st.tabs(["Cadastrar","Gerenciar"])

with tab_cadastro:
    st.subheader("Cadastrar Novo Modelo")

    if not marcas_map or not categorias_map:
        st.warning("É necessário cadastrar ao menos uma Marca e uma Categoria antes de cadastrar um Modelo.")
    else:
        with st.form("form_modelo", clear_on_submit=True):
            nome_modelo = st.text_input("Nome do Modelo")

            # Menus suspensos com dados carregados no início
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

    # --- Criar Abas (Tabs) ---
    col_marcas, col_categorias, col_setores = st.columns(3)

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

    # --- Aba 3: Setores ---
    with col_setores:
        st.subheader("Cadastrar Novo Setor")
        with st.form("form_setor", clear_on_submit=True):
            nome_setor = st.text_input("Nome do Setor")
            submitted_setor = st.form_submit_button("Salvar Setor")

        if submitted_setor:
            if not nome_setor:
                st.error("Por favor, preencha o nome do setor.")
            else:
                try:
                    response = supabase.table("setores").insert({"nome": nome_setor}).execute()
                    if response.data:
                        st.success(f"Setor '{nome_setor}' cadastrado com sucesso!")
                        # Não precisa limpar o cache aqui, pois setores não são usados em "Modelos"
                    else:
                        st.error(f"Erro ao salvar: {response.error.message}")
                except Exception as e:
                    st.error(f"Erro: {e}")

with tab_geral:
    st.header("Visualizar e Editar Cadastros Gerais")
    st.info("Aqui você pode visualizar e editar os nomes de Marcas, Categorias e Setores existentes.")

    col_1, col_2, col_3 = st.columns(3)

    # --- 1. SEÇÃO MARCAS ---
    with col_1:
        with st.expander("Gerenciar Marcas", expanded=False):
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
                    use_container_width=True
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
                    st.cache_data.clear(); st.rerun()
                else:
                    st.info("Nenhuma alteração detectada em Marcas.")

    # --- 2. SEÇÃO CATEGORIAS ---
    with col_2:
        with st.expander("Gerenciar Categorias", expanded=False):
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
                    use_container_width=True
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
                    st.cache_data.clear(); st.rerun()
                else:
                    st.info("Nenhuma alteração detectada em Categorias.")

    # --- 3. SEÇÃO SETORES ---
    with col_3:
        with st.expander("Gerenciar Setores", expanded=False):
            # --- 3a. Carregar Setores ---
            @st.cache_data
            def carregar_setores():
                data = supabase.table("setores").select("id, nome").order("nome").execute().data
                return pd.DataFrame(data)

            try:
                df_setores = carregar_setores()
            except Exception as e:
                st.error(f"Erro ao carregar setores: {e}")
                st.stop()

            # --- 3b. Editar Setores (Data Editor) ---
            with st.form("form_edit_setores"):
                st.write("Visualizar e Editar Setores:")
                edited_df_setores = st.data_editor(
                    df_setores,
                    key="editor_setores", # Chave única
                    num_rows="fixed",
                    disabled=["id"],
                    use_container_width=True
                )
                submit_edit_setores = st.form_submit_button("Salvar Alterações de Setores")

            if submit_edit_setores:
                updates_count = 0
                for index, row in edited_df_setores.iterrows():
                    original_row = df_setores.iloc[index]
                    if not row.equals(original_row):
                        item_id = row["id"]
                        updates = row.to_dict(); del updates["id"]
                        try:
                            supabase.table("setores").update(updates).eq("id", item_id).execute()
                            updates_count += 1
                        except Exception as e:
                            st.error(f"Erro ao atualizar setor ID {item_id}: {e}")

                if updates_count > 0:
                    st.success(f"{updates_count} setor(es) atualizado(s)!")
                    st.cache_data.clear(); st.rerun()
                else:
                    st.info("Nenhuma alteração detectada em Setores.")

    # --- 4. SEÇÃO MODELOS ---
    with st.expander("Gerenciar Modelos", expanded=False):
        
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

            # --- O PULO DO GATO: TRADUZIR IDs para NOMES ---
            # Criamos um DataFrame para o editor e "traduzimos" os IDs para nomes
            df_para_editar = pd.DataFrame(modelos_filtrados)
            df_para_editar['marca'] = df_para_editar['marca_id'].map(marcas_map_inv)
            df_para_editar['categoria'] = df_para_editar['categoria_id'].map(categorias_map_inv)

            with st.form("form_edit_modelo"):
                st.write(f"Editando Modelos da Categoria: **{categoria_filtro_nome}**")
                
                edited_df = st.data_editor(
                    df_para_editar,
                    key="editor_modelos",
                    # --- A MÁGICA ACONTECE AQUI ---
                    column_config={
                        "id": None, # Oculta a coluna de ID
                        "categoria_id": None, # Oculta a coluna de ID
                        "marca_id": None, # Oculta a coluna de ID
                        
                        "nome": st.column_config.TextColumn("Modelo", required=True),
                        
                        "marca": st.column_config.SelectboxColumn(
                            "Marca",
                            options=lista_nomes_marcas, # A lista de opções
                            required=True
                        ),
                        
                        "categoria": st.column_config.SelectboxColumn(
                            "Categoria",
                            options=lista_nomes_categorias, # A lista de opções
                            required=True
                        )
                    },
                    num_rows="dynamic", # Permite adicionar/deletar
                    use_container_width=True,
                    hide_index=True,
                )
                
                submitted_edit = st.form_submit_button("Salvar Alterações de Modelos")

            if submitted_edit:
                # --- O SEGUNDO PULO DO GATO: TRADUZIR NOMES de volta para IDs ---
                try:
                    updates_count = 0
                    # Itera sobre o DataFrame editado
                    for index, row in edited_df.iterrows():
                        # Pega o ID original (se existir) ou cria um novo
                        item_id = row["id"]
                        
                        # Traduz os nomes de volta para IDs
                        dados_para_salvar = {
                            "nome": row["nome"],
                            "marca_id": marcas_map[row["marca"]],       # "Dell" -> 6
                            "categoria_id": categorias_map[row["categoria"]] # "Notebook" -> 2
                        }

                        # Lógica para saber se é um update ou insert
                        # (O 'num_rows="dynamic"' permite criar novos, que vêm com id=NaN)
                        if pd.isna(item_id):
                            # É um item NOVO
                            supabase.table("modelos").insert(dados_para_salvar).execute()
                            updates_count += 1
                        else:
                            # É um item existente, vamos verificar se mudou
                            original_row = df_para_editar.iloc[index]
                            if not row.equals(original_row):
                                supabase.table("modelos").update(dados_para_salvar).eq("id", item_id).execute()
                                updates_count += 1
                    
                    if updates_count > 0:
                        st.success(f"{updates_count} alterações salvas com sucesso!")
                        st.cache_data.clear(); st.rerun()
                    else:
                        st.info("Nenhuma alteração detectada.")
                        
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
                    st.info("Verifique se algum campo obrigatório (Marca, Categoria) ficou vazio.")
        # --- 4a. Carregar Todos os Dados de Modelos ---
        @st.cache_data
        def carregar_dados_modelos_completos():
            modelos = supabase.table("modelos").select("id, nome, categoria_id, marca_id").order("nome").execute().data
            marcas = supabase.table("marcas").select("id, nome").order("nome").execute().data
            categorias = supabase.table("categorias").select("id, nome").order("nome").execute().data
            return modelos, marcas, categorias

        try:
            modelos_data, marcas_data, categorias_data = carregar_dados_modelos_completos()
            
            # --- 4b. Criar Mapeamentos (Dicionários) ---
            marcas_map = {m['nome']: m['id'] for m in marcas_data}
            categorias_map = {c['nome']: c['id'] for c in categorias_data}
            
            # Mapeamentos inversos (ID -> Nome) para preencher os formulários
            marcas_map_inv = {m['id']: m['nome'] for m in marcas_data}
            categorias_map_inv = {c['id']: c['nome'] for c in categorias_data}
            
            lista_nomes_marcas = list(marcas_map.keys())
            lista_nomes_categorias = list(categorias_map.keys())

        except Exception as e:
            st.error(f"Erro ao carregar dados dos modelos: {e}")
            st.stop()

        st.subheader("Editar Modelo Existente")
        st.info("Para editar um modelo, primeiro filtre por Categoria e depois selecione o Modelo.")

        # --- 4c. FILTRO DE CATEGORIA ---
        categoria_filtro_nome = st.selectbox(
            "1. Filtrar por Categoria", 
            options=lista_nomes_categorias,
            index=None,
            placeholder="Selecione uma categoria...",
            key="filtro_cat_modelos_edit"
        )

        modelos_filtrados_map = {}
        if categoria_filtro_nome:
            categoria_filtro_id = categorias_map[categoria_filtro_nome]
            modelos_filtrados = [
                m for m in modelos_data if m.get('categoria_id') == categoria_filtro_id
            ]
            modelos_filtrados_map = {m['nome']: m['id'] for m in modelos_filtrados}

        # --- 4d. SELETOR DE MODELO (FILTRADO) ---
        modelo_selecionado_nome = st.selectbox(
            "2. Selecione o Modelo para Editar",
            options=modelos_filtrados_map.keys(),
            index=None,
            placeholder="Selecione um modelo...",
            key="select_modelo_edit"
        )

        # --- 4e. FORMULÁRIO DE EDIÇÃO (Aparece se um modelo for selecionado) ---
        if modelo_selecionado_nome:
            modelo_id = modelos_filtrados_map[modelo_selecionado_nome]
            modelo_obj = next((m for m in modelos_data if m['id'] == modelo_id), None)

            if modelo_obj:
                # Encontra o índice (posição) da categoria e marca atuais
                try:
                    default_cat_index = lista_nomes_categorias.index(categorias_map_inv.get(modelo_obj['categoria_id']))
                    default_marca_index = lista_nomes_marcas.index(marcas_map_inv.get(modelo_obj['marca_id']))
                except (ValueError, KeyError):
                    st.error("Erro: A marca ou categoria deste modelo não foi encontrada. Verifique o cadastro.")
                    st.stop()

                with st.form("form_edit_modelo"):
                    st.subheader(f"Editando: {modelo_selecionado_nome}")
                    
                    nome_editado = st.text_input("Nome do Modelo", value=modelo_obj['nome'])
                    cat_editada_nome = st.selectbox(
                        "Categoria", options=lista_nomes_categorias, index=default_cat_index
                    )
                    marca_editada_nome = st.selectbox(
                        "Marca", options=lista_nomes_marcas, index=default_marca_index
                    )
                    
                    submitted_edit = st.form_submit_button("Salvar Alterações")

                if submitted_edit:
                    try:
                        dados_atualizados = {
                            "nome": nome_editado,
                            "categoria_id": categorias_map[cat_editada_nome],
                            "marca_id": marcas_map[marca_editada_nome]
                        }
                        supabase.table("modelos").update(dados_atualizados).eq("id", modelo_id).execute()
                        st.success("Modelo atualizado com sucesso!")
                        st.cache_data.clear(); st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {e}")
            else:
                st.warning("Modelo selecionado não encontrado. Por favor, recarregue a página.")
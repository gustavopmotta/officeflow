import streamlit as st
from supabase import create_client, Client
import pandas as pd

@st.cache_resource(ttl=600)
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

st.title("Gerenciar Ativos")
st.set_page_config(page_title="Gerenciar Ativos", layout="wide")

tab_lista, tab_cadastro = st.tabs(["Lista de Ativos", "Cadastrar Novo Ativo"])

def carregar_opcoes():
    modelos = supabase.table("modelos").select("id, categoria_id, nome").execute().data
    categorias = supabase.table("categorias").select("id, nome").execute().data
    setores = supabase.table("setores").select("id, nome").execute().data
    status = supabase.table("status").select("id, nome").execute().data
    estados = supabase.table("estados").select("id, nome").execute().data
    
    return modelos, categorias, setores, status, estados

def carregar_dados_completos():
    """Carrega os ativos e todas as tabelas relacionadas para tradução."""
    try:
        # 1. Carregar a tabela principal de ativos
        ativos = supabase.table("ativos").select("*").execute().data
        
        # 2. Carregar tabelas de "lookup"
        # Precisamos de modelos com suas marcas para o nome formatado
        modelos = supabase.table("modelos").select("id, nome, categoria_id, marcas(nome)").order("nome").execute().data
        categorias = supabase.table("categorias").select("id, nome").order("nome").execute().data
        usuarios = supabase.table("usuarios").select("id, nome").order("nome").execute().data
        setores = supabase.table("setores").select("id, nome").order("nome").execute().data
        status = supabase.table("status").select("id, nome").order("nome").execute().data
        estados = supabase.table("estados").select("id, nome").order("nome").execute().data
        
        return ativos, modelos, categorias, usuarios, setores, status, estados
        
    except Exception as e:
        st.error(f"Erro fatal ao carregar dados: {e}")
        return [], [], [], [], [], [], []

with tab_cadastro:
    try:
        modelos, categorias, setores, status, estados = carregar_opcoes()

        # --- Criar Mapeamentos ---
        # Precisamos de um dicionário (map) para converter o NOME selecionado
        # de volta para o ID que será salvo no banco.
        # Ex: 'Notebook Dell' -> 14
        categorias_map = {c['nome']: c['id'] for c in categorias}
        setores_map = {s['nome']: s['id'] for s in setores}
        status_map = {s['nome']: s['id'] for s in status}
        estados_map = {e['nome']: e['id'] for e in estados}

        if not categorias_map:
            st.error("É necessário cadastrar ao menos uma Categoria antes de cadastrar um Ativo.")

        else:
        # --- Formulário de Cadastro ---
            st.subheader("1. Categoria do Ativo")
            categoria_selecionada = st.selectbox("Categoria do Ativo", options=categorias_map.keys(), label_visibility="collapsed")

            if categoria_selecionada:
                # Encontra o ID da categoria selecionada
                categoria_id_selecionada = categorias_map[categoria_selecionada]

                # Cria uma lista de modelos que pertencem a essa categoria
                modelos_filtrados = [
                    m for m in modelos 
                    if m.get('categoria_id') == categoria_id_selecionada
                ]
                # Cria o mapa apenas com os modelos filtrados
                modelos_filtrados_map = {m['nome']: m['id'] for m in modelos_filtrados}
            else:
                # Se nenhuma categoria for selecionada, o mapa de modelos fica vazio
                modelos_filtrados_map = {}

            st.subheader("2. Informações do Ativo")   
            with st.form("form_cadastro_ativo", clear_on_submit=True):


                # --- Inputs do Formulário ---
                serial_input = st.text_input("Serial Number (ou Patrimônio)", key="serial")

                # Usamos .keys() para mostrar os nomes no dropdown
                modelo_selecionado = st.selectbox("Modelo", options=modelos_filtrados_map.keys())
                setor_selecionado = st.selectbox("Setor", options=setores_map.keys())
                status_selecionado = st.selectbox("Status", options=status_map.keys())
                estado_selecionado = st.selectbox("Estado", options=estados_map.keys())

                # --- Botão de Envio ---
                submitted = st.form_submit_button("Cadastrar Ativo")

            # --- Lógica de Submissão (Fora do 'with st.form') ---
            if submitted:
                if not serial_input or not modelo_selecionado:
                    st.error("Os campos 'Serial' e 'Modelo' são obrigatórios.")
                else:
                    # Converter os NOMES selecionados de volta para IDs
                    try:
                        novo_ativo = {
                            "serial": serial_input,
                            # 7. Modificado: Usamos o mapa filtrado para obter o ID
                            "modelo_id": modelos_filtrados_map[modelo_selecionado], 
                            "local_id": setores_map[setor_selecionado],
                            "status_id": status_map[status_selecionado],
                            "estado_id": estados_map[estado_selecionado]
                        }

                        # Inserir no Supabase
                        response = supabase.table("ativos").insert(novo_ativo).execute()

                        if response.data:
                            st.success("Ativo cadastrado com sucesso!")
                        else:
                            # Tenta mostrar o erro específico do banco
                            st.error(f"Erro ao cadastrar: {response.error.message}")

                    except Exception as e:
                        st.error(f"Ocorreu um erro ao processar os dados: {e}")

    except Exception as e:
        st.error(f"Não foi possível carregar as opções de cadastro: {e}")

with tab_lista:
    try:
        ativos_data, modelos_data, categorias_data, usuarios_data, setores_data, status_data, estados_data = carregar_dados_completos()

        if not all([modelos_data, categorias_data, usuarios_data, setores_data, status_data, estados_data]):
            st.warning("Faltam dados cadastrais (modelos, usuários, etc.). Verifique o 'Cadastro Geral'.")
            st.stop()

        # --- 1. Criar os Mapas de "Tradução" ---
        categorias_map = {c['nome']: c['id'] for c in categorias_data}
        usuarios_map = {u['nome']: u['id'] for u in usuarios_data}
        setores_map = {s['nome']: s['id'] for s in setores_data}
        status_map = {s['nome']: s['id'] for s in status_data}
        estados_map = {e['nome']: e['id'] for e in estados_data}
        usuarios_map_inv = {u['id']: u['nome'] for u in usuarios_data}
        setores_map_inv = {s['id']: s['nome'] for s in setores_data}
        status_map_inv = {s['id']: s['nome'] for s in status_data}
        estados_map_inv = {e['id']: e['nome'] for e in estados_data}

        modelos_map = {}
        modelos_map_inv = {}
        modelos_por_categoria = {}

        for m in modelos_data:
            marca_nome = m.get('marcas', {}).get('nome', 'Sem Marca')
            display_name = f"{marca_nome} - {m['nome']}"
            modelos_map[display_name] = m['id']
            modelos_map_inv[m['id']] = display_name
            cat_id = m.get('categoria_id')
            if cat_id not in modelos_por_categoria:
                modelos_por_categoria[cat_id] = []
            modelos_por_categoria[cat_id].append(m)

        lista_nomes_modelos = list(modelos_map.keys())
        lista_nomes_usuarios = list(usuarios_map.keys())
        lista_nomes_setores = list(setores_map.keys())
        lista_nomes_status = list(status_map.keys())
        lista_nomes_estados = list(estados_map.keys())

    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        st.stop()

    # --- 2. Filtro de Categoria (OPCIONAL) ---
    st.subheader("Filtrar Ativos por Categoria")
    
    opcoes_filtro = ["Todas as Categorias"] + list(categorias_map.keys())
    categoria_filtro_nome = st.selectbox(
        "Selecione uma categoria para filtrar a lista",
        options=opcoes_filtro,
        index=0
    )

    # --- 3. Lógica de Filtragem ---
    ativos_filtrados = []
    lista_nomes_modelos_filtrada = lista_nomes_modelos 

    if categoria_filtro_nome and categoria_filtro_nome != "Todas as Categorias":
        categoria_filtro_id = categorias_map[categoria_filtro_nome]
        modelos_nesta_categoria_ids = [m['id'] for m in modelos_por_categoria.get(categoria_filtro_id, [])]
        ativos_filtrados = [a for a in ativos_data if a.get('modelo_id') in modelos_nesta_categoria_ids]
        lista_nomes_modelos_filtrada = [modelos_map_inv[m_id] for m_id in modelos_nesta_categoria_ids if m_id in modelos_map_inv]
    else:
        ativos_filtrados = ativos_data

    # --- 4. Exibição da Tabela ---
    if not ativos_filtrados:
        st.info(f"Nenhum ativo encontrado.")
    else:
        df_ativos = pd.DataFrame(ativos_filtrados)
        df_display = pd.DataFrame()
        df_display['id'] = df_ativos['id']
        df_display['serial'] = df_ativos['serial']
        df_display['modelo'] = df_ativos['modelo_id'].map(modelos_map_inv)
        df_display['status'] = df_ativos['status_id'].map(status_map_inv)
        df_display['usuario'] = df_ativos['usuario_id'].map(usuarios_map_inv)
        df_display['local'] = df_ativos['local_id'].map(setores_map_inv)
        df_display['estado'] = df_ativos['estado_id'].map(estados_map_inv)
        df_display['valor'] = df_ativos['valor'] 
        df_display['compra_id'] = df_ativos['compra_id'] 

        # --- O Data Editor ---
        with st.form("form_edit_ativos"):
            st.subheader(f"Editando Ativos: {categoria_filtro_nome}")

            edited_df = st.data_editor(
                df_display, width="stretch", height="stretch",
                key="editor_ativos",
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                disabled=["id", "compra_id"], 
                column_config={
                    "serial": st.column_config.TextColumn("Serial", required=True),
                    
                    "valor": st.column_config.NumberColumn(
                        "Valor (R$)", format="R$ %.2f"
                    ),
                    
                    "modelo": st.column_config.SelectboxColumn(
                        "Modelo",
                        options=lista_nomes_modelos_filtrada,
                        required=True
                    ),

                    "status": st.column_config.SelectboxColumn(
                        "Status", options=lista_nomes_status, required=True
                    ),

                    "usuario": st.column_config.SelectboxColumn(
                        "Usuário", options=lista_nomes_usuarios, required=False 
                    ),

                    "local": st.column_config.SelectboxColumn(
                        "Local", options=lista_nomes_setores, required=True
                    ),

                    "estado": st.column_config.SelectboxColumn(
                        "Condição", options=lista_nomes_estados, required=True
                    ),

                    "id": st.column_config.NumberColumn("ID"),
                    "compra_id": None,
                }
            )

            submit_button = st.form_submit_button("Salvar Alterações")

        # --- 5. Lógica de Salvamento ---
        if submit_button:
            with st.spinner("Salvando alterações..."):
                updates_count = 0
                errors = []

                for index, row in edited_df.iterrows():
                    item_id = int(row["id"])
                    original_row = df_display[df_display['id'] == item_id].iloc[0]

                    if not row.equals(original_row):
                        try:
                            updates = {
                                "serial": row["serial"],
                                "valor": row["valor"],
                                "modelo_id": modelos_map.get(row["modelo"]),
                                "status_id": status_map.get(row["status"]),
                                "usuario_id": usuarios_map.get(row["usuario"]), 
                                "local_id": setores_map.get(row["local"]),
                                "estado_id": estados_map.get(row["estado"])
                            }

                            supabase.table("ativos").update(updates).eq("id", item_id).execute()
                            updates_count += 1
                        except Exception as e:
                            errors.append(f"ID {item_id}: {e}")

                if updates_count > 0:
                    st.success(f"{updates_count} ativo(s) atualizado(s) com sucesso!")
                    st.cache_data.clear() 
                    st.rerun()
                elif errors:
                    st.error(f"Erros ao salvar: {errors}")
                else:
                    st.info("Nenhuma alteração detectada.")
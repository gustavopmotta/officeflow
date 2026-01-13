from utils import verificar_autenticacao
import streamlit as st
import pandas as pd

# --- Conexão com Supabase ---
supabase = verificar_autenticacao()

# --- Função de Carregamento Centralizada e com Cache ---
def fetch_table(table_name, select_query="*"):
    return supabase.table(table_name).select(select_query).execute().data

def carregar_dados_sistema():
    try:
        dados = {
            "ativos": fetch_table("ativos"),
            "categorias": fetch_table("categorias", "id, nome"),
            "setores": fetch_table("setores", "id, nome"),
            "status": fetch_table("status", "id, nome"),
            "estados": fetch_table("estados", "id, nome"),
            "usuarios": fetch_table("usuarios", "id, nome"),
            "modelos": fetch_table("modelos", "id, nome, categoria_id, marcas(nome)")
        }
        return dados
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

# --- Carregamento ---
st.title("Gerenciar Ativos")
dados = carregar_dados_sistema()

if not dados:
    st.stop()

def criar_mapas(lista_dados, chave_valor="id", chave_nome="nome"):
    map_inv = {item[chave_valor]: item[chave_nome] for item in lista_dados}
    map_dir = {item[chave_nome]: item[chave_valor] for item in lista_dados}
    return map_inv, map_dir

# Processamento especial para Modelos (Nome + Marca)
lista_modelos_processada = []
for m in dados["modelos"]:
    marca = m.get('marcas', {}).get('nome', 'S/M')
    nome_completo = f"{marca} - {m['nome']}"
    lista_modelos_processada.append({
        "id": m["id"], 
        "nome": nome_completo, 
        "categoria_id": m["categoria_id"]
    })

# Mapas Gerais
map_cats_inv, map_cats = criar_mapas(dados["categorias"])
map_setor_inv, map_setor = criar_mapas(dados["setores"])
map_status_inv, map_status = criar_mapas(dados["status"])
map_estado_inv, map_estado = criar_mapas(dados["estados"])
map_user_inv, map_user = criar_mapas(dados["usuarios"])
map_model_inv, map_model = criar_mapas(lista_modelos_processada)

# --- Interface ---
tab_lista, tab_cadastro = st.tabs(["Lista de Ativos", "Cadastrar Novo"])

# --- ABA 01: Lista (Edição) ---
with tab_lista:
    if not dados["ativos"]:
        st.info("Nenhum ativo cadastrado.")
    else:
        # 1. Filtros
        col_f1, col_f2 = st.columns([1, 3])
        cat_filtro = col_f1.selectbox("Filtrar por Categoria", ["Todas"] + list(map_cats.keys()))
        
        # 2. Prepara DataFrame
        df = pd.DataFrame(dados["ativos"])
        
        # Aplica Filtro (usando Pandas é mais rápido)
        if cat_filtro != "Todas":
            id_cat = map_cats[cat_filtro]
            # Pega IDs de modelos dessa categoria
            ids_mods = [m['id'] for m in lista_modelos_processada if m['categoria_id'] == id_cat]
            df = df[df['modelo_id'].isin(ids_mods)]

        # 3. Mapeamento Visual (Substitui IDs por Nomes)
        df_view = pd.DataFrame()
        df_view["id"] = df["id"]
        df_view["serial"] = df["serial"]
        df_view["valor"] = df["valor"]
        df_view["modelo"] = df["modelo_id"].map(map_model_inv)
        df_view["status"] = df["status_id"].map(map_status_inv)
        df_view["usuario"] = df["usuario_id"].map(map_user_inv)
        df_view["local"] = df["local_id"].map(map_setor_inv)
        df_view["estado"] = df["estado_id"].map(map_estado_inv)

        # 4. Data Editor
        edited_df = st.data_editor(
            df_view,
            width="stretch",
            hide_index=True,
            num_rows="fixed",
            disabled=["id"],
            column_config={
                "id": None,
                "serial": st.column_config.TextColumn("Serial", disabled=True),
                "modelo": st.column_config.SelectboxColumn("Modelo", options=list(map_model.keys()), required=True),
                "local": st.column_config.SelectboxColumn("Local", options=list(map_setor.keys()), required=True, disabled=True),
                "estado": st.column_config.SelectboxColumn("Estado", options=list(map_estado.keys()), required=True, disabled=True),
                "status": st.column_config.SelectboxColumn("Status", options=list(map_status.keys()), required=True, disabled=True),
                "usuario": st.column_config.SelectboxColumn("Usuário", options=list(map_user.keys()), disabled=True),
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")
            }
        )

        # 5. Salvar Alterações
        if st.button("Salvar Alterações da Tabela"):
            updates_count = 0

            for i, row in edited_df.iterrows():
                item_id = int(row["id"])
                original = df[df['id'] == item_id].iloc[0]
                novo_modelo_id = map_model.get(row["modelo"])
                
                payload = {
                    "serial": row["serial"],
                    "valor": row["valor"],
                    "modelo_id": novo_modelo_id,
                }
                
                try:
                    supabase.table("ativos").update(payload).eq("id", item_id).execute()
                    updates_count += 1
                except Exception as e:
                    st.error(f"Erro no ID {item_id}: {e}")

            if updates_count > 0:
                st.success("Dados atualizados!")
                st.cache_data.clear()
                st.rerun()

# --- ABA 2: Cadastro ---
with tab_cadastro:
    if not map_cats:
        st.warning("Cadastre categorias primeiro.")
    else:
        st.subheader("Novo Ativo")
        
        sel_cat = st.selectbox("1. Selecione a Categoria do Ativo", list(map_cats.keys()))
        
        id_cat_sel = map_cats[sel_cat]
        modelos_filtrados = [m['nome'] for m in lista_modelos_processada if m['categoria_id'] == id_cat_sel]
        
        st.divider()
        
        with st.form("form_add", clear_on_submit=True):
            st.markdown("##### 2. Dados do Equipamento")
            
            c1, c2, c3 = st.columns(3)
            serial = c1.text_input("Serial / Patrimônio")
            modelo = c2.selectbox("Modelo", modelos_filtrados if modelos_filtrados else [], placeholder="Selecione o modelo...")
            valor_input = c3.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f") # NOVO CAMPO

            c4, c5, c6, c7 = st.columns(4)
            
            lista_users_opcoes = ["Nenhum"] + list(map_user.keys())
            usuario_inicial = c4.selectbox("Usuário Inicial", lista_users_opcoes)
            
            setor = c5.selectbox("Setor / Local", list(map_setor.keys()))
            status = c6.selectbox("Status", list(map_status.keys()))
            estado = c7.selectbox("Condição (Estado)", list(map_estado.keys()))
            
            if st.form_submit_button("Cadastrar Ativo"):
                if not serial or not modelo:
                    st.error("Os campos 'Serial' e 'Modelo' são obrigatórios.")
                else:
                    try:
                        id_usuario_salvar = map_user[usuario_inicial] if usuario_inicial != "Nenhum" else None

                        novo_ativo = {
                            "serial": serial,
                            "valor": valor_input,
                            "modelo_id": map_model[modelo],
                            "usuario_id": id_usuario_salvar,
                            "local_id": map_setor[setor],
                            "status_id": map_status[status],
                            "estado_id": map_estado[estado]
                        }
                        
                        supabase.table("ativos").insert(novo_ativo).execute()
                        
                        st.success(f"Ativo '{serial}' cadastrado com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erro ao cadastrar: {e}")
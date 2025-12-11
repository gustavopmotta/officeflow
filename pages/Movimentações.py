from utils import sidebar_global, verificar_autenticacao
import streamlit as st
import pandas as pd

# --- Conexão com Supabase ---
supabase = verificar_autenticacao()

# --- Configuração da Página ---
st.set_page_config(page_title="Movimentações", layout="wide")
sidebar_global()

# --- Carregar Dados Auxiliares ---
def carregar_dados_auxiliares():
    try:
        ativos = supabase.table("ativos").select("id, serial, usuario_id, local_id, status_id(nome), modelo_id(nome, marca_id(nome))").order("status_id").execute().data
        usuarios = supabase.table("usuarios").select("id, nome").order("nome").execute().data
        setores = supabase.table("setores").select("id, nome").order("nome").execute().data 
        status = supabase.table("status").select("id, nome").order("nome").execute().data
        
        return ativos, usuarios, setores, status
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return [], [], [], []

# --- Carrega os dados ---
ativos_data, usuarios_data, setores_data, status_data = carregar_dados_auxiliares()

# --- Formatação do nome
ativos_map = {}
for a in ativos_data:
    # Valores padrão caso algo venha vazio
    nome_modelo = "Modelo Desconhecido"
    nome_marca = "Marca Desconhecida"
    nome_status = "Status Desconhecido"
    
    # 1. Acessa o objeto "modelos"
    dados_modelo = a.get("modelo_id")
    dados_status = a.get("status_id")
    
    # Verifica se existe um modelo vinculado e se é um dicionário
    if dados_modelo and isinstance(dados_modelo, dict):
        nome_modelo = dados_modelo.get("nome", "S/M")
        dados_marca = dados_modelo.get("marca_id")
        
        if dados_marca and isinstance(dados_marca, dict):
            nome_marca = dados_marca.get("nome", "S/M")
    
    if dados_status and isinstance(dados_status, dict):
        nome_status = dados_status.get("nome","S/M")

    serial = a["serial"]
    label = f"S/M: {nome_marca} {nome_modelo} (SN: {serial}) - {nome_status}"
    
    ativos_map[label] = a

# --- Mapas de "Tradução" (ID <-> Nome) ---
usuarios_map = {u["nome"]: u["id"] for u in usuarios_data}
setores_map = {s["nome"]: s["id"] for s in setores_data}
status_map = {s["nome"]: s["id"] for s in status_data}

usuarios_map_inv = {u["id"]: u["nome"] for u in usuarios_data}
setores_map_inv = {s["id"]: s["nome"] for s in setores_data}
status_map_inv = {s["id"]: s["nome"] for s in status_data}

# Listas de Nomes (para dropdowns)
lista_usuarios = ["Nenhum (Estoque)"] + list(usuarios_map.keys())
lista_setores = list(setores_map.keys())
lista_status = list(status_map.keys())


# --- Interface Principal ---
st.title("Movimentação de Ativos")

tab_movimentar, tab_historico = st.tabs(["Realizar Movimentação", "Histórico de Movimentações"])

# --- Aba 1: Realizar Movimentação ---
with tab_movimentar:
    st.subheader("1. Selecione o Ativo")
    
    serial_selecionado = st.selectbox(
        "Buscar por Serial Number",
        options=ativos_map.keys(),
        index=None,
        placeholder="Digite ou selecione o serial do ativo..."
    )
    
    if serial_selecionado:
        ativo_atual = ativos_map[serial_selecionado]
        
        st.subheader("2. Status Atual do Ativo")

        def extrair_id(dado):
            if isinstance(dado, dict):
                return dado.get("id")
            return dado
        
        id_usuario_origem = extrair_id(ativo_atual.get("usuario_id"))
        id_local_origem = extrair_id(ativo_atual.get("local_id"))
        id_status_origem = extrair_id(ativo_atual.get("status_id"))
        
        nome_usuario_origem = usuarios_map_inv.get(id_usuario_origem, "Nenhum (Estoque)")
        nome_local_origem = setores_map_inv.get(id_local_origem, "N/A")
        nome_status_origem = status_map_inv.get(id_status_origem, "N/A")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Usuário Atual", nome_usuario_origem)
        col2.metric("Setor Atual", nome_local_origem)
        col3.metric("Status Atual", nome_status_origem)
        
        st.divider()
        
        st.subheader("3. Mover Para:")
        with st.form("form_movimentacao"):
            
            col_d1, col_d2, col_d3 = st.columns(3)
            
            with col_d1:
                # CORREÇÃO: Verifica se o usuário de origem existe na lista. Se não (ex: é N/A), define índice 0
                idx_usuario = lista_usuarios.index(nome_usuario_origem) if nome_usuario_origem in lista_usuarios else 0
                
                nome_usuario_destino = st.selectbox(
                    "Novo Usuário", 
                    options=lista_usuarios, 
                    index=idx_usuario
                )
                
            with col_d2:
                # CORREÇÃO: Mesma verificação para setor
                idx_setor = lista_setores.index(nome_local_origem) if nome_local_origem in lista_setores else 0
                
                nome_local_destino = st.selectbox(
                    "Novo Setor", 
                    options=lista_setores, 
                    index=idx_setor
                )
                
            with col_d3:
                # CORREÇÃO: Mesma verificação para status (Resolve o erro do N/A)
                idx_status = lista_status.index(nome_status_origem) if nome_status_origem in lista_status else 0
                
                nome_status_destino = st.selectbox(
                    "Novo Status", 
                    options=lista_status, 
                    index=idx_status
                )
            
            observacao_input = st.text_area("Observação (Opcional)", placeholder="Ex: Devolvido para manutenção, tela quebrada.")
    
            submitted = st.form_submit_button("Confirmar Movimentação")
            
            if submitted:
                # ... (o restante do código de salvamento permanece igual)
                # "Traduzir" nomes de destino para IDs
                id_usuario_destino = usuarios_map.get(nome_usuario_destino) 
                id_local_destino = setores_map[nome_local_destino]
                id_status_destino = status_map[nome_status_destino]
                
                # --- LÓGICA DA "TRANSAÇÃO" ---
                with st.spinner("Processando movimentação..."):
                    try:
                        # 1. Cria o registro no "log" (tabela movimentacoes)
                        log_data = {
                            "ativo_id": ativo_atual['id'],
                            "usuario_id": id_usuario_destino,
                            "setor_id": id_local_destino,
                            "status_id": id_status_destino,
                            "observacao": observacao_input if observacao_input else None
                        }
                        supabase.table("movimentacoes").insert(log_data).execute()
                        
                        # 2. Atualiza o registro principal na tabela 'ativos'
                        update_data = {
                            "usuario_id": id_usuario_destino,
                            "local_id": id_local_destino,
                            "status_id": id_status_destino
                        }
                        supabase.table("ativos").update(update_data).eq("id", ativo_atual['id']).execute()
                        
                        st.success(f"Ativo {ativo_atual['serial']} movido com sucesso!")
                        st.cache_data.clear() 
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

# --- Aba 2: Histórico de Movimentações ---
with tab_historico:
    st.subheader("Histórico Completo de Movimentações")
    
    serial_filtro_hist = st.selectbox(
        "Filtrar histórico por Serial Number",
        options=["Todos os Ativos"] + list(ativos_map.keys()),
        index=0
    )
    
    with st.spinner("Carregando histórico..."):
        try:
            # --- QUERY AJUSTADA ---
            # Busca o log e traduz os IDs do *novo estado* para Nomes
            query = """
                created_at, observacao,
                ativos!inner(serial),
                usuarios:usuario_id(nome),
                setores:setor_id(nome),
                status:status_id(nome)
            """
            
            query_builder = supabase.table("movimentacoes").select(query).order("created_at", desc=True)
            
            if serial_filtro_hist != "Todos os Ativos":
                ativo_id_filtro = ativos_map[serial_filtro_hist]["id"]
                query_builder = query_builder.eq("ativo_id", ativo_id_filtro)
            
            historico_data = query_builder.execute().data
            
            if not historico_data:
                st.info("Nenhum histórico de movimentação encontrado.")
            else:
                # --- DATAFRAME AJUSTADO ---
                # Remove as colunas "De" e "Para" e mostra apenas o estado registrado
                df_list = []
                for item in historico_data:
                    df_list.append({
                        "Data": pd.to_datetime(item["created_at"]).strftime("%d/%m/%Y %H:%M"),
                        "Serial": item["ativos"]["serial"],
                        "Usuário": item["usuarios"]["nome"] if item["usuarios"] else "Estoque",
                        "Local": item["setores"]["nome"] if item["setores"] else "N/A",
                        "Status": item["status"]["nome"] if item["status"] else "N/A",
                        "Obs": item["observacao"]
                    })
                
                df_historico = pd.DataFrame(df_list)
                st.dataframe(df_historico, width="stretch", hide_index=True)

        except Exception as e:
            st.error(f"Erro ao carregar histórico: {e}")
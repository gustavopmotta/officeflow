from utils import verificar_autenticacao
import streamlit as st
import pandas as pd

# --- Conexão com Supabase ---
supabase = verificar_autenticacao()

# --- Carregar Dados Auxiliares ---
def carregar_dados_auxiliares():
    try:
        query = """
            id, serial, usuario_id, local_id, status_id,
            status_dados:status_id(nome),
            modelo_id(nome, marca_id(nome))
        """
        ativos = supabase.table("ativos").select(query).order("id").execute().data
        
        usuarios = supabase.table("usuarios").select("id, nome").order("nome").execute().data
        setores = supabase.table("setores").select("id, nome").order("nome").execute().data 
        status = supabase.table("status").select("id, nome").order("nome").execute().data
        
        return ativos, usuarios, setores, status
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return [], [], [], []

# --- Carrega os dados ---
ativos_data, usuarios_data, setores_data, status_data = carregar_dados_auxiliares()

# --- Formatação do nome (Criação do Label) ---
ativos_map = {}
for a in ativos_data:
    nome_modelo = "Modelo Desconhecido"
    nome_marca = "Marca Desconhecida"
    nome_status = "Status Desconhecido"
    
    # 1. Dados de Modelo e Marca
    dados_modelo = a.get("modelo_id")
    if dados_modelo and isinstance(dados_modelo, dict):
        nome_modelo = dados_modelo.get("nome", "S/M")
        dados_marca = dados_modelo.get("marca_id")
        if dados_marca and isinstance(dados_marca, dict):
            nome_marca = dados_marca.get("nome", "S/M")
    
    # 2. Dados de Status (usando o alias que criamos na query)
    dados_status = a.get("status_dados")
    if dados_status and isinstance(dados_status, dict):
        nome_status = dados_status.get("nome", "S/M")

    serial = a["serial"]
    label = f"{nome_marca} {nome_modelo} (SN: {serial}) - {nome_status}"
    
    ativos_map[label] = a

# --- Mapas de "Tradução" (ID <-> Nome) ---
usuarios_map = {u["nome"]: u["id"] for u in usuarios_data}
setores_map = {s["nome"]: s["id"] for s in setores_data}
status_map = {s["nome"]: s["id"] for s in status_data}

usuarios_map_inv = {u["id"]: u["nome"] for u in usuarios_data}
setores_map_inv = {s["id"]: s["nome"] for s in setores_data}
status_map_inv = {s["id"]: s["nome"] for s in status_data}

opcao_manter = "Manter atual"

lista_usuarios = [opcao_manter, "Nenhum (Estoque)"] + list(usuarios_map.keys())
lista_setores = [opcao_manter] + list(setores_map.keys())
lista_status = [opcao_manter] + list(status_map.keys())

# --- Interface Principal ---
st.title("Movimentação de Ativos (Lote)")

tab_movimentar, tab_historico = st.tabs(["Realizar Movimentação", "Histórico"])

# --- ABA 1: Realizar Movimentação ---
with tab_movimentar:
    st.subheader("1. Selecione os Ativos")
    
    chaves_selecionadas = st.multiselect(
        "Buscar por Serial, Marca ou Modelo:",
        options=ativos_map.keys(),
        placeholder="Selecione um ou mais ativos..."
    )
    
    if chaves_selecionadas:
        st.subheader(f"2. Itens Selecionados ({len(chaves_selecionadas)})")
        
        dados_preview = []
        for chave in chaves_selecionadas:
            ativo = ativos_map[chave]
            
            uid = ativo.get("usuario_id")
            lid = ativo.get("local_id")
            sid = ativo.get("status_id")
            
            dados_preview.append({
                "Serial": ativo.get("serial"),
                "Usuário Atual": usuarios_map_inv.get(uid, "Estoque"),
                "Setor Atual": setores_map_inv.get(lid, "-"),
                "Status Atual": status_map_inv.get(sid, "-")
            })
            
        st.dataframe(pd.DataFrame(dados_preview), use_container_width=True, hide_index=True)
        
        st.divider()
        
        st.subheader("3. Definir Destino")
        st.info("Selecione **'Manter atual'** para não alterar o campo específico daquele ativo.")

        with st.form("form_movimentacao"):
            
            col_d1, col_d2, col_d3 = st.columns(3)
            
            with col_d1:
                nome_usuario_destino = st.selectbox("Novo Usuário", options=lista_usuarios, index=0)
            with col_d2:
                nome_local_destino = st.selectbox("Novo Setor", options=lista_setores, index=0)
            with col_d3:
                nome_status_destino = st.selectbox("Novo Status", options=lista_status, index=0)
            
            observacao_input = st.text_area("Observação", placeholder="Ex: Mudança de setor em massa.")
    
            submitted = st.form_submit_button(f"Confirmar Movimentação")
            
            if submitted:
                with st.spinner("Processando..."):
                    sucessos = 0
                    erros = 0
                    
                    for chave in chaves_selecionadas:
                        # Lógica "Manter Atual"
                        ativo_atual = ativos_map[chave]
                        
                        id_user_final = ativo_atual.get("usuario_id") if nome_usuario_destino == opcao_manter else usuarios_map.get(nome_usuario_destino)
                        id_local_final = ativo_atual.get("local_id") if nome_local_destino == opcao_manter else setores_map[nome_local_destino]
                        id_status_final = ativo_atual.get("status_id") if nome_status_destino == opcao_manter else status_map[nome_status_destino]

                        try:
                            # Executa Update e Log com os IDs calculados
                            supabase.table("movimentacoes").insert({
                                "ativo_id": ativo_atual['id'],
                                "usuario_id": id_user_final,
                                "setor_id": id_local_final,
                                "status_id": id_status_final,
                                "observacao": observacao_input
                            }).execute()
                            
                            supabase.table("ativos").update({
                                "usuario_id": id_user_final,
                                "local_id": id_local_final,
                                "status_id": id_status_final
                            }).eq("id", ativo_atual['id']).execute()
                            
                            sucessos += 1
                            
                        except Exception as e:
                            erros += 1
                            st.error(f"Erro no ativo {ativo_atual['serial']}: {e}")
                    
                    if sucessos > 0:
                        st.success(f"{sucessos} movimentações realizadas!")
                        if erros == 0:
                            st.cache_data.clear()
                            st.rerun()

# --- ABA 2: Histórico---
with tab_historico:
    st.subheader("Histórico Completo")
    serial_filtro_hist = st.selectbox(
        "Filtrar histórico por Ativo",
        options=["Todos os Ativos"] + list(ativos_map.keys()),
        index=0
    )
    
    with st.spinner("Carregando histórico..."):
        try:
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
            
            historico_data = query_builder.limit(100).execute().data
            
            if historico_data:
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
                st.dataframe(pd.DataFrame(df_list), use_container_width=True, hide_index=True)
            else:
                st.info("Sem histórico.")
        except Exception as e:
            st.error(f"Erro: {e}")
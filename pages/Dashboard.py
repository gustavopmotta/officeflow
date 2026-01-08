import streamlit as st
import pandas as pd
import plotly.express as px
from utils import verificar_autenticacao
from st_pages import get_nav_from_toml, add_page_title

# --- Conexão com supabase ---
supabase = verificar_autenticacao()

# --- Funções de Carregamento (Cache Otimizado) ---
@st.cache_data(ttl=300) # Cache de 5 minutos para performance
def carregar_dados_dashboard():
    try:
        # 1. Busca Ativos (Com status e setores para gráficos)
        query_ativos = "id, serial, valor, status(nome), setores(nome), modelos(nome, marcas(nome))"
        response_ativos = supabase.table("ativos").select(query_ativos).execute()
        df_ativos = pd.DataFrame(response_ativos.data)

        # 2. Busca Movimentações Recentes (Últimas 10)
        query_mov = "created_at, ativos(serial), usuarios(nome), setores(nome), status(nome)"
        response_mov = supabase.table("movimentacoes").select(query_mov).order("created_at", desc=True).limit(10).execute()
        df_movimentacoes = pd.DataFrame(response_mov.data)

        # 3. Busca Manutenções em Aberto (retornado_em is null)
        query_manut = "id, criado_em, fornecedor, defeito, ativos(serial, modelos(nome))"
        response_manut = supabase.table("manutencoes").select(query_manut).is_("retornado_em", "null").execute()
        df_manutencao = pd.DataFrame(response_manut.data)

        return df_ativos, df_movimentacoes, df_manutencao

    except Exception as e:
        st.error(f"Erro ao carregar dados do dashboard: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# --- Processamento e Carga de Dados ---
with st.spinner("Atualizando indicadores..."):
    df_ativos, df_mov, df_manut = carregar_dados_dashboard()

# --- Tratamento de Dados (Flattening) ---
if not df_ativos.empty:
    # Extrai nomes dos objetos aninhados de forma segura
    df_ativos["status_nome"] = df_ativos["status"].apply(lambda x: x.get("nome") if x else "N/A")
    df_ativos["setor_nome"] = df_ativos["setores"].apply(lambda x: x.get("nome") if x else "Sem Setor")
    df_ativos["valor"] = df_ativos["valor"].fillna(0)
else:
    # Cria estrutura vazia para evitar erros nos gráficos
    df_ativos = pd.DataFrame(columns=["status_nome", "setor_nome", "valor"])

# --- Interface Gráfica Principal ---
st.title("Visão Geral do Patrimônio")
st.markdown("Monitoramento de ativos, movimentações e alertas de manutenção.")
st.divider()

# --- Seção 1: Indicadores Chave (KPIs) ---
with st.expander("Dados Gerais", expanded=True):
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

total_ativos = len(df_ativos)
valor_total_investido = df_ativos["valor"].sum()
qtd_manutencao_aberta = len(df_manut)

# Lógica para contar estoque (busca textual por "Estoque" independente de maiúscula/minúscula)
qtd_em_estoque = len(df_ativos[df_ativos["status_nome"].str.contains("Estoque", case=False, na=False)])

with col_kpi1:
    st.metric(
        label="Total de Ativos",
        value=total_ativos,
        help="Quantidade total de itens cadastrados na base."
    )

with col_kpi2:
    st.metric(
        label="Valor Patrimonial",
        value=f"R$ {valor_total_investido:,.2f}",
        help="Soma do valor de compra de todos os ativos."
    )

with col_kpi3:
    st.metric(
        label="Itens Disponíveis",
        value=qtd_em_estoque,
        help="Ativos com status 'Em Estoque' prontos para uso."
    )

with col_kpi4:
    st.metric(
        label="Em Manutenção",
        value=qtd_manutencao_aberta,
        help="Chamados de manutenção que ainda não foram fechados."
    )

# --- Seção 2: Gráficos Gerenciais ---
if not df_ativos.empty:
    col_graf1, col_graf2 = st.columns(2)

    # Gráfico de Rosca: Status
    with col_graf1:
        with st.expander("Distribuição por Status", expanded=True, width="stretch"):
            status_counts = df_ativos["status_nome"].value_counts().reset_index()
            status_counts.columns = ["Status", "Quantidade"]

            fig_status = px.pie(
                status_counts, 
                values="Quantidade", 
                names="Status", 
                color_discrete_sequence=px.colors.qualitative.Set1
            )
            st.plotly_chart(fig_status, width="stretch")

    # Gráfico de Barras: Setores (Top 10)
    with col_graf2:
        with st.expander("Alocação por Setor", expanded=True, width="stretch"):
            setor_counts = df_ativos["setor_nome"].value_counts().reset_index().head(10)
            setor_counts.columns = ["Setor", "Quantidade"]

            fig_setor = px.pie(
                setor_counts, 
                values="Quantidade", 
                names="Setor", 
                color_discrete_sequence=px.colors.qualitative.D3
            )
            st.plotly_chart(fig_setor, width="stretch")

else:
    st.info("Cadastre ativos para visualizar os gráficos de distribuição.")

st.divider()

# --- Seção 3: Tabelas Operacionais ---
col_tab_mov, col_tab_manut = st.columns([3, 2])

# Tabela de Movimentações Recentes
with col_tab_mov:
    st.subheader("Últimas Movimentações")
    if not df_mov.empty:
        lista_display_mov = []
        for _, row in df_mov.iterrows():
            lista_display_mov.append({
                "Data": pd.to_datetime(row["created_at"]).strftime("%d/%m %H:%M"),
                "Ativo": row["ativos"]["serial"] if row["ativos"] else "?",
                "Usuário": row["usuarios"]["nome"] if row.get("usuarios") else "Estoque",
                "Destino": row["setores"]["nome"] if row.get("setores") else "-",
                "Status": row["status"]["nome"] if row.get("status") else "-"
            })
        st.dataframe(pd.DataFrame(lista_display_mov), width="stretch", hide_index=True)
    else:
        st.info("Nenhuma movimentação registrada recentemente.")

# Tabela de Alertas de Manutenção
with col_tab_manut:
    st.subheader("Alertas de Manutenção")
    if not df_manut.empty:
        lista_display_manut = []
        for _, row in df_manut.iterrows():
            mod = row["ativos"].get("modelos") if row.get("ativos") else {}
            nome_modelo = mod.get("nome", "S/M")
            
            lista_display_manut.append({
                "Aberto em": pd.to_datetime(row["criado_em"]).strftime("%d/%m"),
                "Modelo": nome_modelo,
                "Fornecedor": row["fornecedor"]
            })
        st.dataframe(pd.DataFrame(lista_display_manut), width="stretch", hide_index=True)
    else:
        st.success("Nenhuma manutenção pendente no momento.")

# --- Botão de Atualização Manual ---
if st.button("Atualizar Dados Agora"):
    st.cache_data.clear()
    st.rerun()
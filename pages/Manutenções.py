import streamlit as st
import pandas as pd
from datetime import datetime
from utils import verificar_autenticacao

# --- Conexão com Supabase ---
supabase = verificar_autenticacao()

# --- Criação de Dados ---
def carregar_dados():
    ativos_raw = supabase.table("ativos").select("*, modelos(nome, marcas(nome)), status(nome)").execute().data
    status_raw = supabase.table("status").select("id, nome").execute().data
    
    return ativos_raw, status_raw

def carregar_manutencoes_abertas():
    return supabase.table("manutencoes").select(
        "*, ativos(serial, modelos(nome, marcas(nome)))"
    ).is_("retornado_em", "null").execute().data

def carregar_historico_completo():
    return supabase.table("manutencoes").select(
        "*, ativos(serial, modelos(nome, marcas(nome)))"
    ).order("criado_em", desc=True).execute().data

ativos_data, status_data = carregar_dados()

status_map_inv = {s['nome']: s['id'] for s in status_data}
id_em_manutencao = status_map_inv.get("Em Manutenção")
id_em_estoque = status_map_inv.get("Em Estoque")

ativos_map = {}
for a in ativos_data:
    mod = a.get('modelos') or {}
    marc = mod.get('marcas') or {}
    label = f"{marc.get('nome','S/M')} - {mod.get('nome','S/M')} - {a['serial']}"
    ativos_map[label] = a

# --- Estrutura da Página ---
st.title("Controle de Manutenções")

tab_novo, tab_fechar, tab_hist = st.tabs(["Abrir Chamado", "Concluir Manutenção", "Histórico de Manutenções"])

# --- ABA 0.1: Criar OS ---
with tab_novo:
    st.subheader("Registrar Saída para Manutenção")
    
    with st.form("form_abrir_manutencao"):
        col1, col2 = st.columns(2)
        
        # Seleção do Ativo
        ativo_label = col1.selectbox("Selecione o Ativo", options=ativos_map.keys())
        
        # Campos da Tabela
        fornecedor = col2.text_input("Fornecedor / Assistência Técnica")
        defeito = st.text_area("Descrição do Defeito")
        data_envio = st.date_input("Data de Envio", value=datetime.today())
        
        # Checkbox para automação
        atualizar_status = st.checkbox("Mudar status do ativo para 'Em Manutenção' automaticamente?", value=True)
        
        submit_abrir = st.form_submit_button("Abrir Chamado")
        
        if submit_abrir:
            if not fornecedor or not defeito:
                st.warning("Preencha o fornecedor e o defeito.")
            else:
                ativo_selecionado = ativos_map[ativo_label]
                
                try:
                    # 1. Insere na tabela 'manutencoes'
                    dados_insert = {
                        "ativo_id": ativo_selecionado['id'],
                        "fornecedor": fornecedor,
                        "defeito": defeito,
                        "criado_em": data_envio.isoformat(),
                        "retornado_em": None, # Fica em aberto
                        "valor": None
                    }
                    supabase.table("manutencoes").insert(dados_insert).execute()
                    
                    # 2. Atualiza status do ativo (Opcional)
                    if atualizar_status and id_em_manutencao:
                        supabase.table("ativos").update(
                            {"status_id": id_em_manutencao}
                        ).eq("id", ativo_selecionado['id']).execute()
                        msg_extra = "e status do ativo atualizado"
                    else:
                        msg_extra = ""

                    st.success(f"Chamado aberto com sucesso {msg_extra}!")
                    st.cache_data.clear()
                    
                except Exception as e:
                    st.error(f"Erro ao registrar: {e}")

# --- ABA 02: Fechar OS
with tab_fechar:
    st.subheader("Finalizar Chamado e Registrar Custos")
    
    manutencoes_abertas = carregar_manutencoes_abertas()
    
    if not manutencoes_abertas:
        st.info("Não há manutenções em aberto no momento.")
    else:
        mapa_chamados = {}
        for m in manutencoes_abertas:
            a = m.get('ativos') or {}
            mod = a.get('modelos') or {}
            label_chamado = f"Chamado #{m['id']} | {a.get('serial')} ({m.get('fornecedor')})"
            mapa_chamados[label_chamado] = m
            
        selecao_chamado = st.selectbox("Selecione o Chamado em Aberto", options=mapa_chamados.keys())
        
        if selecao_chamado:
            chamado_atual = mapa_chamados[selecao_chamado]
            
            st.write(f"**Defeito Reportado:** {chamado_atual['defeito']}")
            st.write(f"**Data de Abertura:** {pd.to_datetime(chamado_atual['criado_em']).strftime('%d/%m/%Y')}")
            
            st.divider()
            
            with st.form("form_fechar_manutencao"):
                c1, c2 = st.columns(2)
                valor_servico = c1.number_input("Valor do Serviço (R$)", min_value=0.0, step=0.01, format="%.2f")
                data_retorno = c2.date_input("Data de Retorno", value=datetime.today())
                
                voltar_estoque = st.checkbox("Retornar ativo para 'Em Estoque'?", value=True)
                
                submit_fechar = st.form_submit_button("Finalizar Chamado")
                
                if submit_fechar:
                    try:
                        supabase.table("manutencoes").update({
                            "valor": valor_servico,
                            "retornado_em": data_retorno.isoformat()
                        }).eq("id", chamado_atual['id']).execute()

                        if voltar_estoque and id_em_estoque:
                            supabase.table("ativos").update({
                                "status_id": id_em_estoque
                            }).eq("id", chamado_atual['ativo_id']).execute()
                            
                        st.success("Manutenção finalizada e custos registrados!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erro ao finalizar: {e}")

# --- ABA 03: Histórico de Movimentações
with tab_hist:
    st.subheader("Histórico de Manutenções")
    
    # Filtro por Ativo
    filtro_ativo = st.selectbox("Filtrar por Ativo", options=["Todos"] + list(ativos_map.keys()))
    
    # Carrega dados
    hist_data = carregar_historico_completo()
    
    df_lista = []
    for h in hist_data:
        a = h.get('ativos') or {}
        mod = a.get('modelos') or {}
        marc = mod.get('marcas') or {}

        label_ativo = f"{marc.get('nome','S/M')} - {mod.get('nome','S/M')} - {a['serial']}"
        
        if filtro_ativo == "Todos" or filtro_ativo == label_ativo:
            df_lista.append({
                "ID Chamado": h['id'],
                "Data Envio": pd.to_datetime(h['criado_em']).strftime('%d/%m/%Y'),
                "Data Retorno": pd.to_datetime(h['retornado_em']).strftime('%d/%m/%Y') if h['retornado_em'] else "Em Aberto",
                "Ativo": label_ativo,
                "Fornecedor": h['fornecedor'],
                "Defeito": h['defeito'],
                "Custo (R$)": h['valor']
            })
            
    if df_lista:
        df_final = pd.DataFrame(df_lista)
        st.dataframe(
            df_final, 
            width="stretch", 
            hide_index=True,
            column_config={
                "Custo (R$)": st.column_config.NumberColumn(format="R$ %.2f")
            }
        )
        
        total_custo = df_final["Custo (R$)"].sum()
        st.metric("Custo Total Filtrado", f"R$ {total_custo:,.2f}")
    else:
        st.warning("Nenhum registro encontrado.")
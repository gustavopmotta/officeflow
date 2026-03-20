from utils import verificar_autenticacao
import streamlit as st
import pandas as pd
import datetime
import re

# --- Configuração ---
supabase = verificar_autenticacao()

st.title("Estoque de Acessórios")
st.markdown("Gerencie o saldo de capas e películas por modelo de aparelho.")

if 'carrinho_acessorios' not in st.session_state:
    st.session_state.carrinho_acessorios = []

def formatar_nf_padrao(valor_nf):
    if not valor_nf:
        return ""
    apenas_numeros = re.sub(r'\D', '', str(valor_nf))
    apenas_numeros = apenas_numeros.zfill(9)
    return f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:]}"

# --- Funções do Banco de Dados ---
def carregar_dados_auxiliares():
    try:
        lojas = supabase.table("lojas").select("id, nome").order("nome").execute().data
        colaboradores = supabase.table("colaboradores").select("id, nome").order("nome").execute().data
        
        # Puxa modelos únicos que já estão no estoque de acessórios
        estoque_atual = supabase.table("capas_peliculas").select("modelo").execute().data
        modelos_estoque = [item['modelo'] for item in estoque_atual] if estoque_atual else []
        
        return lojas, colaboradores, modelos_estoque
    except Exception as e:
        st.error(f"Erro ao carregar opções: {e}")
        return [], [], []

def buscar_estoque():
    try:
        response = supabase.table("capas_peliculas").select("*").order("modelo").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao buscar estoque: {e}")
        return []

def atualizar_saldo(modelo, add_capas, add_peliculas, operacao="entrada"):
    try:
        registro_atual = supabase.table("capas_peliculas").select("*").eq("modelo", modelo).execute().data
        
        if registro_atual:
            saldo_capas = registro_atual[0].get("qnt_capas", 0)
            saldo_pelic = registro_atual[0].get("qnt_peliculas", 0)
            
            if operacao == "entrada":
                novo_capas = saldo_capas + add_capas
                novo_pelic = saldo_pelic + add_peliculas
            else:
                novo_capas = saldo_capas - add_capas
                novo_pelic = saldo_pelic - add_peliculas
                
                if novo_capas < 0 or novo_pelic < 0:
                    return False, "A quantidade de saída é maior que o saldo em estoque!"

            # Atualiza no banco
            supabase.table("capas_peliculas").update({
                "qnt_capas": novo_capas,
                "qnt_peliculas": novo_pelic
            }).eq("modelo", modelo).execute()
            
            return True, "Estoque atualizado com sucesso!"
            
        else:
            # Se não existe e for entrada, cria um novo registro
            if operacao == "entrada":
                supabase.table("capas_peliculas").insert({
                    "modelo": modelo.upper(),
                    "qnt_capas": add_capas,
                    "qnt_peliculas": add_peliculas
                }).execute()
                return True, "Novo modelo cadastrado com sucesso!"
            else:
                return False, "Modelo não encontrado para dar saída."
                
    except Exception as e:
        return False, f"Erro no banco de dados: {e}"

# --- Interface (Abas) ---
aba_estoque, aba_entrada, aba_saida = st.tabs(["Visão Geral", "Entradas (Compras)", "Saídas (Uso)"])

dados_estoque = buscar_estoque()
modelos_existentes = [item['modelo'] for item in dados_estoque] if dados_estoque else []

with aba_estoque:
    st.subheader("Posição Atual do Estoque")
    
    if dados_estoque:
        df_estoque = pd.DataFrame(dados_estoque)
        
        # Métricas no topo
        col1, col2 = st.columns(2)
        total_capas = df_estoque['qnt_capas'].sum()
        total_peliculas = df_estoque['qnt_peliculas'].sum()
        
        col1.metric("Total de Capas", int(total_capas))
        col2.metric("Total de Películas", int(total_peliculas))
        
        st.divider()
        
        # Tabela formatada
        st.dataframe(
            df_estoque,
            width="content",
            hide_index=True,
            column_config={
                "id": None,
                "modelo": st.column_config.TextColumn("Modelo do Aparelho"),
                "qnt_capas": st.column_config.NumberColumn("Qtd. Capas", format="%d"),
                "qnt_peliculas": st.column_config.NumberColumn("Qtd. Películas", format="%d")
            }
        )
    else:
        st.info("Nenhum acessório cadastrado no estoque ainda.")

with aba_entrada:
    lojas_data, colaboradores_data, modelos_existentes = carregar_dados_auxiliares()
    
    lojas_map = {f['nome']: f['id'] for f in lojas_data}
    colaboradores_map = {c['nome']: c['id'] for c in colaboradores_data}

    if not lojas_map or not colaboradores_map:
        st.warning("É necessário cadastrar lojas e colaboradores no sistema antes de registrar compras.")
    else:
        # --- ETAPA 1: CABEÇALHO DA NOTA FISCAL ---
        st.subheader("1. Dados da Nota Fiscal")
        with st.container(border=True):
            col_nf, col_data, col_loja, col_comp = st.columns(4)
            
            with col_nf:
                nf_input = st.text_input("Nota Fiscal (Apenas Números)", key="acess_nf")
            with col_data:
                data_compra = st.date_input("Data da Compra", datetime.date.today(), key="acess_data")
            with col_loja:
                loja_selecionada = st.selectbox("Loja / Fornecedor", options=lojas_map.keys(), index=None)
            with col_comp:
                comprador_selecionado = st.selectbox("Comprador / Responsável", options=colaboradores_map.keys(), index=None)
            
            col_pdf, col_valor = st.columns([3, 1])
            with col_pdf:
                uploaded_pdf = st.file_uploader("Anexar PDF da Nota Fiscal (Opcional)", type="pdf", key="acess_pdf")
            with col_valor:
                valor_total_nota = st.number_input("Valor Total da NF (R$)", min_value=0.0, format="%.2f", key="acess_valor")

        # --- ETAPA 2: ADICIONAR ITENS (CARRINHO) ---
        st.subheader("2. Adicionar Itens (Lotes)")
        st.markdown("Selecione os modelos e as quantidades para adicionar à lista desta compra.")
        
        with st.container(border=True):
            col_tipo, col_mod, col_c, col_p = st.columns([1.5, 2.5, 1, 1])
            
            with col_tipo:
                tipo_modelo = st.radio("O modelo já existe no estoque?", ["Sim", "Não"], horizontal=True, key="radio_tipo")
                
            with col_mod:
                if tipo_modelo == "Sim":
                    modelo_input = st.selectbox("Selecione o Modelo", options=modelos_existentes) if modelos_existentes else ""
                    if not modelos_existentes:
                        st.caption("Nenhum modelo no estoque. Use a opção 'Não, é novo'.")
                else:
                    modelo_input = st.text_input("Digite o Novo Modelo").strip().upper()
                    
            with col_c:
                qtd_capas = st.number_input("Qtd. Capas", min_value=0, step=1, key="num_capas")
            with col_p:
                qtd_pelic = st.number_input("Qtd. Películas", min_value=0, step=1, key="num_pelic")
                
            if st.button("Adicionar Lote à Lista", width="stretch"):
                if not modelo_input:
                    st.warning("Informe o modelo do aparelho.")
                elif qtd_capas == 0 and qtd_pelic == 0:
                    st.warning("Informe a quantidade de capas ou películas.")
                else:
                    st.session_state.carrinho_acessorios.append({
                        "Modelo": modelo_input,
                        "Capas": qtd_capas,
                        "Películas": qtd_pelic
                    })
                    st.rerun()

        # --- ETAPA 3: FINALIZAR COMPRA ---
        if st.session_state.carrinho_acessorios:
            st.subheader("3. Lista de Itens a Registrar")
            
            df_carrinho = pd.DataFrame(st.session_state.carrinho_acessorios)
            st.dataframe(df_carrinho, width="stretch", hide_index=True)
            
            col_btn_limpar, col_espaco, col_btn_salvar = st.columns([1, 2, 2])
            
            with col_btn_limpar:
                if st.button("Limpar Lista"):
                    st.session_state.carrinho_acessorios = []
                    st.rerun()
                    
            with col_btn_salvar:
                if st.button("Salvar Compra e Atualizar Estoque", width="stretch"):
                    
                    # Validações Finais
                    if not nf_input:
                        st.error("A Nota Fiscal é obrigatória.")
                    elif not loja_selecionada:
                        st.error("Selecione a Loja.")
                    elif not comprador_selecionado:
                        st.error("Selecione o Comprador.")
                    else:
                        with st.spinner("Processando e salvando..."):
                            try:
                                nf_formatada = formatar_nf_padrao(nf_input)
                                    
                                # 1. Upload do PDF (se houver)
                                path_para_salvar = None
                                if uploaded_pdf:
                                    pdf_bytes = uploaded_pdf.getvalue()
                                    file_path_in_storage = f"public/acessnf-{nf_formatada}.pdf"
                                    supabase.storage.from_("NFs").upload(
                                        file_path_in_storage, pdf_bytes,
                                        {"content-type": "application/pdf", "upsert": "true"}
                                    )
                                    path_para_salvar = file_path_in_storage

                                # 2. Registrar a Compra na tabela de compras
                                nova_compra = {
                                    "data_compra": data_compra.isoformat(),
                                    "nota_fiscal": nf_formatada,
                                    "loja_id": lojas_map[loja_selecionada],
                                    "comprador_id": colaboradores_map[comprador_selecionado],
                                    "valor_total": valor_total_nota if valor_total_nota > 0 else None,
                                    "nf_url": path_para_salvar,
                                }
                                
                                supabase.table("compras").insert(nova_compra).execute()
                                
                                # 3. Atualizar o Estoque (Tabela capas_peliculas)
                                # Agrupa caso o usuário tenha colocado o mesmo modelo 2x no carrinho
                                df_agrupado = df_carrinho.groupby("Modelo").sum().reset_index()
                                
                                for _, linha in df_agrupado.iterrows():
                                    mod = linha["Modelo"]
                                    add_c = linha["Capas"]
                                    add_p = linha["Películas"]
                                    
                                    # Verifica se já existe
                                    reg = supabase.table("capas_peliculas").select("*").eq("modelo", mod).execute().data
                                    
                                    if reg:
                                        nova_q_c = reg[0].get("qnt_capas", 0) + add_c
                                        nova_q_p = reg[0].get("qnt_peliculas", 0) + add_p
                                        supabase.table("capas_peliculas").update({
                                            "qnt_capas": nova_q_c,
                                            "qnt_peliculas": nova_q_p
                                        }).eq("modelo", mod).execute()
                                    else:
                                        supabase.table("capas_peliculas").insert({
                                            "modelo": mod,
                                            "qnt_capas": add_c,
                                            "qnt_peliculas": add_p
                                        }).execute()

                                # Sucesso e Limpeza
                                st.session_state.carrinho_acessorios = []
                                st.success(f"Compra NF {nf_formatada} registrada e estoque atualizado!")
                                st.rerun()

                            except Exception as e:
                                st.error(f"Ocorreu um erro: {e}")

with aba_saida:
    st.subheader("Registrar Saída de Estoque")
    st.markdown("Dê baixa nos itens entregues a colaboradores ou descartados.")
    
    dados_estoque_atual = buscar_estoque()
    
    if not dados_estoque_atual:
        st.info("O estoque está vazio. Não é possível realizar saídas.")
    else:
        with st.container(border=True):
            # Cria lista apenas dos modelos que tem alguma coisa no estoque (> 0)
            modelos_com_saldo = [item for item in dados_estoque_atual if item['qnt_capas'] > 0 or item['qnt_peliculas'] > 0]
            opcoes_modelos = [item['modelo'] for item in modelos_com_saldo]
            
            if not opcoes_modelos:
                st.warning("Todos os modelos estão com saldo zerado no momento.")
            else:
                modelo_saida = st.selectbox("Selecione o Modelo", options=opcoes_modelos, key="saida_modelo")
                
                # Encontra os limites (saldo atual) do modelo selecionado
                item_selecionado = next(item for item in modelos_com_saldo if item['modelo'] == modelo_saida)
                max_capas = int(item_selecionado['qnt_capas'])
                max_pelic = int(item_selecionado['qnt_peliculas'])
                
                st.caption(f"**Saldo Disponível:** {max_capas} capas | {max_pelic} películas")
                
                with st.form("form_saida_acessorios"):
                    col_c_out, col_p_out = st.columns(2)
                    with col_c_out:
                        qtd_out_capas = st.number_input("Capas a retirar", min_value=0, max_value=max_capas, step=1)
                    with col_p_out:
                        qtd_out_pelic = st.number_input("Películas a retirar", min_value=0, max_value=max_pelic, step=1)
                        
                    submit_saida = st.form_submit_button("Confirmar Saída", width="stretch")
                    
                    if submit_saida:
                        if qtd_out_capas == 0 and qtd_out_pelic == 0:
                            st.warning("Informe pelo menos 1 item para retirar.")
                        else:
                            with st.spinner("Atualizando banco de dados..."):
                                try:
                                    nova_qtd_c = max_capas - qtd_out_capas
                                    nova_qtd_p = max_pelic - qtd_out_pelic
                                    
                                    supabase.table("capas_peliculas").update({
                                        "qnt_capas": nova_qtd_c,
                                        "qnt_peliculas": nova_qtd_p
                                    }).eq("modelo", modelo_saida).execute()
                                    
                                    st.success(f"Saída de {modelo_saida} registrada com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao registrar saída: {e}")
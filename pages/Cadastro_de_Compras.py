from utils import verificar_autenticacao
import streamlit as st
import pandas as pd
import random
import datetime
import re  # Importação adicionada para tratar a formatação da NF

# --- Conexão com Supabase ---
supabase = verificar_autenticacao()

# --- Funções Auxiliares ---

def formatar_nf_padrao(valor_nf):
    """
    Recebe qualquer string, remove não-números, garante 9 dígitos
    e retorna no formato 000.000.000.
    """
    if not valor_nf:
        return ""
    # Remove tudo que não é dígito
    apenas_numeros = re.sub(r'\D', '', str(valor_nf))
    # Garante 9 dígitos com zeros a esquerda (ex: 540 -> 000000540)
    apenas_numeros = apenas_numeros.zfill(9)
    # Fatia e formata
    return f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:]}"

def carregar_opcoes():
    """Busca dados das tabelas auxiliares para preencher os selectbox."""
    modelos = supabase.table("modelos").select("id, nome, categoria_id, marcas(nome)").order("nome").execute().data
    categorias = supabase.table("categorias").select("id, nome").order("nome").execute().data
    setores = supabase.table("setores").select("id, nome").order("nome").execute().data
    status = supabase.table("status").select("id, nome").order("nome").execute().data
    estados = supabase.table("estados").select("id, nome").order("nome").execute().data
    lojas = supabase.table("lojas").select("id, nome").order("nome").execute().data 
    # NOVA TABELA: Colaboradores
    colaboradores = supabase.table("colaboradores").select("id, nome").order("nome").execute().data

    return modelos, categorias, setores, status, estados, lojas, colaboradores

def carregar_historico_compras():
    try:
        # ALTERAÇÃO: Adicionado join com colaboradores(nome)
        response = supabase.table("compras").select("*, lojas(nome), modelos(nome), colaboradores(nome)").order("data_compra", desc=True).limit(50).execute()
        dados = response.data
        
        lista_processada = []
        
        if dados:
            for compra in dados:
                caminho_arquivo = compra.get("nf_url")
                url_pdf = None

                if caminho_arquivo:
                    try:
                        res_storage = supabase.storage.from_("NFs").create_signed_url(
                            caminho_arquivo, 3600
                        )
                        
                        if isinstance(res_storage, dict):
                            url_pdf = res_storage.get('signedURL')
                        else:
                            url_pdf = res_storage 
                    except Exception as e:
                        print(f"Erro ao gerar URL: {e}")

                # Dados da Loja, Modelo e Comprador (joins seguros)
                nome_loja = compra.get('lojas', {}).get('nome', 'N/A') if compra.get('lojas') else "N/A"
                nome_modelo = compra.get('modelos', {}).get('nome', '-') if compra.get('modelos') else "-"
                # ALTERAÇÃO: Pegando nome do comprador
                nome_comprador = compra.get('colaboradores', {}).get('nome', '-') if compra.get('colaboradores') else "-"

                lista_processada.append({
                    "ID": compra["id"],
                    "Data": pd.to_datetime(compra["data_compra"]).strftime('%d/%m/%Y'),
                    "NF": compra["nota_fiscal"], # Já virá formatado do banco se salvo corretamente
                    "Modelo": nome_modelo,
                    "Loja": nome_loja,
                    "Comprador": nome_comprador, # Nova Coluna
                    "Valor Total": compra["valor_total"],
                    "Comprovante": url_pdf
                })
                
        return lista_processada

    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
        return []

# --- Página Principal ---
st.title("Gestão de Compras")

# --- Criação das Abas ---
tab_cadastro, tab_historico = st.tabs(["Registrar Nova Compra", "Histórico e Notas Fiscais"])

# --- ABA 1: Cadastro ---
with tab_cadastro:
    try:
        # ALTERAÇÃO: Recebendo colaboradores
        modelos_data, categorias_data, setores_data, status_data, estados_data, lojas_data, colaboradores_data = carregar_opcoes()

        # --- Mapeamentos ---
        categorias_map = {c['nome']: c['id'] for c in categorias_data}
        setores_map = {s['nome']: s['id'] for s in setores_data}
        status_map = {s['nome']: s['id'] for s in status_data}
        estados_map = {e['nome']: e['id'] for e in estados_data}
        lojas_map = {f['nome']: f['id'] for f in lojas_data}
        # NOVO MAPEAMENTO
        colaboradores_map = {c['nome']: c['id'] for c in colaboradores_data}

        if not categorias_map or not setores_map or not status_map or not estados_map:
            st.error("Dados auxiliares incompletos. Verifique o 'Cadastro Geral'.")
        else:
            # --- ETAPA 1: INFORMAÇÕES DO LOTE ---     
            st.subheader("1. Itens da Compra")
            st.info("Primeiro, defina a Categoria, Modelo, Valor e Quantidade do lote.")
            
            col_categoria, col_modelo, col_valor, col_quant = st.columns(4)
            
            with col_categoria:
                categoria_selecionada = st.selectbox(
                    "Categoria", 
                    options=categorias_map.keys(), 
                    key="compra_categoria"
                )
            
            # Lógica de filtragem e formatação dos modelos
            modelos_map = {}
            if categoria_selecionada:
                categoria_id_selecionada = categorias_map[categoria_selecionada]
                modelos_filtrados = [m for m in modelos_data if m.get('categoria_id') == categoria_id_selecionada]
                
                for m in modelos_filtrados:
                    marca_nome = m.get('marcas', {}).get('nome', 'Sem Marca')
                    display_name = f"{marca_nome} - {m['nome']}"
                    modelos_map[display_name] = m['id']
            
            with col_modelo:
                st.selectbox("Modelo Comprado", options=modelos_map.keys(), key="compra_modelo")
            with col_valor:
                st.number_input("Valor Unitário (R$)", min_value=0.01, format="%.2f", key="compra_valor")
            with col_quant:
                st.number_input("Quantidade Comprada", min_value=1, step=1, value=1, key="compra_qtd")
            
            st.divider()

            # --- BOTÃO GERADOR DE SERIAL ---
            def gerar_seriais_callback():
                try:
                    modelo_display_name = st.session_state.compra_modelo
                    qtd = st.session_state.compra_qtd
                    
                    if not modelo_display_name:
                        st.warning("Por favor, selecione um modelo primeiro.")
                        return

                    modelo_id = modelos_map[modelo_display_name]
                    modelo_obj = next(m for m in modelos_data if m['id'] == modelo_id)
                    
                    marca_nome = "S-MARCA"
                    if modelo_obj.get('marcas') and isinstance(modelo_obj['marcas'], dict):
                        marca_nome = modelo_obj['marcas'].get('nome', 'S-MARCA').split(' ')[0].upper()
                    
                    modelo_prefixo = modelo_obj['nome'].split(' ')[0].upper()
                    
                    for i in range(qtd):
                        sufixo_aleatorio = random.randint(10000, 99999)
                        novo_serial = f"{marca_nome}-{modelo_prefixo}-{sufixo_aleatorio}"
                        st.session_state[f"serial_{i}"] = novo_serial
                    
                except Exception as e:
                    st.error(f"Erro ao gerar seriais: {e}")

            st.button(
                "Gerar Seriais",
                on_click=gerar_seriais_callback,
                help="Preenche os campos de serial abaixo."
            )

            # --- ETAPA 2: FORMULÁRIO PRINCIPAL ---
            with st.form("form_compra_ativos"):
                
                # --- 2A. Informações da Compra ---
                st.subheader("2. Informações da Nota Fiscal")
                # ALTERAÇÃO: Layout de colunas ajustado para incluir o Comprador
                col_nf, col_data, col_loja, col_comprador, col_valor_nf = st.columns(5)
                
                with col_nf:
                    st.text_input("Nota Fiscal", key="compra_nf", help="Será formatado como 000.000.000")
                with col_data:
                    data_compra = st.date_input("Data da Compra", datetime.date.today(), key="compra_data")
                with col_loja:
                    loja = st.selectbox(
                        "Loja",
                        options=lojas_map.keys(),
                        index=None,
                        placeholder="Selecione...",
                        key="compra_loja"
                    )
                with col_comprador:
                    # NOVA COLUNA: Comprador
                    comprador = st.selectbox(
                        "Comprador",
                        options=colaboradores_map.keys(),
                        index=None,
                        placeholder="Responsável...",
                        key="compra_comprador"
                    )
                with col_valor_nf:
                    valor_total_nota = st.number_input("Valor Total NF (R$)", min_value=0.0, format="%.2f", key="compra_valor_total")

                # --- UPLOAD DE PDF ---
                uploaded_pdf = st.file_uploader(
                    "Anexar PDF da Nota Fiscal",
                    type="pdf",
                    key="compra_pdf"
                )
                st.divider()

                # --- 2B. Inputs dos Seriais ---
                st.subheader(f"3. Números de Série ({st.session_state.compra_qtd} itens)")
                seriais_input = []
                cols = st.columns(3)
                for i in range(st.session_state.compra_qtd):
                    with cols[i % 3]:
                        serial = st.text_input(f"Serial {i+1}", key=f"serial_{i}")
                        seriais_input.append(serial)
                
                # --- 2C. Status Padrão ---
                st.subheader("4. Status Padrão (para este lote)")
                col_status, col_estado, col_setor = st.columns(3)
                with col_status:
                    status_selecionado = st.selectbox("Status", options=status_map.keys())
                with col_estado:
                    estado_selecionado = st.selectbox("Estado", options=estados_map.keys())
                with col_setor:
                    setor_selecionado = st.selectbox("Setor (Local)", options=setores_map.keys())

                st.divider()
                
                # --- Botão de Envio ---
                submitted = st.form_submit_button("Cadastrar Compra e Todos os Ativos")

            # --- ETAPA 3: LÓGICA DE SUBMISSÃO ---
            if submitted:
                nf_raw = st.session_state.compra_nf # Pega o valor digitado

                # --- Validações ---
                if not nf_raw:
                    st.error("Erro: O campo 'Nota Fiscal' é obrigatório.")
                elif 'compra_modelo' not in st.session_state or not st.session_state.compra_modelo:
                     st.error("Erro: Nenhum modelo foi selecionado.")
                elif not loja:
                     st.error("Erro: O campo 'Loja' é obrigatório.")
                elif not comprador:
                     st.error("Erro: O campo 'Comprador' é obrigatório.")
                elif any(s.strip() == "" for s in seriais_input):
                    st.error("Erro: Todos os campos de número de série devem ser preenchidos.")
                elif len(set(seriais_input)) != len(seriais_input):
                    st.error("Erro: Existem números de série duplicados na lista.")
                else:
                    with st.spinner("Registrando compra e ativos..."):
                        try:
                            # ALTERAÇÃO: Formatação da NF
                            nf_formatada = formatar_nf_padrao(nf_raw)

                            # --- LÓGICA DE UPLOAD DO PDF ---
                            path_para_salvar = None
                            if uploaded_pdf is not None:
                                pdf_bytes = uploaded_pdf.getvalue()
                                # Usa a NF formatada no nome do arquivo para padronizar
                                file_path_in_storage = f"public/nf-{nf_formatada}.pdf"
                                try:
                                    supabase.storage.from_("NFs").upload(
                                        file_path_in_storage, pdf_bytes,
                                        {"content-type": "application/pdf", "upsert": "true"}
                                    )
                                    path_para_salvar = file_path_in_storage
                                except Exception as storage_error:
                                    st.error(f"Erro ao salvar PDF no Storage: {storage_error}")
                                    st.stop()

                            # --- ETAPA 1: INSERIR A COMPRA ---
                            loja_id_para_salvar = lojas_map[loja]
                            # ALTERAÇÃO: Pegando ID do comprador
                            comprador_id_para_salvar = colaboradores_map[comprador]
                            modelo_id_para_salvar = modelos_map[st.session_state.compra_modelo]
                            
                            nova_compra_dados = {
                                "data_compra": data_compra.isoformat(),
                                "nota_fiscal": nf_formatada, # Salva formatado
                                "loja_id": loja_id_para_salvar,
                                "comprador_id": comprador_id_para_salvar, # Novo campo salvo
                                "modelo_comprado_id": modelo_id_para_salvar, 
                                "valor_total": valor_total_nota if valor_total_nota > 0 else None,
                                "nf_url": path_para_salvar
                            }
                            
                            response_compra = supabase.table("compras").insert(nova_compra_dados).execute()
                            
                            if not response_compra.data:
                                st.error(f"Erro ao criar registro de compra: {response_compra.error.message}")
                                st.stop()
                            
                            nova_compra_id = response_compra.data[0]['id']
                            
                            # --- ETAPA 2: PREPARAR OS ATIVOS ---
                            status_id = status_map[status_selecionado]
                            estado_id = estados_map[estado_selecionado]
                            local_id = setores_map[setor_selecionado]
                            valor_unit = st.session_state.compra_valor

                            novos_ativos_lista = []
                            for serial in seriais_input:
                                novos_ativos_lista.append({
                                    "serial": serial.strip(),
                                    "modelo_id": modelo_id_para_salvar,
                                    "status_id": status_id,
                                    "estado_id": estado_id,
                                    "local_id": local_id,
                                    "valor": valor_unit, 
                                    "compra_id": nova_compra_id
                                })
                            
                            # --- ETAPA 3: INSERIR OS ATIVOS ---
                            response_ativos = supabase.table("ativos").insert(novos_ativos_lista).execute()

                            if response_ativos.data:
                                st.success(f"Compra {nf_formatada} cadastrada com sucesso!")
                                st.rerun()
                            else:
                                st.error(f"Erro ao cadastrar os ativos: {response_ativos.error.message}")
                                
                        except Exception as e:
                             st.error(f"Ocorreu um erro fatal: {e}")

    except Exception as e:
        st.error(f"Não foi possível carregar as opções de cadastro: {e}")

# --- ABA 02: Historico ---
with tab_historico:
    st.subheader("Últimas Compras Realizadas")
    st.markdown("Visualize as compras recentes e clique no botão para abrir o PDF da Nota Fiscal.")
    
    dados_hist = carregar_historico_compras()
    
    if dados_hist:
        df = pd.DataFrame(dados_hist)
        
        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
            column_config={
                "ID": None,
                "Valor Total": st.column_config.NumberColumn(format="R$ %.2f"),
                # Configuração visual para o comprador
                "Comprador": st.column_config.TextColumn("Comprador", width="medium"),
                "NF": st.column_config.TextColumn("Nota Fiscal", help="Formato 000.000.000"),
                "Comprovante": st.column_config.LinkColumn(
                    "Nota Fiscal",
                    display_text="Abrir PDF", 
                    help="Clique para visualizar o arquivo original"
                )
            }
        )
    else:
        st.info("Nenhuma compra com nota fiscal registrada ainda.")
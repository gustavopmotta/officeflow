import streamlit as st
from supabase import create_client, Client
import pandas as pd
import random

# --- Conexão com Supabase ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- Funções para Carregar Dados Auxiliares ---
def carregar_opcoes():
    """Busca dados das tabelas auxiliares para preencher os selectbox."""
    modelos = supabase.table("modelos").select("id, nome, categoria_id, marcas(nome)").order("nome").execute().data
    categorias = supabase.table("categorias").select("id, nome").order("nome").execute().data
    setores = supabase.table("setores").select("id, nome").order("nome").execute().data
    status = supabase.table("status").select("id, nome").order("nome").execute().data
    estados = supabase.table("estados").select("id, nome").order("nome").execute().data
    
    return modelos, categorias, setores, status, estados

# --- Página de Cadastro ---
st.title("Registrar Nova Compra de Ativos")
st.set_page_config(layout="wide")

# Não precisamos mais inicializar 'seriais_gerados'
# if 'seriais_gerados' not in st.session_state:
#     st.session_state.seriais_gerados = []

try:
    modelos_data, categorias_data, setores_data, status_data, estados_data = carregar_opcoes()

    # --- Mapeamentos ---
    categorias_map = {c['nome']: c['id'] for c in categorias_data}
    setores_map = {s['nome']: s['id'] for s in setores_data}
    status_map = {s['nome']: s['id'] for s in status_data}
    estados_map = {e['nome']: e['id'] for e in estados_data}

    if not categorias_map or not setores_map or not status_map or not estados_data:
        st.error("Dados auxiliares incompletos. Verifique o 'Cadastro Geral'.")
    else:
        # --- ETAPA 1: CATEGORIA DA COMPRA ---
        st.subheader("1. Categoria do Ativo")
        categoria_selecionada = st.selectbox("Categoria do Ativo", options=categorias_map.keys(), label_visibility="collapsed")

        if categoria_selecionada:
            categoria_id_selecionada = categorias_map[categoria_selecionada]
            modelos_filtrados = [
                m for m in modelos_data 
                if m.get('categoria_id') == categoria_id_selecionada
            ]
            
            # Criamos o mapa formatado
            modelos_filtrados_map = {}
            for m in modelos_filtrados:
                # Pega o nome da marca (com segurança)
                marca_nome = "Sem Marca"
                if m.get('marcas') and isinstance(m['marcas'], dict) and m['marcas'].get('nome'):
                    marca_nome = m['marcas']['nome']
                
                # Formata o nome de exibição: "Marca - Modelo"
                display_name = f"{marca_nome} {m['nome']}"
                modelos_filtrados_map[display_name] = m['id'] # A chave é o nome formatado, o valor é o ID
        else:
            modelos_filtrados_map = {} # Vazio se nenhuma categoria for selecionada

        # --- ETAPA 2: INFORMAÇÕES DA COMPRA ---
        st.subheader("2. Informações da Compra")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.selectbox("Modelo Comprado", options=modelos_filtrados_map.keys(), key="compra_modelo")
        with col2:
            st.number_input("Valor Unitário (R$)", min_value=0.01, format="%.2f", key="compra_valor")
        with col3:
            st.number_input("Quantidade Comprada", min_value=1, step=1, value=1, key="compra_qtd")
        
        st.divider()

        # --- LÓGICA DE CALLBACK (MODIFICADA) ---
        def gerar_seriais_callback():
            try:
                # Pega o nome formatado (ex: "DELL - LATITUDE 5490")
                modelo_display_name = st.session_state.compra_modelo
                qtd = st.session_state.compra_qtd
                
                # 1. Verifica se um modelo foi selecionado
                if not modelo_display_name:
                    st.warning("Por favor, selecione um modelo primeiro.")
                    return

                # 2. Encontra o ID do modelo usando o mapa formatado
                # (Se isso falhar, o 'except' abaixo vai pegar)
                modelo_id = modelos_filtrados_map[modelo_display_name]
                
                # 3. Encontra o objeto do modelo na lista de dados *completa*
                modelo_obj = next(m for m in modelos_data if m['id'] == modelo_id)
                
                # --- 4. VERIFICAÇÃO DE SEGURANÇA (A CORREÇÃO) ---
                # Verifica se a marca existe e tem um nome
                if modelo_obj.get('marcas') and isinstance(modelo_obj['marcas'], dict) and modelo_obj['marcas'].get('nome'):
                    marca_nome = modelo_obj['marcas']['nome'].split(' ')[0].upper()
                else:
                    marca_nome = "S-MARCA" # "S-MARCA" = "Sem Marca"
                # --- FIM DA CORREÇÃO ---
                
                # 5. Pega o nome do modelo
                modelo_prefixo = modelo_obj['nome'].split(' ')[0].upper()
                
                # 6. Gera os seriais
                for i in range(qtd):
                    sufixo_aleatorio = random.randint(10000, 99999)
                    novo_serial = f"{marca_nome}-{modelo_prefixo}-{sufixo_aleatorio}"
                    st.session_state[f"serial_{i}"] = novo_serial
                
            except Exception as e:
                # Mensagem de erro mais detalhada
                st.error(f"Erro ao gerar seriais: {e}")
                st.info(f"Ocorreu um erro ao processar o modelo: '{st.session_state.compra_modelo}'. Verifique se este modelo possui uma marca associada no 'Cadastro Geral'.")

        # --- Botão Gerador ---
        st.button(
            "Gerar Seriais Sugeridos",
            on_click=gerar_seriais_callback,
            help="Preenche os campos abaixo com seriais únicos baseados na Marca e Modelo."
        )

        # --- ETAPA 3: FORMULÁRIO DE REGISTRO ---
        st.subheader("3. Registro dos Números de Série")
        
        qtd_real = st.session_state.compra_qtd

        with st.form("form_compra_ativos"):
            
            seriais_input = []
            cols = st.columns(3)
            # Não precisamos mais de 'seriais_gerados' ou 'valor_padrao' aqui

            for i in range(qtd_real):
                with cols[i % 3]:
                    # O widget agora lê seu valor automaticamente do session_state
                    # graças ao parâmetro 'key'.
                    serial = st.text_input(
                        f"Serial {i+1}",
                        key=f"serial_{i}" # Esta é a parte importante
                    )
                    seriais_input.append(serial)
            
            st.divider()
            
            # --- Status, Estado e Setor ---
            st.write("Definir o status inicial para todos os ativos desta compra:")
            col_status, col_estado, col_setor = st.columns(3)
            with col_status:
                status_keys = list(status_map.keys())
                status_selecionado = st.selectbox("Status Inicial", options=status_keys)
            
            with col_estado:
                estado_keys = list(estados_map.keys())
                estado_selecionado = st.selectbox("Estado Inicial", options=estado_keys)
            
            with col_setor:
                setor_keys = list(setores_map.keys())
                setor_selecionado = st.selectbox("Setor Inicial", options=setor_keys)

            submitted = st.form_submit_button("Cadastrar Todos os Ativos")

        # --- ETAPA 3: LÓGICA DE SUBMISSÃO ---
        if submitted:
            # Não precisamos mais limpar 'seriais_gerados'
            
            # Validação
            if any(s.strip() == "" for s in seriais_input):
                st.error("Erro: Todos os campos de número de série devem ser preenchidos.")
            elif len(set(seriais_input)) != len(seriais_input):
                st.error("Erro: Existem números de série duplicados na sua lista.")
            else:
                try:
                    # Preparar os dados para o Supabase
                    modelo_id = modelos_filtrados_map[st.session_state.compra_modelo]
                    status_id = status_map[status_selecionado]
                    estado_id = estados_map[estado_selecionado]
                    local_id = setores_map[setor_selecionado]
                    valor_unit = st.session_state.compra_valor

                    novos_ativos_lista = []
                    for serial in seriais_input:
                        novos_ativos_lista.append({
                            "serial": serial.strip(),
                            "modelo_id": modelo_id,
                            "status_id": status_id,
                            "estado_id": estado_id,
                            "local_id": local_id,
                            "valor": valor_unit 
                        })
                    
                    response = supabase.table("ativos").insert(novos_ativos_lista).execute()
                    
                    if response.data:
                        st.success(f"{len(response.data)} novo(s) ativo(s) cadastrados com sucesso!")
                        st.rerun() # Limpa o formulário e recarrega
                    else:
                        st.error(f"Erro ao salvar no banco de dados: {response.error.message}")
                except Exception as e:
                     st.error(f"Ocorreu um erro ao processar os dados: {e}")

except Exception as e:
    st.error(f"Não foi possível carregar as opções de cadastro: {e}")
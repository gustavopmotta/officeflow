import streamlit as st
import pandas as pd
from utils import verificar_autenticacao

# --- Autenticação e Conexão ---
supabase = verificar_autenticacao()

st.title("Gerenciamento de Dados")
st.markdown("Importação e exportação em massa para o banco de dados.")

# --- Definição de Segurança ---
# Lista de tabelas permitidas para evitar acesso indevido a tabelas de sistema
TABELAS_DISPONIVEIS = ["ativos", "movimentacoes", "manutencoes", "setores", "usuarios"]

# --- Estrutura de Navegação Interna ---
aba_export, aba_import = st.tabs(["Exportar (Download)", "Importar (Upload)"])

# --- Aba 1: Exportação de Dados ---
with aba_export:
    st.header("Exportar Dados para CSV")
    st.caption("Selecione a tabela desejada para baixar os dados atuais.")

    tabela_selecionada = st.selectbox(
        "Selecione a Tabela:", 
        TABELAS_DISPONIVEIS, 
        key="sel_export"
    )

    if st.button("Carregar Dados"):
        with st.spinner(f"Baixando dados de '{tabela_selecionada}'..."):
            try:
                # 1. Busca dados no Supabase
                response = supabase.table(tabela_selecionada).select("*").execute()
                dados = response.data

                if len(dados) > 0:
                    # 2. Conversão para DataFrame
                    df = pd.DataFrame(dados)
                    
                    # 3. Exibição de prévia
                    st.dataframe(df, width="stretch", hide_index=True)
                    st.caption(f"Total de registros encontrados: {len(df)}")

                    # 4. Preparação do arquivo CSV
                    csv = df.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig")

                    # 5. Disponibilização do Download
                    st.download_button(
                        label="Baixar arquivo .csv",
                        data=csv,
                        file_name=f"{tabela_selecionada}_export.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("A tabela selecionada está vazia.")
            
            except Exception as e:
                st.error(f"Erro ao exportar: {e}")

# --- Aba 2: Importação de Dados ---
with aba_import:
    st.header("Importar Dados via CSV")
    st.warning("Atenção: As colunas do CSV devem ter exatamente o mesmo nome das colunas no banco de dados.")

    tabela_destino = st.selectbox(
        "Tabela de Destino:", 
        TABELAS_DISPONIVEIS, 
        key="sel_import"
    )

    arquivo_upload = st.file_uploader("Escolha o arquivo CSV", type=["csv"])

    if arquivo_upload is not None:
        try:
            # 1. Leitura do arquivo
            try:
                # Tenta padrão Web (UTF-8)
                df_upload = pd.read_csv(arquivo_upload, sep=';', decimal=',', encoding='utf-8-sig', dtype=str)
            except:
                # Se der erro, tenta padrão Excel (Latin-1)
                arquivo_upload.seek(0)
                df_upload = pd.read_csv(arquivo_upload, sep=';', decimal=',', encoding='latin1', dtype=str)
            
            st.subheader("Pré-visualização dos dados")
            st.dataframe(df_upload, width="stretch", hide_index=True)
            st.info(f"Registros prontos para importação: {len(df_upload)}")

            # 2. Ação de Importação
            if st.button("Confirmar Importação no Banco de Dados", type="primary"):
                with st.spinner("Enviando dados para o Supabase..."):
                    # Conversão de Inteiros
                    for col in df_upload.select_dtypes(include=['float']).columns:
                        is_integer = df[col].dropna().apply(lambda x: x.is_integer()).all()
                        
                        if is_integer:
                            df_upload[col] = df_upload[col].astype('Int64')

                    # Tratamento de dados nulos (NaN -> None) para compatibilidade SQL
                    df_upload = df_upload.where(pd.notnull(df_upload), None)
                    
                    # Conversão para formato de dicionário
                    dados_para_inserir = df_upload.to_dict(orient='records')

                    # Inserção em lote
                    supabase.table(tabela_destino).insert(dados_para_inserir).execute()
                    
                    st.success("Importação realizada com sucesso!")

        except Exception as e:
            st.error("Falha na importação. Verifique se os nomes das colunas estão corretos.")
            with st.expander("Ver detalhes do erro"):
                st.write(e)
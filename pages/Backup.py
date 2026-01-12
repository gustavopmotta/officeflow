import streamlit as st
import pandas as pd
import zipfile
import io
import numpy as np
from utils import verificar_autenticacao

# --- Autenticação e Conexão ---
supabase = verificar_autenticacao()

st.title("Sistema de Backup e Restauração")
st.markdown("Crie cópias de segurança de todo o banco de dados antes de realizar testes.")

# --- Definição de Tabelas ---
TABELAS_ORDENADAS = [
    "marcas", "modelos", "setores", "status", "usuarios", # Cadastros Básicos
    "ativos",                                             # Depende dos anteriores
    "movimentacoes", "manutencoes"                        # Dependem de ativos
]

# --- Estrutura de Abas ---
aba_backup, aba_restore = st.tabs(["Gerar Backup (Snapshot)", "Restaurar Banco de Dados"])

# --- Aba 1: Gerar Backup ---
with aba_backup:
    st.header("Criar Snapshot do Sistema")
    st.markdown("Esta ação baixará um arquivo .zip contendo todas as tabelas do sistema em formato CSV.")

    if st.button("Gerar Backup Completo", type="primary"):
        with st.spinner("Compilando dados de todas as tabelas..."):
            try:
                # Buffer em memória para o arquivo ZIP
                zip_buffer = io.BytesIO()

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    total_registros = 0
                    
                    for tabela in TABELAS_ORDENADAS:
                        # Busca todos os dados da tabela
                        response = supabase.table(tabela).select("*").execute()
                        dados = response.data
                        
                        if dados:
                            df = pd.DataFrame(dados)
                            total_registros += len(df)
                            
                            # Converte para CSV
                            csv_data = df.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig")
                            
                            # Adiciona ao ZIP
                            zip_file.writestr(f"{tabela}.csv", csv_data)
                
                # Finaliza o ZIP
                zip_buffer.seek(0)
                st.success(f"Backup gerado com sucesso! Total de {total_registros} registros processados.")
                
                # Botão de Download
                st.download_button(
                    label="Baixar Arquivo de Backup (.zip)",
                    data=zip_buffer,
                    file_name="officeflow_full_backup.zip",
                    mime="application/zip"
                )

            except Exception as e:
                st.error(f"Erro ao gerar backup: {e}")

# --- Aba 2: Restaurar Backup ---
with aba_restore:
    st.header("Restaurar Dados")
    st.warning("Atenção: A restauração pode sobrescrever dados existentes!")
    
    arquivo_zip = st.file_uploader("Upload do arquivo de backup (.zip)", type="zip")
    
    # Opção perigosa para limpar antes de restaurar
    limpar_antes = st.checkbox("Limpar tabelas antes de restaurar (Recomendado para 'Reset' total)")

    if arquivo_zip is not None and st.button("Iniciar Restauração"):
        with st.spinner("Processando arquivo de backup..."):
            try:
                with zipfile.ZipFile(arquivo_zip, "r") as z:
                    # Itera na ordem correta de inserção
                    for tabela in TABELAS_ORDENADAS:
                        nome_arquivo = f"{tabela}.csv"
                        
                        if nome_arquivo in z.namelist():
                            # Lê o CSV do ZIP
                            with z.open(nome_arquivo) as f:
                                try:
                                    # Tenta ler formato BR
                                    df = pd.read_csv(f, sep=';', decimal=',')
                                except:
                                    # Fallback para formato padrão
                                    f.seek(0)
                                    df = pd.read_csv(f, sep=',', decimal='.')
                            
                            if not df.empty:
                                # Conversão de Inteiros
                                for col in df.select_dtypes(include=['float']).columns:
                                    is_integer = df[col].dropna().apply(lambda x: x.is_integer()).all()
                                    
                                    if is_integer:
                                        df[col] = df[col].astype('Int64')

                                # Tratamento de Nulos
                                df = df.astype(object)
                                df = df.where(pd.notnull(df), None)

                                dados = df.to_dict(orient='records')
                                
                                # 1. Limpeza (Se selecionado)
                                if limpar_antes:
                                    try:
                                        supabase.table(tabela).delete().neq("id", 0).execute()
                                    except:
                                        pass

                                # 2. Upsert (Atualiza se existir ID, Cria se não existir)
                                supabase.table(tabela).upsert(dados).execute()
                                st.write(f"Tabela '{tabela}': {len(dados)} registros restaurados.")
                
                st.success("Processo de restauração finalizado!")
                st.info("Recomendamos atualizar a página para visualizar os dados restaurados.")

            except Exception as e:
                st.error(f"Falha na restauração: {e}")
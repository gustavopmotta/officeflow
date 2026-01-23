# OfficeFlow - Sistema de Gestão de Patrimônio

> Um sistema completo, minimalista e eficiente para controle de ativos, movimentações e manutenção, construído com **Streamlit** e **Supabase**.

![Badge em Desenvolvimento](https://img.shields.io/badge/Versão-0.8.1-F05032?style=flat-square&logo=git)
![Python](https://img.shields.io/badge/Python-3.13.3%2B-3776AB?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.53.1%2B-FF4B4B?style=flat-square&logo=streamlit)
![Supabase](https://img.shields.io/badge/Database-Supabase-3FCF8E?style=flat-square&logo=supabase)

---

## Sobre o Projeto

O **OfficeFlow** é uma solução web para gerenciamento de inventário e patrimônio corporativo. O sistema permite o rastreamento completo do ciclo de vida dos ativos, desde a aquisição, movimentação entre setores/usuários, até o registro de manutenções e descarte.

O diferencial do projeto é sua interface focada em usabilidade (UX) e suas ferramentas robustas de administração de dados, permitindo migrações e backups seguros.

## Funcionalidades Principais

### Operacional
* **Gestão de Ativos:** Cadastro completo de equipamentos (Patrimônio, Marca, Modelo, Setor, Status).
* **Movimentações:** Registro de transferência de ativos entre setores ou responsáveis.
* **Manutenções:** Histórico de reparos, custos e fornecedores.

### Administrativo
* **Cadastros Auxiliares:** Gerenciamento centralizado de Marcas, Modelos, Setores e Status.
* **Gestão de Usuários:** Controle de acesso e perfis (Admin/User).
* **Autenticação Segura:** Login integrado via Supabase Auth.

### Segurança e Dados (Destaques)
* **Backup & Restore (Snapshots):**
    * Geração de **Backups Completos (.zip)** com um clique.
    * Arquivos CSV formatados especificamente para **Excel Brasileiro** (Separador `;`, Decimal `,`, UTF-8-SIG).
    * **Restauração Inteligente:** O sistema aceita uploads de backups, sanitiza os dados (converte `NaN` para `NULL`), corrige tipagem de inteiros e previne duplicidade.
* **Importação em Massa (Smart Import):**
    * Permite cadastrar centenas de ativos via planilha CSV.
    * **Tradução Automática:** O usuário escreve o **NOME** do setor/marca (ex: "TI", "Dell") e o sistema busca automaticamente o **ID** correspondente no banco de dados.
    * Blindagem contra erros de codificação (`UTF-8` vs `Latin-1/Excel`).

## Tecnologias Utilizadas

* **Frontend/Backend:** [Streamlit](https://streamlit.io/) (Python)
* **Banco de Dados:** [Supabase](https://supabase.com/) (PostgreSQL)
* **Manipulação de Dados:** Pandas & Numpy
* **Visualização:** Matplotlib (para geração de logos/gráficos)

## Estrutura do Projeto

```text
officeflow/
├── assets/              # Imagens e Logos
├── pages/               # Páginas da aplicação (Multipage App)
│   ├── Backups.py       # Sistema de Backup e Restore
│   ├── Importar.py      # Importação e Exportação de Dados
│   ├── Ativos.py        # Gestão Operacional
│   └── ...
├── utils.py             # Funções globais (Auth, Sidebar, Conexão DB)
├── streamlit_app.py     # Ponto de entrada (Entrypoint)
├── requirements.txt     # Dependências do Python
└── README.md            # Documentação
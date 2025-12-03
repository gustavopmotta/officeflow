import streamlit as st

# --- Barra lateral Global do Site ---
def sidebar_global():
    with st.sidebar:
        st.markdown("### OfficeFlow")
        st.caption("Sistema de Gestão de Ativos")
        
        st.divider()
        
        st.markdown("Desenvolvido pela TI")
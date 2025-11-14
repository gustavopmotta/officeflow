from supabase import create_client
import streamlit as st
import os

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

name = st.text_input("Nome")
category = st.number_input("Categoria ID", step=1)
description = st.text_area("Descrição")

if st.button("Salvar"):
    data = {
        "name": name,
        "category_id": category,
        "description": description
    }

    result = supabase.table("assets").insert(data).execute()
    st.success("Asset criado!")
    st.json(result.data)
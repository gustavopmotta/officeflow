from supabase import create_client
import streamlit as st
import os

SUPABASE_URL = st.secrets["https://lhidxhtvxbqtkelswenl.supabase.co"]
SUPABASE_KEY = st.secrets["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxoaWR4aHR2eGJxdGtlbHN3ZW5sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMwNjUyNjgsImV4cCI6MjA3ODY0MTI2OH0.J9RMaCpxyDe42NLKx1hz8pCCex4xG5a_B4i7_vWfB_w"]

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
import streamlit as st

st.set_page_config(
    page_title="Semantic Pokédex",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🕸️Pokédex")
st.caption("INFOMKDE Project | Utrecht University")
st.divider()
st.subheader("📊 Current Graph Status (dummy data)")
stat1, stat2, stat3, stat4 = st.columns(4)
stat1.metric("Total Triples", "15,402")
stat2.metric("Classes (Ontology)", "48")
stat3.metric("Linked Entities", "151")
stat4.metric("Inference Rules", "12")

st.success("👈 **Start by clicking 'Search Engine' in the sidebar!**")
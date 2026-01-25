import streamlit as st

# config
st.set_page_config(
    page_title="Semantic Pokédex | Group 1",
    page_icon="🔴",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# session state
if "first_load" not in st.session_state:
    st.session_state.first_load = True
    st.balloons()
    st.session_state.first_load = False

col_logo, col_title = st.columns([1, 2.5])

with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/9/98/International_Pokémon_logo.svg",
             use_container_width=True)

with col_title:
    st.title("Semantic Pokédex")
    st.markdown("##### **Knowledge and Data Engineering Project**")
    st.caption("Group 1 • Utrecht University")

st.divider()

with st.container(border=True):
    col_anim, col_desc = st.columns([1.2, 2], gap="medium")

    with col_anim:
        st.image(
            "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3MXI2anFtdDF3aTU4MGU2bHR2c2pmN3J0ejR6MGJwMzViNmkweHU0aiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/xx0JzzsBXzcMK542tx/giphy.gif",
            use_container_width=True
        )

    with col_desc:
        st.markdown("### 🚀 Welcome!")

        if st.button("🔍 Enter the search page ->", type="primary", use_container_width=True):
            st.switch_page("pages/search.py")


st.subheader("🛠️ System Architecture")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("**1. Ontology**", icon="🧠")
    st.markdown("Defined in **Protégé**. Models the hierarchy (e.g., `Wings` $\\sqsubseteq$ `BodyPart`).")

with col2:
    st.success("**2. Data**", icon="🗄️")
    st.markdown("Stored in **GraphDB**. Contains heterogeneous data (Anatomy + Generation 1 stats).")

with col3:
    st.warning("**3. Interface**", icon="💻")
    st.markdown("Built with **Streamlit**. Used SPARQL queries and Visual Models.")

st.divider()

st.subheader("👥 The Team")

team_cols = st.columns(2)

with team_cols[0]:
    st.markdown("**Ali Nesaei**")


    st.markdown("**Andrea Suklan**")


    st.markdown("**Shallwin Silvania**")


with team_cols[1]:
    st.markdown("**Jelke de Haan**")

    st.markdown("**Samuel Sorour**")


st.divider()

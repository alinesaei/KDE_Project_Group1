import streamlit as st

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="Semantic Pokédex | Group 1",
    page_icon="🔴",
    layout="centered"  # "Centered" looks better for a landing page than "Wide"
)

# 2. SESSION STATE (For the entry animation)
if "first_load" not in st.session_state:
    st.session_state.first_load = True
    st.balloons()  # 🎉 Fun entry animation!
    st.session_state.first_load = False

# 3. HEADER & LOGO
col_logo, col_title = st.columns([1, 2])

with col_logo:
    # A high-quality transparent Pokemon logo
    st.image("https://upload.wikimedia.org/wikipedia/commons/9/98/International_Pokémon_logo.svg",
             use_container_width=True)

with col_title:
    st.title("Semantic Pokédex")
    st.subheader("Knowledge Engineering Project")
    st.caption("Group 1 • Utrecht University")

st.divider()

# 4. INTRO ANIMATION (A classic Pokedex GIF)
# We put this in a container to make it look like a "Hero Section"
with st.container(border=True):
    col_anim, col_desc = st.columns([1, 2], gap="medium")

    with col_anim:
        # A clean GIF of a Pokedex
        st.image(
            "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3MXI2anFtdDF3aTU4MGU2bHR2c2pmN3J0ejR6MGJwMzViNmkweHU0aiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/xx0JzzsBXzcMK542tx/giphy.gif",
            use_container_width=True)

    with col_desc:
        st.markdown("### 🚀 Welcome!")
        # st.write("""
        # This isn't just a database—it's a **Knowledge Graph**.
        #
        # Unlike a standard wiki, this app understands **Anatomy**.
        # If you search for *"Wings"*, it knows to look for *Dragon Wings*, *Bug Wings*, and *Feathered Wings* automatically.
        # """)

        # Call to Action Button
        if st.button("🔍 Start Searching Now", type="primary", use_container_width=True):
            st.switch_page("pages/search.py")

# 5. TECHNICAL ARCHITECTURE (The "Student Project" part)
st.subheader("🛠️ Architecture")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("**Ontology (TBox)**")
    st.markdown("Modeled in **Protégé**. Defines the hierarchy (e.g., `Teeth` $\\subseteq$ `Mouth`).")

with col2:
    st.success("**Data (ABox)**")
    st.markdown("Stored in **GraphDB**. Contains the instances (e.g., `Charizard` has `DragonWings`).")

with col3:
    st.warning("**Application**")
    st.markdown("Built with **Streamlit** & **SPARQL**. Handles the logic and visualization.")

st.divider()

# 6. TEAM MEMBERS
st.markdown("### 👥 The Team")

#
# for i, member in enumerate(members):
#     with team_cols[i % 4]:
#         st.caption(f"👤 {member}")

import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from streamlit_agraph import agraph, Node, Edge, Config
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from utils.mock_data import get_mock_pokemon, get_pokemon_by_id
except ImportError:
    st.error("⚠️ Error: Could not find 'utils/mock_data.py'. Please create it first.")
    st.stop()

# --- PAGE CONFIG ---
st.set_page_config(page_title="Search Engine", page_icon="🔍", layout="wide")


if "selected_pokemon_id" not in st.session_state:
    st.session_state.selected_pokemon_id = None


# --- HELPER: KNOWLEDGE GRAPH VISUALIZER ---
def render_interactive_graph(poke_name, relations):
    """
    Renders the interactive node-link diagram
    """
    nodes = []
    edges = []

    # central node (the pokemon)
    nodes.append(Node(id=poke_name, label=poke_name, size=25, color="#ff4b4b"))

    #connected Nodes
    if relations:
        for rel in relations:
            # Avoid duplicate nodes
            if rel["target"] not in [n.id for n in nodes]:
                # Color code: Types (Orange), Biology (Blue), Evolution (Green)
                if rel["label"] == "hasType":
                    color = "#FFA500"  # Orange
                elif rel["label"] == "evolvesTo":
                    color = "#28a745"  # Green
                else:
                    color = "#00BFFF"  # Blue

                nodes.append(Node(id=rel["target"], label=rel["target"], size=15, color=color))

            edges.append(Edge(source=rel["source"], target=rel["target"], label=rel["label"]))
    config = Config(
        width="100%",
        height=350,
        directed=True,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False
    )

    return agraph(nodes=nodes, edges=edges, config=config)


# --- VIEW 1: DETAILS PAGE ---
def show_details_view():
    """
    Shows the specific information for one Pokemon when selected.
    """
    poke_id = st.session_state.selected_pokemon_id
    poke = get_pokemon_by_id(poke_id)

    # back button
    if st.button("⬅️ Back to Search"):
        st.session_state.selected_pokemon_id = None
        st.rerun()

    if not poke:
        st.error("Pokemon not found!")
        return
    col_left, col_right = st.columns([1, 2], gap="large")

    with col_left:
        # Image and Title
        st.image(poke['img'], use_container_width=True)
        st.markdown(f"## #{poke['id']} {poke['name']}")
        type_html = "".join([
                                f"<span style='background-color:#eee; color:black; padding:4px 10px; border-radius:15px; margin-right:5px; font-weight:bold'>{t}</span>"
                                for t in poke['type']])
        st.markdown(type_html, unsafe_allow_html=True)

        st.markdown(f"**_{poke['desc']}_**")

        # Basic Info Box
        st.info(f"**Evolves From:** {poke.get('evolves_from', 'None')}")
        st.warning(f"**Weakness:** {', '.join(poke.get('weakness', []))}")

    with col_right:
        # Knowledge graph visualization
        st.subheader("🕸️ Semantic Network")
        st.caption(f"Visualizing RDF triples centered on **{poke['name']}**.")

        # Call the graph helper
        render_interactive_graph(poke['name'], poke.get('relations', []))

    st.divider()

    tab_stats, tab_ont, tab_lod, tab_reasoning = st.tabs(["📊 Stats", "🧬 Ontology", "🌍 Linked Data", "⚡ Reasoning"])

    with tab_stats:
        col_stat_text, col_stat_chart = st.columns([1, 2])
        with col_stat_text:
            st.write("#### Base Statistics")
            stats = poke.get('stats', {})
            for k, v in stats.items():
                st.progress(v / 150, text=f"{k}: {v}")

        with col_stat_chart:
            # Radar Chart using Plotly
            df_stats = pd.DataFrame(dict(r=list(stats.values()), theta=list(stats.keys())))
            fig = px.line_polar(df_stats, r='r', theta='theta', line_close=True)
            fig.update_traces(fill='toself', line_color='#ff4b4b')
            fig.update_layout(height=300, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

    with tab_ont:
        st.info("Visualizing the Class Hierarchy (T-Box) for inferred features.")
        st.graphviz_chart(f"""
            digraph {{
                rankdir=LR;
                node [shape=box, style=filled, fillcolor="#f0f2f6"];
                "AnatomicalPart" -> "Limb";
                "AnatomicalPart" -> "SensoryOrgan";
                "Limb" -> "Wings" [color=red, penwidth=2];
                "Limb" -> "Arms";

                "{poke['name']}" [shape=oval, fillcolor="#ffbd45", style=filled];
                "Wings" -> "{poke['name']}" [label="hasVisualFeature", style=dashed];
            }}
        """)

    with tab_lod:
        st.markdown("### External Knowledge Sources")
        st.markdown("This data is federated from external SPARQL endpoints.")
        st.markdown(f"- **Wikidata ID:** [`Q{poke['id'] * 123}`]({poke.get('wikidata_url', '#')})")
        st.markdown(f"- **DBpedia URI:** `dbr:{poke['name']}`")
        st.success("✅ Linked Data Verified")

    with tab_reasoning:
        st.markdown("### 🧠 Inference Trace")
        st.code(f"""
        # Why is {poke['name']} classified as a FirePokemon?

        # Fact 1 (Triple):
        ex:{poke['name']} rdf:type ex:Pokemon .
        ex:{poke['name']} ex:hasType ex:Fire .

        # Rule (OWL Restriction):
        ex:FirePokemon owl:equivalentClass [
            a owl:Class ;
            owl:intersectionOf (
                ex:Pokemon 
                [ a owl:Restriction ; owl:onProperty ex:hasType ; owl:hasValue ex:Fire ]
            )
        ] .

        # Conclusion (Inferred Triple):
        >> ex:{poke['name']} rdf:type ex:FirePokemon .
        """, language="turtle")


def show_search_view():
    st.markdown("## 🔍 Knowledge Graph Explorer")
    st.markdown("---")

    col_filters, col_results = st.columns([1, 3], gap="large")

    with col_filters:
        st.subheader("🛠️ Filters")
        with st.form("filter_form"):
            st.write("#### 📂 Classification")
            selected_types = st.multiselect(
                "Pokemon Type",
                ["Fire", "Water", "Grass", "Electric", "Psychic", "Flying", "Bug", "Normal"],
                default=["Fire", "Flying"]
            )

            st.write("#### 🧬 Anatomy (Ontology)")
            st.caption("Filter by inferred body parts")
            st.multiselect("Limbs", ["Wings", "Claws", "Arms", "Legs"])
            st.multiselect("Sensors", ["Antenna", "Ears", "Whiskers"])

            st.write("#### 🎨 Appearance")
            st.selectbox("Color", ["Any", "Red", "Blue", "Green", "Yellow"])

            st.markdown("---")
            submitted = st.form_submit_button("🚀 Apply Filters", type="primary")

    with col_results:
        if submitted:
            st.success(f"Searching for types: **{', '.join(selected_types)}**")

        # Get data (mock for now, SPARQL later)
        data = get_mock_pokemon()

        st.subheader(f"Results ({len(data)})")

        # Custom Grid Layout
        grid_cols = st.columns(3)
        for index, poke in enumerate(data):
            with grid_cols[index % 3]:
                with st.container(border=True):
                    st.image(poke["img"], use_container_width=True)
                    st.markdown(f"**#{poke['id']} {poke['name']}**")

                    # Pill badges for types
                    type_html = "".join([
                                            f"<span style='background-color:#eee; padding:2px 8px; border-radius:10px; margin-right:4px; font-size:12px'>{t}</span>"
                                            for t in poke['type']])
                    st.markdown(type_html, unsafe_allow_html=True)

                    st.caption(f"🧬 {', '.join(poke['features'][:3])}")

                    if st.button("Details ➡️", key=f"btn_{poke['id']}"):
                        st.session_state.selected_pokemon_id = poke['id']
                        st.rerun()




# 1. Top Navigation Menu
selected_tab = option_menu(
    menu_title=None,
    options=["Search", "Analytics"],
    icons=["search", "bar-chart-fill"],
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#fafafa"},
        "nav-link-selected": {"background-color": "#ff4b4b"},
    }
)

# 2. View Switching Logic
if selected_tab == "Search":
    if st.session_state.selected_pokemon_id is not None:
        show_details_view()
    else:
        show_search_view()

elif selected_tab == "Analytics":
    st.info("Nothing to see here for now :)")

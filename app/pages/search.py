import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_agraph import agraph, Node, Edge, Config
from streamlit_option_menu import option_menu
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from utils.db_connector import (
        get_gen1_data,
        get_ontology_options,
        get_pokemon_details,
        get_ontology_hierarchy,
        get_feature_counts,
        execute_custom_sparql
    )
    from utils.NLtoQuery import extract_ontology_terms, generate_sparql

    NLP_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ System Error: {e}")
    NLP_AVAILABLE = False

st.set_page_config(page_title="Search Engine", page_icon="🔍", layout="wide")

# --- STATE MANAGEMENT
#Which Pokemon are we looking at?
if "selected_pokemon_name" not in st.session_state:
    st.session_state.selected_pokemon_name = None

# keeping the result
if "ai_search_df" not in st.session_state:
    st.session_state.ai_search_df = None

# cache Ontology
if "ont_opts" not in st.session_state:
    st.session_state.ont_opts = []  # Will load later


# search dashboard
def show_search_dashboard():
    st.title("🔍 Semantic Search")
    st.markdown("Explore the Knowledge Graph using standard filters or natural language.")

    tab_manual, tab_ai = st.tabs(["🎛️ Standard Filters", "💬 AI Search"])

    with tab_manual:
        col_filters, col_results = st.columns([1, 4], gap="large")

        with col_filters:
            st.subheader("Filters")
            with st.form("manual_filter_form"):
                # Load options if empty
                if not st.session_state.ont_opts:
                    st.session_state.ont_opts = get_ontology_options()

                st.markdown("**🧬 Anatomy**")
                st.caption("Finds parts via reasoning (e.g., 'Head' -> 'Teeth')")
                sel_part = st.selectbox("Body Part", ["Any"] + st.session_state.ont_opts)

                st.markdown("**🎨 Appearance**")
                sel_color = st.selectbox("Color",
                                         ["Any", "Red", "Blue", "Green", "Yellow", "Purple", "Brown", "Pink", "Black",
                                          "White"])

                submitted = st.form_submit_button("🚀 Apply Filters", type="primary")

        with col_results:
            # Fetch Data
            df = get_gen1_data(body_part=sel_part, color=sel_color)
            render_results_grid(df, key_suffix="manual")

    #ai tab
    with tab_ai:
        st.markdown("#### 🧠 Ask the Ontology")

        col_input, col_debug = st.columns([3, 1])
        with col_input:
            with st.form("ai_search_form"):
                user_query = st.text_input("Describe your Pokemon:",
                                           placeholder="Example: I want a dragon with wings and claws...")
                run_ai = st.form_submit_button("✨ Generate SPARQL & Search")

        # to check if just clicked button
        if run_ai and user_query:
            if not NLP_AVAILABLE:
                st.error("NLP Module not loaded.")
            else:
                with st.spinner("Analyzing semantics..."):
                    # reset previous results
                    st.session_state.ai_search_df = None

                    # extract terms
                    uris, logs = extract_ontology_terms(user_query)

                    with col_debug:
                        with st.expander("🤖 Logic Trace", expanded=False):
                            for log in logs:
                                st.text(f"• {log}")
                            if not uris:
                                st.warning("No ontology terms matched.")

                    if uris:
                        sparql_query = generate_sparql(uris)
                        # execute and save the session
                        results = execute_custom_sparql(sparql_query)
                        st.session_state.ai_search_df = results

                        # Show the generated query
                        with st.expander("View Generated SPARQL Code"):
                            st.code(sparql_query, language="sparql")
                    else:
                        st.warning(
                            "I couldn't understand the anatomical features in your request. Try words like 'wings', 'tail', 'claws'.")

        if st.session_state.ai_search_df is not None:
            st.divider()
            render_results_grid(st.session_state.ai_search_df, key_suffix="ai")


def show_details_view():
    name = st.session_state.selected_pokemon_name
    poke = get_pokemon_details(name)  # Fetch real details

    # Top Navigation Bar
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("⬅️ Back to Search"):
            st.session_state.selected_pokemon_name = None
            st.rerun()
    with col_title:
        st.subheader(f"Analyzing: {name}")

    st.divider()

    # Main layout
    col_img, col_graph, col_stats = st.columns([1, 2, 1])

    with col_img:
        st.image(poke['img'], use_container_width=True)
        st.markdown(f"### {poke['name']}")

        st.info("🧬 **Inferred Attributes**")
        if poke['features']:
            # Render attributes as tags
            st.markdown(" ".join([f"`{f}`" for f in poke['features']]))
        else:
            st.write("No attributes found.")

    with col_graph:
        st.markdown("#### 🕸️ Knowledge Graph")
        # graph
        nodes = [Node(id=poke['name'], label=poke['name'], size=25, color="#ff4b4b")]
        edges = []
        for rel in poke['relations']:
            # Avoid duplicate nodes
            if rel['target'] not in [n.id for n in nodes]:
                nodes.append(Node(id=rel['target'], label=rel['target'], size=15, color="#00BFFF"))
            edges.append(Edge(source=rel['source'], target=rel['target'], label=rel['label']))

        config = Config(width="100%", height=400, directed=True, nodeHighlightBehavior=True, highlightColor="#F7A7A6")
        agraph(nodes=nodes, edges=edges, config=config)

    with col_stats:
        st.markdown("#### 📊 Base Stats")
        stats = poke['stats']
        df = pd.DataFrame(dict(r=list(stats.values()), theta=list(stats.keys())))
        fig = px.line_polar(df, r='r', theta='theta', line_close=True)
        fig.update_traces(fill='toself', line_color='#ff4b4b')
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 150])), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


# analytics
def show_analytics_view():
    st.title("📊 Knowledge Graph Analytics")
    st.markdown("Overview of the Ontology structure and Dataset distribution.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧬 Ontology Hierarchy")
        st.caption("Sunburst chart showing 'part-of' relationships.")
        df_ont = get_ontology_hierarchy()
        if not df_ont.empty:
            df_ont.loc[len(df_ont)] = ["Body", "MainBody"]
            fig = px.sunburst(df_ont, names='child', parents='parent')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No ontology data found.")

    with col2:
        st.subheader("📈 Feature Distribution")
        st.caption("Most frequent anatomical features in Gen 1.")
        df_counts = get_feature_counts()
        if not df_counts.empty:
            fig2 = px.bar(df_counts, x='count', y='feature', orientation='h', color='count')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No data found.")


# RESULT GRID RENDERER
def render_results_grid(df, key_suffix="default"):
    """
    Renders a grid of Pokemon cards.
    Args:
        key_suffix: A unique string (e.g., 'ai', 'manual') to prevent duplicate button ID errors.
    """
    if df.empty:
        st.info("No Pokemon found matching these criteria.")
        return

    st.success(f"Found {len(df['name'].unique())} Pokemon")

    cols = st.columns(4)
    grouped = df.groupby("name")

    for i, (name, group) in enumerate(grouped):
        first = group.iloc[0]
        with cols[i % 4]:
            with st.container(border=True):
                st.image(first['img'], use_container_width=True)
                st.markdown(f"**{name}**")

                if 'color' in first and first['color'] != "Unknown":
                    st.caption(f"🎨 {first['color']}")

                # key generation just to prevent crashingg
                unique_key = f"btn_{name}_{key_suffix}"

                if st.button("Details ➡️", key=unique_key, use_container_width=True):
                    st.session_state.selected_pokemon_name = name
                    st.rerun()


# if Pokemon is selected, show its details (Overwrites everything else)
if st.session_state.selected_pokemon_name:
    show_details_view()

# otherwise, show the menu
else:
    # Cleaner Menu at the top
    selected_page = option_menu(
        menu_title=None,
        options=["Search", "Analytics"],
        icons=["search", "bar-chart-fill"],
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#f0f2f6"},
            "nav-link": {"font-size": "14px", "text-align": "center", "margin": "0px"},
            "nav-link-selected": {"background-color": "#ff4b4b", "color": "white"},
        }
    )

    if selected_page == "Search":
        show_search_dashboard()
    elif selected_page == "Analytics":
        show_analytics_view()
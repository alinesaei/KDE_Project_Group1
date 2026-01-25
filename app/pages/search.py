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
        execute_custom_sparql,
        get_multiple_pokemon_details,
        get_graph_stats,
        get_attribute_correlations,
        get_filter_options
    )
    from utils.NLtoQuery import extract_ontology_terms, generate_sparql

    NLP_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ System Error: {e}")
    NLP_AVAILABLE = False

st.set_page_config(page_title="Search Engine", page_icon="🔍", layout="wide")

# --- STATE MANAGEMENT
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

    # manual filters
    with tab_manual:
        col_filters, col_results = st.columns([1, 3], gap="large")

        with col_filters:
            st.subheader("Filters")
            with st.form("manual_filter_form"):

                # 1. Anatomy Filter (Reasoning)
                if "ont_opts" not in st.session_state or not st.session_state.ont_opts:
                    st.session_state.ont_opts = get_ontology_options()

                st.markdown("**🧬 Anatomy**")
                st.caption("E.g., 'Head' finds 'Mouth'")
                sel_part = st.selectbox("Body Part", ["Any"] + st.session_state.ont_opts)

                st.divider()

                # elemental Type Filter
                if "type_opts" not in st.session_state:
                    st.session_state.type_opts = get_filter_options("Type")

                st.markdown("**🔥 Elemental Type**")
                sel_type = st.selectbox("Type", ["Any"] + st.session_state.type_opts)

                # Habitat Filter
                if "hab_opts" not in st.session_state:
                    st.session_state.hab_opts = get_filter_options("Habitat")

                st.markdown("**🌲 Habitat**")
                sel_hab = st.selectbox("Habitat", ["Any"] + st.session_state.hab_opts)

                st.divider()

                # Color Filter
                st.markdown("**🎨 Appearance**")
                sel_color = st.selectbox("Color",
                                         ["Any", "Red", "Blue", "Green", "Yellow", "Purple", "Brown", "Pink", "Black",
                                          "White"])

                submitted = st.form_submit_button("🚀 Apply Filters", type="primary")

        with col_results:
            # Fetch Data (Passes all 4 filters now)
            df = get_gen1_data(
                body_part=sel_part,
                color=sel_color,
                poke_type=sel_type,
                habitat=sel_hab
            )
            render_results_grid(df, key_suffix="manual")

    # ai ab
    with tab_ai:
        st.markdown("#### 🧠 Ask the Ontology")

        col_input, col_debug = st.columns([3, 1])
        with col_input:
            with st.form("ai_search_form"):
                user_query = st.text_input("Describe your Pokemon:",
                                           placeholder="Example: I want a Fire dragon that lives in mountains...")
                run_ai = st.form_submit_button("✨ Generate SPARQL & Search")

        if run_ai and user_query:
            if not NLP_AVAILABLE:
                st.error("NLP Module not loaded.")
            else:
                with st.spinner("Analyzing semantics..."):
                    # Reset previous results
                    st.session_state.ai_search_df = None

                    # Extract Terms
                    uris, logs = extract_ontology_terms(user_query)

                    # Debug Info
                    with col_debug:
                        with st.expander("🤖 Logic Trace", expanded=False):
                            for log in logs:
                                st.text(f"• {log}")
                            if not uris:
                                st.warning("No ontology terms matched.")

                    if uris:
                        sparql_query = generate_sparql(uris)
                        # Execute & SAVE to Session State
                        results = execute_custom_sparql(sparql_query)
                        st.session_state.ai_search_df = results

                        # Show Query
                        with st.expander("View Generated SPARQL Code"):
                            st.code(sparql_query, language="sparql")
                    else:
                        st.warning("I couldn't understand the features in your request.")

        # Render results from State
        if st.session_state.ai_search_df is not None:
            st.divider()
            render_results_grid(st.session_state.ai_search_df, key_suffix="ai")


def show_details_view():
    name = st.session_state.selected_pokemon_name
    poke = get_pokemon_details(name)  # Fetch real details

    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("⬅️ Back to Search"):
            st.session_state.selected_pokemon_name = None
            st.rerun()
    with col_title:
        st.subheader(f"Analyzing: {name}")

    st.divider()

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

        st.divider()
        st.markdown("⚔️ **Top Moves**")
        if poke.get('moves'):
            # bullet list or tags
            st.write(", ".join(poke['moves']))
        else:
            st.caption("No move data available.")

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
    st.markdown("Structural relationships of the Generation 1 dataset.")

    # key metrics
    stats = get_graph_stats()
    kpi1, kpi2, kpi3 = st.columns(3)

    with kpi1:
        st.metric(label="Total Species", value=stats['pokemon'], delta="Gen 1")
    with kpi2:
        st.metric(label="Anatomical Parts", value=stats['attributes'], delta="Ontology Classes")
    with kpi3:
        st.metric(label="Total Connections", value=stats['triples'], delta="RDF Triples")

    st.divider()

    col1, col2 = st.columns(2)

    #ONTOLOGY STRUCTURE
    with col1:
        st.subheader("🧬 Anatomy Hierarchy")
        st.caption("How body parts are organized (T-Box).")
        df_ont = get_ontology_hierarchy()
        if not df_ont.empty:
            df_ont.loc[len(df_ont)] = ["Body", "MainBody"]
            # Using a consistent color scheme
            fig = px.sunburst(
                df_ont,
                names='child',
                parents='parent',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No ontology data found.")

    #FEATURE DISTRIBUTION
    with col2:
        st.subheader("📈 Common Features")
        st.caption("Which attributes appear most frequently?")
        df_counts = get_feature_counts()
        if not df_counts.empty:
            fig2 = px.bar(
                df_counts.head(15),  # Limit to top 15 to keep it clean
                x='count',
                y='feature',
                orientation='h',
                color='count',
                color_continuous_scale='Bluered'
            )
            fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No data found.")

    st.divider()

    # correlation heatmap
    st.subheader("🔗 Attribute Correlations")
    st.caption("If a Pokemon has **Attribute A**, does it also have **Attribute B**?")

    df_corr = get_attribute_correlations()
    if not df_corr.empty:
        # Pivot the data for the heatmap
        heatmap_data = df_corr.pivot(index="Attribute A", columns="Attribute B", values="Co-occurrence")

        fig3 = px.imshow(
            heatmap_data,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="Viridis",
            origin='lower'
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Not enough data to calculate correlations.")
# RESULT GRID RENDERER
def render_results_grid(df, key_suffix="default"):

    if df.empty:
        st.info("No Pokemon found matching these criteria.")
        return

    st.success(f"Found {len(df['name'].unique())} Pokemon")

    cols = st.columns(5)
    grouped = df.groupby("name")

    for i, (name, group) in enumerate(grouped):
        first = group.iloc[0]

        with cols[i % 5]:

            with st.container(border=True):

                st.image(first['img'], use_container_width=True)

                st.markdown(f"##### **{name}**")

                badges = []
                if 'color' in first and first['color'] != "Unknown":
                    badges.append(f"🎨 {first['color']}")
                if 'type' in first and first['type']:
                    badges.append(f"🔥 {first['type']}")

                if badges:
                    st.caption(" • ".join(badges))
                else:
                    st.caption("No details")


                unique_key = f"btn_{name}_{key_suffix}"
                if st.button("Details", key=unique_key, use_container_width=True):
                    st.session_state.selected_pokemon_name = name
                    st.rerun()


# view for COMPARISON PAGE
def show_comparison_view():
    st.title("⚖️ Compare Pokémon")
    st.markdown("Select two Pokémon to see their anatomical differences side-by-side.")

    #  Get List of all Pokemon for the dropdown
    # (We can fetch this efficiently via SPARQL)
    if "all_pokemon_names" not in st.session_state:
        # Quick query to get all names
        df_all = get_gen1_data()
        st.session_state.all_pokemon_names = sorted(df_all['name'].unique().tolist())

    # selectioon inputs
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        p1 = st.selectbox("Select Pokémon A", st.session_state.all_pokemon_names, index=0)
    with col_sel2:
        # Default to a different one if possible
        default_idx = 1 if len(st.session_state.all_pokemon_names) > 1 else 0
        p2 = st.selectbox("Select Pokémon B", st.session_state.all_pokemon_names, index=default_idx)

    if st.button("⚔️ Compare", type="primary"):
        if p1 == p2:
            st.warning("Please select two different Pokémon.")
        else:
            # Fetch Data
            data = get_multiple_pokemon_details([p1, p2])
            d1, d2 = data[0], data[1]

            # visual comparison
            col_a, col_mid, col_b = st.columns([2, 1, 2])

            # Left: Pokemon A
            with col_a:
                st.image(d1['img'], width=200)
                st.subheader(d1['name'])
                st.caption(f"Unique Attributes:")
                # Calculate Unique Attributes
                unique_a = set(d1['features']) - set(d2['features'])
                for f in unique_a:
                    st.markdown(f"✅ **{f}**")

            # Middle: Shared
            with col_mid:
                st.markdown("<h3 style='text-align: center;'>🆚</h3>", unsafe_allow_html=True)
                st.markdown("**Shared Attributes:**")
                shared = set(d1['features']) & set(d2['features'])
                if shared:
                    for f in shared:
                        st.markdown(f"🔗 `{f}`")
                else:
                    st.write("No anatomical similarities.")

            # Right: Pokemon B
            with col_b:
                st.image(d2['img'], width=200)
                st.subheader(d2['name'])
                st.caption(f"Unique Attributes:")
                unique_b = set(d2['features']) - set(d1['features'])
                for f in unique_b:
                    st.markdown(f"✅ **{f}**")

            # radar chart overlay
            st.divider()
            st.subheader("📊 Stat Comparison")

            # Prepare Data for Plotly
            df_stats = pd.DataFrame({
                'Stat': list(d1['stats'].keys()),
                d1['name']: list(d1['stats'].values()),
                d2['name']: list(d2['stats'].values())
            })

            # Melt for plotly
            df_melt = df_stats.melt(id_vars=['Stat'], var_name='Pokemon', value_name='Value')

            fig = px.line_polar(df_melt, r='Value', theta='Stat', color='Pokemon', line_close=True)
            fig.update_traces(fill='toself')
            st.plotly_chart(fig, use_container_width=True)

if st.session_state.selected_pokemon_name:
    show_details_view()

else:
    selected_page = option_menu(
        menu_title=None,
        options=["Search", "Analytics", "Compare"],
        icons=["search", "bar-chart-fill", "arrow-left-right"],
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#f0f2f6"},
            "nav-link": {"font-size": "14px", "text-align": "center", "margin": "0px"},
            "nav-link-selected": {"background-color": "#ff4b4b", "color": "white"},
        }
    )

    if selected_page == "Search":
        show_search_dashboard()
    elif selected_page == "Compare":
        show_comparison_view()
    elif selected_page == "Analytics":
        show_analytics_view()
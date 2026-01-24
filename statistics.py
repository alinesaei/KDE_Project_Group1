import rdflib
import numpy as np

BASE = "http://example.org/pokemon-ontology#"

PREFIXES = f"""
PREFIX :    <{BASE}>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
"""

# -------------------------
# Helper functions
# -------------------------

def load_graph(data_file=None):
    g = rdflib.Graph()
    g.parse("ontology/pokemon_anatomy.ttl", format="ttl")
    if data_file:
        g.parse(data_file, format="ttl")
    return g

def count_query(g, query):
    res = list(g.query(query))
    return int(res[0]["count"]) if res else 0

# ------------------------------
# Overall dataset statistics
# ------------------------------

g = load_graph("data/pokemon_visualization.ttl")

print("\n--- Overall dataset statistics ---")

num_pokemon = count_query(g, PREFIXES + """
SELECT (COUNT(DISTINCT ?s) AS ?count)
WHERE {
    { ?s :hasAttribute ?o }
    UNION
    { ?s :hasColour ?c }
}
""")

num_classes = count_query(g, PREFIXES + """
SELECT (COUNT(DISTINCT ?c) AS ?count)
WHERE {
    { ?c a owl:Class }
    UNION { ?x :structuralPartOf ?c }
    UNION { ?c :structuralPartOf ?y }
}
""")

num_properties = count_query(g, PREFIXES + """
SELECT (COUNT(DISTINCT ?p) AS ?count)
WHERE {
    ?s ?p ?o .
    FILTER(?p != rdf:type)
}
""")

stored_colours = count_query(g, PREFIXES + """
SELECT (COUNT(*) AS ?count)
WHERE { ?s :hasColour ?c }
""")

stored_attributes = count_query(g, PREFIXES + """
SELECT (COUNT(*) AS ?count)
WHERE { ?s :hasAttribute ?o }
""")

inferred_attributes = count_query(g, PREFIXES + """
SELECT (COUNT(*) AS ?count)
WHERE {
    ?p :hasAttribute ?part .
    ?part :structuralPartOf+ ?parent .
}
""")

total_attributes = stored_attributes + inferred_attributes
inference_ratio = (inferred_attributes / total_attributes * 100) if total_attributes else 0
total_triples = stored_attributes + stored_colours + inferred_attributes

print(f"Triples in graph:               {len(g)}")
print(f"Pokemon:                        {num_pokemon}")
print(f"Body-part classes:              {num_classes}")
print(f"Properties used:                {num_properties}")
print(f"Colours:                        {stored_colours}")
print(f"Explicit attributes:            {stored_attributes}")
print(f"Inferred attributes:            {inferred_attributes}")
print(f"Total attributes:               {total_attributes}")
print(f"Inference ratio:                {inference_ratio:.2f}%")
print(f"Total characteristic triples:   {total_triples}")

# -------------------------
# Statistics per experiment group
# -------------------------

def measure_dataset(file, label):
    g = load_graph(file)

    pokemon = set(g.subjects(rdflib.URIRef(BASE + "hasAttribute"), None))
    n = len(pokemon)

    if n == 0:
        print(f"\n--- {label} ---\nNo Pokémon found.")
        return

    stored, total = [], []

    for p in pokemon:
        stored.append(count_query(g, PREFIXES + f"""
        SELECT (COUNT(?a) AS ?count)
        WHERE {{ <{p}> :hasAttribute ?a }}
        """))

        total.append(count_query(g, PREFIXES + f"""
        SELECT (COUNT(DISTINCT ?x) AS ?count)
        WHERE {{
            <{p}> :hasAttribute ?c .
            ?c :structuralPartOf* ?x .
        }}
        """))

    avg_stored = np.mean(stored)
    avg_total = np.mean(total)
    inference_ratio = (1 - avg_stored / avg_total) * 100 if avg_total else 0

    print(f"\n--- {label} ---")
    print(f"Pokémon:                        {n}")
    print(f"Average stored attributes:      {avg_stored:.2f}")
    print(f"Average total attributes:       {avg_total:.2f}")
    print(f"Inference ratio:                {inference_ratio:.1f}%")


print("\n--- Statistics per experiment group ---")

measure_dataset(
    "data/pokemon_visualization_first_half.ttl",
    "Group A (Pokémon 001 – 076)"
)

measure_dataset(
    "data/pokemon_visualization_second_half.ttl",
    "Group B (Pokémon 077 – 151)"
)

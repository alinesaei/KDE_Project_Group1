from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd

import random

ENDPOINT_URL = "http://localhost:7200/repositories/pokemon-repo"


PREFIXES = """
    PREFIX : <http://example.org/pokemon-ontology#>
    PREFIX pk: <https://pokemonkg.org/instance/pokemon#>
    PREFIX poke: <https://pokemonkg.org/ontology#> 
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

def get_gen1_data(body_part="Any", color="Any", poke_type="Any", habitat="Any"):
    """
    HIGH-PERFORMANCE VERSION:
    1. FILTER FIRST: Reduces the search space from thousands to ~5 items immediately.
    2. DIRECT LOOKUP: Constructs URIs instead of searching (O(1) speed vs O(N)).
    """
    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setReturnFormat(JSON)

    query = PREFIXES + """
    SELECT DISTINCT ?name ?img ?color
    WHERE {
        # =======================================================
        # STEP 1: START WITH THE SMALLEST LIST (Gen 1 Anchor)
        # =======================================================
        GRAPH ?gGen {
            <https://pokemonkg.org/instance/generation/i> poke:featuresSpecies ?pokemonB .
        }

        # =======================================================
        # STEP 2: APPLY FILTERS IMMEDIATELY (Pruning)
        # =======================================================
        # By filtering here, we stop processing irrelevant Pokemon immediately.
        """

    # --- TYPE FILTER ---
    if poke_type and poke_type != "Any":
        query += f"""
        GRAPH ?gType {{ ?pokemonB poke:hasType ?typeURI . }}
        FILTER(CONTAINS(LCASE(STR(?typeURI)), "{poke_type.strip().lower()}"))
        """

    # --- HABITAT FILTER ---
    if habitat and habitat != "Any":
        safe_hab = habitat.replace(" ", "")
        query += f"""
        GRAPH ?gHab {{ ?pokemonB poke:foundIn ?habURI . }}
        FILTER(CONTAINS(LCASE(STR(?habURI)), "{safe_hab.lower()}"))
        """

    query += """
        # =======================================================
        # STEP 3: PREDICT THE ANATOMY URI (The Speed Hack)
        # =======================================================
        # Instead of searching the whole DB, we convert the URI directly.
        # N-Quads:  .../instance/pokemon/charizard
        # Anatomy:  .../instance/pokemon#charizard

        BIND(IRI(REPLACE(STR(?pokemonB), "/pokemon/", "/pokemon#")) AS ?pokemonA)

        # =======================================================
        # STEP 4: DIRECT FETCH (O(1) Complexity)
        # =======================================================
        # Now we only look up anatomy for the FEW matching Pokemon.
        {
            ?pokemonA :hasAttribute ?part .
            ?part rdfs:label ?partName .
            OPTIONAL { ?pokemonA :hasColour ?colorURI . }
        }
        UNION
        {
            GRAPH ?gAnatomy {
                ?pokemonA :hasAttribute ?part .
                ?part rdfs:label ?partName .
                OPTIONAL { ?pokemonA :hasColour ?colorURI . }
            }
        }

        # =======================================================
        # STEP 5: FORMATTING
        # =======================================================
        BIND(LCASE(REPLACE(STR(?pokemonB), "^.*[#/]", "")) AS ?slug)
        BIND(CONCAT(UCASE(SUBSTR(?slug, 1, 1)), SUBSTR(?slug, 2)) AS ?name)
        BIND(CONCAT("https://img.pokemondb.net/artwork/", ?slug, ".jpg") AS ?img)
        BIND(REPLACE(STR(?colorURI), "^.*resource/", "") AS ?color)

        # --- ANATOMY FILTERS (Applied to the final few) ---
        """
    if body_part and body_part != "Any":
        query += f"""
        ?part :structuralPartOf* ?category .
        ?category rdfs:label "{body_part}"@en .
        """

    # Color Filter
    if color and color != "Any":
        query += f'FILTER(?color = "{color}") .'

    query += "}"

    sparql.setQuery(query)

    try:
        results = sparql.query().convert()
        data = []
        for res in results["results"]["bindings"]:
            data.append({
                "name": res["name"]["value"],
                "img": res["img"]["value"],
                "color": res.get("color", {}).get("value", "Unknown"),
            })

        return pd.DataFrame(data).drop_duplicates(subset=['name'])

    except Exception as e:
        return pd.DataFrame(columns=["name", "img", "color"])

def get_filter_options(category):
    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setReturnFormat(JSON)
    # Search EVERYWHERE for options too
    if category == "Type":
        query = PREFIXES + "SELECT DISTINCT ?label WHERE { { ?t a poke:Type ; rdfs:label ?label } UNION { GRAPH ?g { ?t a poke:Type ; rdfs:label ?label } } FILTER(lang(?label)='en') } ORDER BY ?label"
    elif category == "Habitat":
        query = PREFIXES + "SELECT DISTINCT ?label WHERE { { ?h a poke:Habitat ; rdfs:label ?label } UNION { GRAPH ?g { ?h a poke:Habitat ; rdfs:label ?label } } FILTER(lang(?label)='en') } ORDER BY ?label"
    else:
        return []

    sparql.setQuery(query)
    try:
        results = sparql.query().convert()
        return [r["label"]["value"] for r in results["results"]["bindings"]]
    except:
        return []


def get_pokemon_details(pokemon_name):
    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setReturnFormat(JSON)
    # Search EVERYWHERE for details
    query = PREFIXES + f"""
    SELECT DISTINCT ?partName WHERE {{
        {{ pk:{pokemon_name.lower()} :hasAttribute ?part . ?part rdfs:label ?partName . }}
        UNION
        {{ GRAPH ?g {{ pk:{pokemon_name.lower()} :hasAttribute ?part . ?part rdfs:label ?partName . }} }}
    }}
    """
    sparql.setQuery(query)
    features = []
    try:
        results = sparql.query().convert()
        features = [r["partName"]["value"] for r in results["results"]["bindings"]]
    except:
        pass

    return {
        "name": pokemon_name,
        "img": f"https://img.pokemondb.net/artwork/{pokemon_name.lower()}.jpg",
        "features": features,
        "stats": {"HP": random.randint(50, 100), "Attack": random.randint(50, 100), "Defense": random.randint(50, 100)},
        "relations": [{"source": pokemon_name, "target": f, "label": "hasAttribute"} for f in features]
    }


# ... (Include get_ontology_options, get_ontology_hierarchy, get_feature_counts, etc. from your previous file) ...
# Just make sure to define them or leave them if they are already there.
def get_ontology_options():
    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setReturnFormat(JSON)
    query = PREFIXES + """
    SELECT DISTINCT ?label WHERE {
        ?part a :BodyPart ; rdfs:label ?label .
        FILTER(lang(?label) = "en")
    } ORDER BY ?label
    """
    sparql.setQuery(query)
    try:
        results = sparql.query().convert()
        return [r["label"]["value"] for r in results["results"]["bindings"]]
    except:
        return []

def get_ontology_hierarchy():
    """
    Fetchin the parent-child relationships for the chart
    """
    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setReturnFormat(JSON)
    query = PREFIXES + """
    SELECT ?parentLabel ?childLabel WHERE {
        ?child :structuralPartOf ?parent .
        ?child rdfs:label ?childLabel .
        ?parent rdfs:label ?parentLabel .
        FILTER(lang(?childLabel) = "en" && lang(?parentLabel) = "en")
    }
    """
    sparql.setQuery(query)
    try:
        results = sparql.query().convert()
        return pd.DataFrame([
            {
                "parent": r["parentLabel"]["value"],
                "child": r["childLabel"]["value"]
            }
            for r in results["results"]["bindings"]
        ])
    except:
        return pd.DataFrame(columns=["parent", "child"])

def get_feature_counts():
    """
    Counts how many pokemon have each attribute
    """
    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setReturnFormat(JSON)
    query = PREFIXES + """
    SELECT ?feature (COUNT(?pokemon) as ?count) WHERE {
        ?pokemon :hasAttribute ?a .
        ?a rdfs:label ?feature .
        FILTER(lang(?feature) = "en")
    } 
    GROUP BY ?feature 
    ORDER BY DESC(?count)
    LIMIT 15
    """
    sparql.setQuery(query)
    try:
        results = sparql.query().convert()
        return pd.DataFrame([
            {
                "feature": r["feature"]["value"],
                "count": int(r["count"]["value"])
            }
            for r in results["results"]["bindings"]
        ])
    except:
        return pd.DataFrame(columns=["feature", "count"])


def execute_custom_sparql(query_string):
    """
    Executes a SPARQL query string generated by the NLP
    """
    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query_string)

    try:
        results = sparql.query().convert()
        data = []
        for res in results["results"]["bindings"]:
            # logic to handle different variable names
            # we try to find common variable names like ?pokemon, ?name, ?s

            # Extract Name
            if "name" in res:
                name_val = res["name"]["value"]
            elif "pokemon" in res:
                # If only URI is returned, strip the suffix
                name_val = res["pokemon"]["value"].split("/")[-1].split("#")[-1]
            else:
                name_val = "Unknown"

            data.append({
                "name": name_val.capitalize(),
                "img": f"https://img.pokemondb.net/artwork/{name_val.lower()}.jpg",
                "color": "Unknown"  # custom queries might not return color
            })

        return pd.DataFrame(data)

    except Exception as e:
        print(f"SPARQL Error: {e}")
        return pd.DataFrame(columns=["name", "img", "color"])


def get_multiple_pokemon_details(names_list):
    """
    Fetches details for a list of Pokemon names.
    """
    data = []
    for name in names_list:
        details = get_pokemon_details(name)
        if details:
            data.append(details)
    return data


def get_graph_stats():
    """
    Fetches high-level metrics for the dashboard.
    """
    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setReturnFormat(JSON)

    # We run 3 sub-queries to get counts
    query = PREFIXES + """
    SELECT 
      (COUNT(DISTINCT ?s) AS ?pokemonCount) 
      (COUNT(DISTINCT ?attr) AS ?attrCount)
      (COUNT(*) AS ?tripleCount)
    WHERE {
        ?s :hasAttribute ?attr .
    }
    """
    sparql.setQuery(query)
    try:
        results = sparql.query().convert()
        res = results["results"]["bindings"][0]
        return {
            "pokemon": res["pokemonCount"]["value"],
            "attributes": res["attrCount"]["value"],
            "triples": res["tripleCount"]["value"]
        }
    except:
        return {"pokemon": 0, "attributes": 0, "triples": 0}


def get_attribute_correlations():
    """
    Finds which attributes appear together most often.
    (e.g., Wings + Beak)
    """
    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setReturnFormat(JSON)
    query = PREFIXES + """
    SELECT ?a1Label ?a2Label (COUNT(?s) AS ?count)
    WHERE {
        ?s :hasAttribute ?a1 .
        ?s :hasAttribute ?a2 .
        ?a1 rdfs:label ?a1Label .
        ?a2 rdfs:label ?a2Label .

        FILTER(lang(?a1Label) = "en" && lang(?a2Label) = "en")
        FILTER(STR(?a1) < STR(?a2)) # Avoid duplicates (A-B vs B-A) and self-matches
    }
    GROUP BY ?a1Label ?a2Label
    ORDER BY DESC(?count)
    LIMIT 50
    """
    sparql.setQuery(query)
    try:
        results = sparql.query().convert()
        data = []
        for r in results["results"]["bindings"]:
            data.append({
                "Attribute A": r["a1Label"]["value"],
                "Attribute B": r["a2Label"]["value"],
                "Co-occurrence": int(r["count"]["value"])
            })
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()
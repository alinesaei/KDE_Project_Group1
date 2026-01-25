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
    1. FILTER FIRST
    2. DIRECT lookup: Constructs URIs instead of searching (O(1) speed vs O(N))
    """
    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setReturnFormat(JSON)

    query = PREFIXES + """
    SELECT DISTINCT ?name ?img ?color
    WHERE {
        # start with gen 1 list
        GRAPH ?gGen {
            <https://pokemonkg.org/instance/generation/i> poke:featuresSpecies ?pokemonB .
        }

        # apply filters immediatly (pruning)
        # By filtering here, we stop processing irrelevant Pokemon immediately
        """

    # type filter
    if poke_type and poke_type != "Any":
        query += f"""
        GRAPH ?gType {{ ?pokemonB poke:hasType ?typeURI . }}
        FILTER(CONTAINS(LCASE(STR(?typeURI)), "{poke_type.strip().lower()}"))
        """

    # habitat filter
    if habitat and habitat != "Any":
        safe_hab = habitat.replace(" ", "")
        query += f"""
        GRAPH ?gHab {{ ?pokemonB poke:foundIn ?habURI . }}
        FILTER(CONTAINS(LCASE(STR(?habURI)), "{safe_hab.lower()}"))
        """

    query += """
        # Instead of searching the whole DB, we convert the URI directly
        # N-Quads:  .../instance/pokemon/charizard
        # Anatomy:  .../instance/pokemon#charizard

        BIND(IRI(REPLACE(STR(?pokemonB), "/pokemon/", "/pokemon#")) AS ?pokemonA)

        # Now we only look up anatomy for the few matching Pokemo
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

        # formatting
        BIND(LCASE(REPLACE(STR(?pokemonB), "^.*[#/]", "")) AS ?slug)
        BIND(CONCAT(UCASE(SUBSTR(?slug, 1, 1)), SUBSTR(?slug, 2)) AS ?name)
        BIND(CONCAT("https://img.pokemondb.net/artwork/", ?slug, ".jpg") AS ?img)
        BIND(REPLACE(STR(?colorURI), "^.*resource/", "") AS ?color)

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
    """
    Fetches details + MOVES.
    ROBUST FIX: Handles 'Chain' relationships (Pokemon -> LearningNode -> Move).
    """
    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setReturnFormat(JSON)

    # 1. ANATOMY (Standard Universal Search)
    query_anatomy = PREFIXES + f"""
    SELECT DISTINCT ?partName WHERE {{
        {{ pk:{pokemon_name.lower()} :hasAttribute ?part . ?part rdfs:label ?partName . }}
        UNION
        {{ GRAPH ?g {{ pk:{pokemon_name.lower()} :hasAttribute ?part . ?part rdfs:label ?partName . }} }}
    }}
    """
    sparql.setQuery(query_anatomy)
    features = []
    try:
        results = sparql.query().convert()
        features = [r["partName"]["value"] for r in results["results"]["bindings"]]
    except:
        pass

    # 2. MOVES (The Chain Search)
    query_moves = PREFIXES + f"""
    SELECT DISTINCT ?cleanName WHERE {{
        GRAPH ?g {{
            # We look for the move URI at the end of a chain
            {{
                # PATTERN A: Direct Link (Pokemon -> Move)
                ?pokemon poke:learnsMove ?moveURI .
            }}
            UNION
            {{
                # PATTERN B: Indirect Chain (Pokemon -> LearningNode -> Move)
                # This matches the structure in your screenshot!
                ?pokemon ?link ?intermediateNode .
                ?intermediateNode poke:learnsMove ?moveURI .
            }}

            # 1. Match the Pokemon Name (Fuzzy Match on the START of the chain)
            # This finds ".../charizard" regardless of prefix
            FILTER(CONTAINS(LCASE(STR(?pokemon)), "/{pokemon_name.lower()}"))

            # 2. Get the Move Name
            OPTIONAL {{ ?moveURI rdfs:label ?label . FILTER(lang(?label) = "en") }}
            BIND(REPLACE(STR(?moveURI), "^.*move/", "") AS ?slug)
            BIND(COALESCE(?label, ?slug) AS ?rawName)

            # 3. Clean formatting
            BIND(CONCAT(UCASE(SUBSTR(?rawName, 1, 1)), SUBSTR(?rawName, 2)) AS ?cleanName)
        }}
    }} LIMIT 25
    """
    sparql.setQuery(query_moves)
    moves = []
    try:
        results = sparql.query().convert()
        moves = [r["cleanName"]["value"] for r in results["results"]["bindings"]]
    except:
        pass

    return {
        "name": pokemon_name,
        "img": f"https://img.pokemondb.net/artwork/{pokemon_name.lower()}.jpg",
        "features": features,
        "moves": moves,  # <--- List of moves
        "stats": {"HP": random.randint(50, 100), "Attack": random.randint(50, 100), "Defense": random.randint(50, 100)},
        "relations": [{"source": pokemon_name, "target": f, "label": "hasAttribute"} for f in features]
    }

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
                "color": "Unknown"
            })

        return pd.DataFrame(data)

    except Exception as e:
        print(f"SPARQL Error: {e}")
        return pd.DataFrame(columns=["name", "img", "color"])


def get_multiple_pokemon_details(names_list):
    """
    Fetch details for a list of Pokemon names
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
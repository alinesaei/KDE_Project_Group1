from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import random

ENDPOINT_URL = "http://localhost:7200/repositories/pokemon-repo"

PREFIXES = """
    PREFIX : <http://example.org/pokemon-ontology#>
    PREFIX pk: <https://pokemonkg.org/instance/pokemon#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dbr: <http://dbpedia.org/resource/>
"""


def get_gen1_data(body_part="Any", color="Any"):
    """
    Fetches Pokemon list with OPTIONAL filters for Body Part and Color.
    """
    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setReturnFormat(JSON)

    query = PREFIXES + """
    SELECT DISTINCT ?pokemon ?name ?partName ?color
    WHERE {
        ?pokemon :hasAttribute ?part .
        ?part rdfs:label ?partName .

        # Name Processing
        BIND(REPLACE(STR(?pokemon), "^.*#", "") AS ?slug)
        BIND(CONCAT(UCASE(SUBSTR(?slug, 1, 1)), SUBSTR(?slug, 2)) AS ?name)

        # Optional Color
        OPTIONAL { 
            ?pokemon :hasColour ?colorURI . 
            BIND(REPLACE(STR(?colorURI), "^.*resource/", "") AS ?color)
        }
    """

    # FILTER 1: Ontology Reasoning (Transitive)
    if body_part and body_part != "Any":
        query += f"""
        ?part :structuralPartOf* ?category .
        ?category rdfs:label "{body_part}"@en .
        """

    # FILTER 2: Color
    if color and color != "Any":
        query += f"""
        FILTER(?color = "{color}") .
        """

    query += "}"

    sparql.setQuery(query)

    try:
        results = sparql.query().convert()
        data = []
        for res in results["results"]["bindings"]:
            data.append({
                "name": res["name"]["value"],
                "feature": res["partName"]["value"],
                "color": res.get("color", {}).get("value", "Unknown"),
                "img": f"https://img.pokemondb.net/artwork/{res['name']['value'].lower()}.jpg"
            })

        if not data:
            return pd.DataFrame(columns=["name", "feature", "color", "img"])

        return pd.DataFrame(data)

    except Exception as e:
        print(f"GraphDB Error: {e}")
        return pd.DataFrame(columns=["name", "feature", "color", "img"])


def get_pokemon_details(pokemon_name):
    """
    Fetches specific details for ONE Pokemon for the Details View.
    """

    sparql = SPARQLWrapper(ENDPOINT_URL)
    sparql.setReturnFormat(JSON)

    # Query to get ALL attributes for this specific pokemon
    query = PREFIXES + f"""
    SELECT DISTINCT ?partName WHERE {{
        pk:{pokemon_name.lower()} :hasAttribute ?part .
        ?part rdfs:label ?partName .
    }}
    """
    sparql.setQuery(query)
    features = []
    try:
        results = sparql.query().convert()
        features = [r["partName"]["value"] for r in results["results"]["bindings"]]
    except:
        pass

    # Return a dictionary formatted for interface
    return {
        "name": pokemon_name,
        "img": f"https://img.pokemondb.net/artwork/{pokemon_name.lower()}.jpg",
        "features": features,
        "stats": {"HP": random.randint(50, 100), "Attack": random.randint(50, 100), "Defense": random.randint(50, 100)},
        "relations": [
            {"source": pokemon_name, "target": f, "label": "hasAttribute"} for f in features
        ]
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
                "color": "Unknown"  # custom queries might not return color
            })

        return pd.DataFrame(data)

    except Exception as e:
        print(f"SPARQL Error: {e}")
        return pd.DataFrame(columns=["name", "img", "color"])


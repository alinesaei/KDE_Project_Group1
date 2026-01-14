import spacy

# LOAD NLP MODEL
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    print("Downloading model...")
    from spacy.cli import download
    download("en_core_web_md")
    nlp = spacy.load("en_core_web_md")

# ONTOLOGY MAPPING
# Keys = Natural Language Labels (from rdfs:label)
# Values = Exact URI Suffixes from Ontology
ONTOLOGY_MAP = {
    # Main Body Parts
    "main body": "MainBody",
    "head": "Head",
    "body": "Body",
    "flame": "Flame",
    "leaf": "Leaf",
    "vines": "Vines",
    "flower": "Flower",
    "mushroom": "Mushroom",
    "chrysalis": "Chrysalis",
    "hair": "Hair",
    "mane": "Mane",
    "body shell": "BodyShell",
    "body roughness": "BodyRoughness",
    "body symbols": "BodySymbols",
    "item": "Item",
    "gem": "Gem",

    # Head Parts
    "eyes": "Eyes",
    "mouth": "Mouth",
    "nose": "Nose",
    "ears": "Ears",
    "horn": "Horn",
    "whiskers": "Whiskers",
    "antenna": "Antenna",
    "flowing crest": "FlowingCrest",

    # Mouth/Teeth Parts
    "teeth": "Teeth",
    "tongue": "Tongue",
    "beak": "Beak",
    "lips": "Lips",
    "fangs": "Fangs",

    # Limbs and Appendages
    "arms": "Arms",
    "legs": "Legs",
    "tail": "Tail",
    "wings": "Wings",
    "fins": "Fins",
    "flippers": "Flippers",
    "tentacles": "Tentacles",
    "pinsers": "Pinsers",
    "claws": "Claws",
    
    # Specific Parts
    "fingers": "Fingers",
    "feet": "Feet",
    "talons": "Talons",
    "feathers": "Feathers",
    "dragon wings": "DragonWings",
    "bug wings": "BugWings"
}

# Pre-compute vectors for speed
vocab_vectors = {label: nlp(label) for label in ONTOLOGY_MAP.keys()}

def extract_ontology_terms(user_prompt, threshold=0.70):
    """
    Matches user words to your Ontology Labels using vector similarity.
    """
    doc = nlp(user_prompt.lower())
    found_uris = set()
    debug_log = []

    # specific check for multi-word terms
    for label, vector in vocab_vectors.items():
        # Check exact phrase is in prompt
        if label in user_prompt.lower():
            found_uris.add(ONTOLOGY_MAP[label])
            debug_log.append(f"Exact Match: '{label}' -> :{ONTOLOGY_MAP[label]}")
            continue

    # Token-based similarity check for single words
    for token in doc:
        if token.is_stop or token.pos_ not in ["NOUN", "PROPN", "ADJ"]:
            continue
        
        best_score = 0
        best_match_label = None

        for label, vector in vocab_vectors.items():
            # semantic similarity
            score = token.similarity(vector)
            if score > best_score:
                best_score = score
                best_match_label = label

        if best_score > threshold:
            uri = ONTOLOGY_MAP[best_match_label]
            # Avoid duplicates if we already found it via exact match
            if uri not in found_uris:
                found_uris.add(uri)
                debug_log.append(f"Vector Match: '{token.text}' ~ '{best_match_label}' ({best_score:.2f}) -> :{uri}")

    return list(found_uris), debug_log

def generate_sparql(uris):
    if not uris:
        return "No matching attributes found."

    # PREFIXES
    sparql = """
    PREFIX : <http://example.org/pokemon-ontology#>
    PREFIX poke: <https://pokemonkg.org/ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?pokemon ?name
    WHERE {
        ?pokemon a poke:Species ;
                 rdfs:label ?name .
    """
    
    # constraints for every attribute found
    for uri in uris:
        sparql += f"    ?pokemon :hasAttribute :{uri} .\n"

    sparql += "}"
    return sparql

# --- MAIN ---
if __name__ == "__main__":
    # Test 1
    prompt_1 = "I want a pokemon with wings and a tail"
    print(f"\nUser: '{prompt_1}'")
    uris_1, log_1 = extract_ontology_terms(prompt_1)
    print("Debug:", log_1)
    print(generate_sparql(uris_1))

    # Test 2
    prompt_2 = "Show me a dragon with big fangs and claws"
    print(f"\nUser: '{prompt_2}'")
    uris_2, log_2 = extract_ontology_terms(prompt_2)
    print("Debug:", log_2)
    print(generate_sparql(uris_2))

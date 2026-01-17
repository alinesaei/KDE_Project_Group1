import spacy

# LOAD MODEL
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    print("Model not found. Downloading 'en_core_web_md'...")
    from spacy.cli import download
    download("en_core_web_md")
    nlp = spacy.load("en_core_web_md")

# ONTOLOGY MAPPINGS

# BODY PARTS
ONTOLOGY_MAP = {
    # Main Body & Structural
    "main body": "MainBody", "head": "Head", "body": "Body",
    
    # Main Body Attributes
    "flame": "Flame", "leaf": "Leaf", "vines": "Vines", 
    "flower": "Flower", "mushroom": "Mushroom", "chrysalis": "Chrysalis",
    "hair": "Hair", "mane": "Mane", "body shell": "BodyShell", 
    "shell": "BodyShell", "roughness": "BodyRoughness", 
    "body roughness": "BodyRoughness", 
    "body symbols": "BodySymbols", "item": "Item", "gem": "Gem",

    # Head Parts
    "eyes": "Eyes", "mouth": "Mouth", "nose": "Nose", "ears": "Ears",
    "horn": "Horn", "whiskers": "Whiskers", "antenna": "Antenna",
    "crest": "FlowingCrest", "flowing crest": "FlowingCrest",

    # Mouth Parts
    "teeth": "Teeth", "tongue": "Tongue", "beak": "Beak", "lips": "Lips",
    "fangs": "Fangs",

    # Body Parts
    "arms": "Arms", "legs": "Legs", "tail": "Tail", "wings": "Wings",
    "fins": "Fins", "flippers": "Flippers", "tentacles": "Tentacles",
    "pinsers": "Pinsers", "claws": "Claws",

    # Sub-Parts
    "fingers": "Fingers", "feet": "Feet", "talons": "Talons",
    "feathers": "Feathers", "dragon wings": "DragonWings", "bug wings": "BugWings"
}

# COLORS
COLOR_MAP = {
    "red": "Red", "crimson": "Red", "scarlet": "Red",
    "blue": "Blue", "azure": "Blue", "navy": "Blue",
    "green": "Green", "emerald": "Green",
    "yellow": "Yellow", "gold": "Yellow",
    "black": "Black", "dark": "Black",
    "white": "White", "pale": "White",
    "purple": "Purple", "violet": "Purple",
    "pink": "Pink",
    "brown": "Brown",
    "grey": "Grey", "gray": "Grey", "silver": "Grey"
}

# HIERARCHY Child -> Parent
PARENT_MAP = {
    "Fangs": "Teeth", "Talons": "Feet", "Teeth": "Mouth", 
    "Tongue": "Mouth", "Beak": "Mouth", "Lips": "Mouth", 
    "Fingers": "Arms", "Feet": "Legs", "Feathers": "Wings", 
    "DragonWings": "Wings", "BugWings": "Wings",
    "Eyes": "Head", "Mouth": "Head", "Nose": "Head", 
    "Ears": "Head", "Horn": "Head", "Whiskers": "Head", 
    "Antenna": "Head", "FlowingCrest": "Head",
    "Arms": "Body", "Legs": "Body", "Tail": "Body", 
    "Wings": "Body", "Fins": "Body", "Flippers": "Body", 
    "Tentacles": "Body", "Pinsers": "Body", "Claws": "Body",
    "Head": "MainBody", "Body": "MainBody", "Flame": "MainBody", 
    "Leaf": "MainBody", "Vines": "MainBody", "Flower": "MainBody", 
    "Mushroom": "MainBody", "Chrysalis": "MainBody", "Hair": "MainBody", 
    "Mane": "MainBody", "BodyShell": "MainBody", "BodyRoughness": "MainBody", 
    "BodySymbols": "MainBody", "Item": "MainBody", "Gem": "MainBody"
}

# Pre-compute vectors for body parts only
vocab_vectors = {label: nlp(label) for label in ONTOLOGY_MAP.keys()}

# FUNCTIONS

def get_all_ancestors(uri):
    ancestors = set()
    current = uri
    while current in PARENT_MAP:
        parent = PARENT_MAP[current]
        ancestors.add(parent)
        current = parent
    return ancestors

def filter_redundant_parents(found_uris):
    if not found_uris: return []
    final_set = set(found_uris)
    for uri in found_uris:
        ancestors = get_all_ancestors(uri)
        final_set -= ancestors
    return list(final_set)

def extract_entities(user_prompt, threshold=0.70):
    """
    Returns TWO lists: Body Parts URIs and Color URIs.
    """
    doc = nlp(user_prompt.lower())
    found_parts = set()
    found_colors = set()

    # Exact match
    for label, uri in ONTOLOGY_MAP.items():
        if label in user_prompt.lower():
            found_parts.add(uri)

    # Token analysis
    for token in doc:
        if token.text in COLOR_MAP:
            found_colors.add(COLOR_MAP[token.text])
            continue

        # Body parts with vector similarity
        if token.is_stop or token.pos_ not in ["NOUN", "PROPN", "ADJ"]:
            continue
        
        best_score = 0
        best_match_label = None

        for label, vector in vocab_vectors.items():
            score = token.similarity(vector)
            if score > best_score:
                best_score = score
                best_match_label = label

        if best_score > threshold:
            found_parts.add(ONTOLOGY_MAP[best_match_label])

    # Hierarchy Filter
    refined_parts = filter_redundant_parents(list(found_parts))
    
    return refined_parts, list(found_colors)

def nl_to_sparql(user_prompt):
    parts, colors = extract_entities(user_prompt)
    
    if not parts and not colors:
        return None

    # Base Query
    sparql = """
    PREFIX : <http://example.org/pokemon-ontology#>
    PREFIX poke: <https://pokemonkg.org/ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?pokemon ?name
    WHERE {
        ?pokemon a poke:Species ;
                 rdfs:label ?name .
    """
    
    # Body Part
    for part in parts:
        sparql += f"    ?pokemon :hasAttribute :{part} .\n"

    # Color
    for color in colors:
        sparql += f"    ?pokemon :hasColour :{color} .\n"

    sparql += "}"
    return sparql

# TESTING
if __name__ == "__main__":
    # Test: Mixed colors and body parts
    prompt = "I want to find a red beast with dragon wings and green eyes."
    print(f"User: '{prompt}'")
    
    query = nl_to_sparql(prompt)
    
    if query:
        print("\n--- Generated SPARQL ---")
        print(query)
    else:
        print("No matches found.")
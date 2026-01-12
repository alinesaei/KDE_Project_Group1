# app/utils/mock_data.py

def get_mock_pokemon():
    """
    Returns a list of dummy Pokemon data to test the UI
    before the database is ready.
    """
    return [
        {
            "id": 6,
            "name": "Charizard",
            "type": ["Fire", "Flying"],
            "desc": "Spits fire that is hot enough to melt boulders.",
            "features": ["Wings", "Tail", "Flame"],
            "img": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/6.png"
        },
        {
            "id": 12,
            "name": "Butterfree",
            "type": ["Bug", "Flying"],
            "desc": "In battle, it flaps its wings at high speed to release toxic dust.",
            "features": ["Wings", "Antenna", "Compound Eyes"],
            "img": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/12.png"
        },
        {
            "id": 18,
            "name": "Pidgeot",
            "type": ["Normal", "Flying"],
            "desc": "This Pokémon flies at Mach 2 speed, seeking prey.",
            "features": ["Wings", "Beak", "Talons"],
            "img": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/18.png"
        },
        {
            "id": 25,
            "name": "Pikachu",
            "type": ["Electric"],
            "desc": "When several of these Pokémon gather, their electricity can build and cause lightning storms.",
            "features": ["Tail", "Cheek Pouches", "Ears"],
            "img": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png"
        },
    ]


def get_pokemon_by_id(poke_id):
    all_poke = get_mock_pokemon()
    for p in all_poke:
        if p['id'] == poke_id:
            # Add stats for the Radar Chart
            p["stats"] = {
                "HP": 78, "Attack": 84, "Defense": 78,
                "Sp. Atk": 109, "Sp. Def": 85, "Speed": 100
            }
            # Add relationships for the Graph
            p["relations"] = [
                {"source": p['name'], "target": "Fire", "label": "hasType"},
                {"source": p['name'], "target": "Flying", "label": "hasType"},
                {"source": p['name'], "target": "Wings", "label": "hasBodyPart"},
                {"source": p['name'], "target": "Flame", "label": "hasElement"},
                {"source": "Charmeleon", "target": p['name'], "label": "evolvesTo"},
            ]
            return p
    return None
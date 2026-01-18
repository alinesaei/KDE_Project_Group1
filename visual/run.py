from color import PokemonColorDetectorHSV
from query import PokemonQueryEngine
from detection import YOLOPredictor

color = PokemonColorDetectorHSV()
detector = YOLOPredictor("result/yolo/best.pt")
engine = PokemonQueryEngine("data/ontology.ttl", "data/entities.ttl")

ANNOTATION_TO_ONTOLOGY = {
    "Head": "Head",
    "Body": "Body",
    "Main Body" : "MainBody",
    "Arm": "Arms",
    "Finger": "Fingers",
    "Leg": "Legs",
    "Feet": "Feet",
    "Eye": "Eyes",
    "Mouth": "Mouth",
    "Lip": "Lips",
    "Teeth": "Teeth",
    "Fang": "Fangs",
    "Tongue": "Tongue",
    "Ear": "Ears",
    "Tail": "Tail",
    "Horn": "Horn",
    "Leaf": "Leaf",
    "Vine": "Vines",
    "Flower": "Flower",
    "Mushroom": "Mushroom",
    "Flame": "Flame",
    "Flipper": "Flippers",
    "Gem": "Gem",
    "Item": "Item",
    "Body Shell": "BodyShell",
    "Body Roughness": "BodyRoughness",
    "Body Symbol": "BodySymbols",
    "Beak": "Beak",
    "Talon": "Talons",
    "Flowing Crest": "FlowingCrest",
    "Static Crest": "StaticCrest",         
    "Feathered Wing": "Feathers",
    "Antenna": "Antenna",
    "Chrysalis": "Chrysalis",
    "Pinser": "Pinsers",           
    "Bug Wing": "BugWings",
    "Fin": "Fins",
    "Dragon Wing": "DragonWings",
    "Claw": "Claws",
    "Mane": "Mane",
    "Hair": "Hair",
    "Whisker": "Whiskers"
}

def ontologically_known(attributes):
    result = []
    for attr in attributes:
        try:
            attrm = ANNOTATION_TO_ONTOLOGY[attr]
            result.append(attrm)
        except:
            pass
    return result


def get_pokemon_list(path: str, min_color_ratio=0.3, min_detection_conf=0.4):
    colors, _ = color.detect_colors(path, min_ratio=min_color_ratio)
    detections = detector.predict(path, conf=min_detection_conf)
    attributes = set([pred['label'] for pred in detections[0]])
    result = engine.find_with_all(ontologically_known(attributes), colors)
    return result, colors, attributes
    

import os
import sys
from PIL import Image

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from .visual.color import PokemonColorDetectorHSV
    from .visual.detection import YOLOPredictor

    MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "visual/result/yolo/best.pt"))

    if os.path.exists(MODEL_PATH):
        detector = YOLOPredictor(MODEL_PATH)
    else:
        detector = None

    color_engine = PokemonColorDetectorHSV()
    VISION_AVAILABLE = True
except ImportError as e:
    VISION_AVAILABLE = False
    detector = None

# --- EXACT MAPPING FROM run.py ---
ANNOTATION_TO_ONTOLOGY = {
    "Head": "Head", "Body": "Body", "Main Body": "MainBody",
    "Arm": "Arms", "Finger": "Fingers", "Leg": "Legs",
    "Feet": "Feet", "Eye": "Eyes", "Mouth": "Mouth",
    "Lip": "Lips", "Teeth": "Teeth", "Fang": "Fangs",
    "Tongue": "Tongue", "Ear": "Ears", "Tail": "Tail",
    "Horn": "Horn", "Leaf": "Leaf", "Vine": "Vines",
    "Flower": "Flower", "Mushroom": "Mushroom",
    "Flame": "Flame", "Flipper": "Flippers", "Gem": "Gem",
    "Item": "Item", "Body Shell": "BodyShell",
    "Body Roughness": "BodyRoughness", "Body Symbol": "BodySymbols",
    "Beak": "Beak", "Talon": "Talons", "Flowing Crest": "FlowingCrest",
    "Static Crest": "StaticCrest", "Feathered Wing": "Feathers",
    "Antenna": "Antenna", "Chrysalis": "Chrysalis",
    "Pinser": "Pinsers", "Bug Wing": "BugWings", "Fin": "Fins",
    "Dragon Wing": "DragonWings", "Claw": "Claws", "Mane": "Mane",
    "Hair": "Hair", "Whisker": "Whiskers"
}

# Colors that ruin demos because of shadows/outlines
NOISE_COLORS = {"Black", "White", "Gray", "Beige"}


def process_image(image_file):
    if not VISION_AVAILABLE or not detector:
        return [], ["⚠️ System Error: Vision modules not loaded."]

    temp_path = "temp_upload.png"
    try:
        image = Image.open(image_file).convert("RGB")
        image.save(temp_path)
    except Exception as e:
        return [], [f"Error saving image: {e}"]

    detected_terms = set()
    debug_info = []

    # run yolo
    try:
        predictions = detector.predict(temp_path, conf=0.4)
        if predictions and len(predictions) > 0:
            for pred in predictions[0]:
                label = pred['label']
                if label in ANNOTATION_TO_ONTOLOGY:
                    term = ANNOTATION_TO_ONTOLOGY[label]
                    detected_terms.add(term)
                    debug_info.append(f"Found {label} ({pred['confidence']:.2f}) -> {term}")
    except Exception as e:
        debug_info.append(f"YOLO Error: {e}")

    # color drtection
    try:
        colors, _ = color_engine.detect_colors(temp_path, min_ratio=0.25)

        for c in colors:
            if c not in NOISE_COLORS:
                detected_terms.add(c)
                debug_info.append(f"Found Color: {c}")
            else:
                debug_info.append(f"Ignored Noise Color: {c}")

    except Exception as e:
        debug_info.append(f"Color Error: {e}")

    if os.path.exists(temp_path):
        os.remove(temp_path)

    return list(detected_terms), debug_info
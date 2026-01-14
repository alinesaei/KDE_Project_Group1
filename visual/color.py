import numpy as np
from PIL import Image
from colorsys import rgb_to_hsv
from collections import Counter



class PokemonColorDetectorHSV:
    # Hue ranges in degrees
    HUE_RANGES = {
        "Red":     [(350, 360), (0, 15)],
        "Orange":  [(15, 35)],
        "Yellow":  [(35, 65)],
        "Green":   [(65, 160)],
        "Blue":    [(160, 260)],
        "Purple":  [(260, 315)],
        "Pink":    [(315, 350)],
    }

    def __init__(
        self,
        white_thresh=245,
        saturation_thresh=0.18,
        value_black_thresh=0.18
    ):
        self.white_thresh = white_thresh
        self.saturation_thresh = saturation_thresh
        self.value_black_thresh = value_black_thresh

    def _extract_foreground_pixels(self, image_path):
        img = Image.open(image_path).convert("RGBA")
        data = np.array(img)

        r, g, b, a = data[..., 0], data[..., 1], data[..., 2], data[..., 3]

        # Remove transparent & near-white background
        mask = (a > 0) & ~(
            (r > self.white_thresh) &
            (g > self.white_thresh) &
            (b > self.white_thresh)
        )

        return data[mask][:, :3]

    
    def _classify_pixel(self, r, g, b):
        r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
        h, s, v = rgb_to_hsv(r_, g_, b_)
        h_deg = h * 360

        # Very dark → Black
        if v < self.value_black_thresh:
            return "Black"

        # Low saturation → Beige / Gray
        if s < self.saturation_thresh:
            if v > 0.85:
                return "Beige"
            return "Gray"

        # Hue-based color
        for color, ranges in self.HUE_RANGES.items():
            for lo, hi in ranges:
                if lo <= h_deg <= hi:
                    return color

        return "Other"

    def detect_colors(
        self,
        image_path,
        sample_size=5000,
        min_ratio=0.03
    ):
        pixels = self._extract_foreground_pixels(image_path)

        if len(pixels) == 0:
            return set(), Counter()

        # Random sampling for speed
        if len(pixels) > sample_size:
            idx = np.random.choice(len(pixels), sample_size, replace=False)
            pixels = pixels[idx]

        labels = [
            self._classify_pixel(r, g, b)
            for r, g, b in pixels
        ]

        counts = Counter(labels)
        total = sum(counts.values())

        detected = {
            color for color, count in counts.items()
            if count / total >= min_ratio and color != "Other"
        }

        return detected, counts

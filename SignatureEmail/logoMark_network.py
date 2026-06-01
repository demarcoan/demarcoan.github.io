from pathlib import Path
from collections import deque

import numpy as np
from PIL import Image, ImageFilter, ImageDraw


# ============================================================
# PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_LOGO = (BASE_DIR / "../assets/images/logos/definitiva_cerchio_centered.png").resolve()

OUTPUT_DIR = (BASE_DIR / "../assets/images/logos/email_icon").resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SETTINGS
# ============================================================

BLUE = "#253D8B"
CANVAS_SIZE = 1024

# Scegli cosa tenere:
# "network"       = solo rete
# "network_drop"  = rete + goccia
MODE = "network"

# Grandezza del simbolo dentro il cerchio.
# Per icone piccole conviene stare tra 0.62 e 0.78.
CONTENT_SCALE = 0.72

# Spostamento del simbolo dentro il cerchio.
# positivo X = destra, negativo X = sinistra
# positivo Y = giù, negativo Y = su
SHIFT_X_RATIO = 0.00
SHIFT_Y_RATIO = 0.00

# Inspessisce i tratti.
# Per firma email: 3–6.
THICKEN_PIXELS = 4

# Padding interno per non far toccare il disegno al bordo.
SAFE_PADDING_RATIO = 0.18

# Dimensioni esportate
EXPORT_SIZES = [1024]#, 512, 256, 128, 64, 48, 32]

OUTPUT_BASENAME = "logo_mark_network"


# ============================================================
# REGIONI DA TENERE / CANCELLARE
# Coordinate normalizzate rispetto all'immagine originale:
# x1, y1, x2, y2
# ============================================================

# Area della rete/molecola
NETWORK_REGION = (0.61, 0.30, 0.91, 0.72)

# Area della goccia
DROP_REGION = (0.82, 0.68, 0.96, 0.94)

# Area da cancellare: elimina il rettangolo/canale in basso a sinistra
DELETE_REGIONS = [
    (0.00, 0.52, 0.66, 0.78),
]


# ============================================================
# UTILITY
# ============================================================

def normalized_box_to_pixels(box, width, height):
    x1, y1, x2, y2 = box

    return (
        int(x1 * width),
        int(y1 * height),
        int(x2 * width),
        int(y2 * height),
    )


def boxes_intersect(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    return not (
        ax2 < bx1 or
        ax1 > bx2 or
        ay2 < by1 or
        ay1 > by2
    )


def apply_delete_regions(mask):
    """
    Cancella aree indesiderate, per esempio il rettangolo/canale in basso a sinistra.
    """

    width, height = mask.size
    draw = ImageDraw.Draw(mask)

    for region in DELETE_REGIONS:
        x1, y1, x2, y2 = normalized_box_to_pixels(region, width, height)
        draw.rectangle((x1, y1, x2, y2), fill=0)

    return mask


# ============================================================
# MASK
# ============================================================

def make_raw_mask_from_logo(img):
    """
    Converte il logo originale in una maschera:
    blu/scuro = bianco nella maschera
    bianco/chiaro = nero nella maschera
    """

    img = img.convert("RGBA")

    width, height = img.size

    mask = Image.new("L", img.size, 0)

    pixels = img.load()
    mask_pixels = mask.load()

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]

            if a < 20:
                continue

            is_white = r > 225 and g > 225 and b > 225
            is_light = r > 210 and g > 210 and b > 210

            if not is_white and not is_light:
                mask_pixels[x, y] = 255

    return mask


def keep_only_selected_components(mask):
    """
    Tiene solo le componenti che intersecano la regione della rete
    e, se richiesto, la regione della goccia.
    """

    width, height = mask.size

    keep_regions = [NETWORK_REGION]

    if MODE == "network_drop":
        keep_regions.append(DROP_REGION)

    keep_regions_px = [
        normalized_box_to_pixels(region, width, height)
        for region in keep_regions
    ]

    arr = np.array(mask)
    binary = arr > 0

    visited = np.zeros_like(binary, dtype=bool)
    cleaned = np.zeros_like(arr)

    directions = [
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)
    ]

    h, w = binary.shape

    for y0 in range(h):
        for x0 in range(w):

            if not binary[y0, x0] or visited[y0, x0]:
                continue

            queue = deque([(x0, y0)])
            visited[y0, x0] = True

            component_pixels = []

            while queue:
                x, y = queue.popleft()
                component_pixels.append((x, y))

                for dx, dy in directions:
                    xn = x + dx
                    yn = y + dy

                    if 0 <= xn < w and 0 <= yn < h:
                        if binary[yn, xn] and not visited[yn, xn]:
                            visited[yn, xn] = True
                            queue.append((xn, yn))

            xs = [p[0] for p in component_pixels]
            ys = [p[1] for p in component_pixels]

            component_box = (
                min(xs),
                min(ys),
                max(xs),
                max(ys),
            )

            keep_component = any(
                boxes_intersect(component_box, region_box)
                for region_box in keep_regions_px
            )

            if keep_component:
                for x, y in component_pixels:
                    cleaned[y, x] = 255

    return Image.fromarray(cleaned).convert("L")


def crop_to_content(mask):
    bbox = mask.getbbox()

    if bbox is None:
        raise ValueError("Non è stato trovato nessun contenuto nel logo.")

    return bbox


def make_final_symbol_mask(input_path):
    """
    Crea la maschera finale contenente solo rete o rete+goccia.
    """

    img = Image.open(input_path).convert("RGBA")

    mask = make_raw_mask_from_logo(img)

    # Cancella prima le zone indesiderate
    mask = apply_delete_regions(mask)

    # Tiene solo le componenti vicine alla rete/goccia
    mask = keep_only_selected_components(mask)

    # Inspessisce i tratti
    if THICKEN_PIXELS > 0:
        for _ in range(THICKEN_PIXELS):
            mask = mask.filter(ImageFilter.MaxFilter(3))

    return mask


# ============================================================
# ICON GENERATION
# ============================================================

def create_badge_icon(input_path, output_path, size=1024):
    """
    Crea badge blu con simbolo bianco.
    """

    mask = make_final_symbol_mask(input_path)

    bbox = crop_to_content(mask)
    cropped_mask = mask.crop(bbox)

    w, h = cropped_mask.size

    padding = int(max(w, h) * SAFE_PADDING_RATIO)

    square = max(w, h) + 2 * padding

    padded = Image.new("L", (square, square), 0)

    padded.paste(
        cropped_mask,
        (
            (square - w) // 2,
            (square - h) // 2
        )
    )

    content_size = int(size * CONTENT_SCALE)

    content = padded.resize(
        (content_size, content_size),
        Image.Resampling.LANCZOS
    )

    badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    circle = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(circle)

    draw.ellipse(
        (0, 0, size - 1, size - 1),
        fill=BLUE
    )

    badge.alpha_composite(circle)

    white_shape = Image.new(
        "RGBA",
        (content_size, content_size),
        (255, 255, 255, 255)
    )

    white_shape.putalpha(content)

    x = (size - content_size) // 2
    y = (size - content_size) // 2

    x += int(size * SHIFT_X_RATIO)
    y += int(size * SHIFT_Y_RATIO)

    badge.alpha_composite(white_shape, (x, y))

    badge.save(output_path)


def export_resized_versions(master_path):
    master = Image.open(master_path).convert("RGBA")

    for export_size in EXPORT_SIZES:
        out = master.resize(
            (export_size, export_size),
            Image.Resampling.LANCZOS
        )

        output_path = OUTPUT_DIR / f"{OUTPUT_BASENAME}_{MODE}_{export_size}.png"
        out.save(output_path)


def create_all_versions():
    master_path = OUTPUT_DIR / f"{OUTPUT_BASENAME}_{MODE}_{CANVAS_SIZE}.png"

    create_badge_icon(
        input_path=INPUT_LOGO,
        output_path=master_path,
        size=CANVAS_SIZE
    )

    export_resized_versions(master_path)

    print("Done.")
    print(f"Mode: {MODE}")
    print(f"Files saved in: {OUTPUT_DIR}")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    create_all_versions()
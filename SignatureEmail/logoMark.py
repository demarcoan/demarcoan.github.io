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

# Grandezza del disegno bianco dentro il cerchio.
# Se il logo è troppo piccolo: aumenta.
# Se viene tagliato: diminuisci.
CONTENT_SCALE = 1.05

# Padding attorno al disegno prima di inserirlo nel badge.
# Serve per non tagliare goccia, canali, dettagli laterali.
SAFE_PADDING_RATIO = 0.14

# Inspessimento forme.
# Per firma email: 2 o 3 di solito funziona bene.
THICKEN_PIXELS = 3

# Margine esterno ignorato quando si crea la maschera.
# Serve a evitare di prendere il bordo più esterno del vecchio logo.
IGNORE_OUTER_MARGIN_RATIO = 0.07

# Dimensioni esportate.
# Per email userei 64 visualizzato a 32 px.
EXPORT_SIZES = [1024]

# Nome base dei file esportati.
OUTPUT_BASENAME = "logo_mark_email"

SHIFT_X_RATIO = 0.00   # positivo = destra, negativo = sinistra
SHIFT_Y_RATIO = -0.05  # negativo = su, positivo = giù
# ============================================================
# MASK CREATION
# ============================================================

def make_mask_from_logo(img):
    """
    Crea una maschera bianca/nera dal logo originale.

    I pixel blu/scuri diventano bianchi nella maschera.
    I pixel bianchi/chiari vengono ignorati.
    """

    img = img.convert("RGBA")

    mask = Image.new("L", img.size, 0)

    pixels = img.load()
    mask_pixels = mask.load()

    width, height = img.size

    margin = int(min(width, height) * IGNORE_OUTER_MARGIN_RATIO)

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]

            if a < 20:
                continue

            # Ignora la fascia più esterna dell'immagine originale
            if (
                x < margin
                or x > width - margin
                or y < margin
                or y > height - margin
            ):
                continue

            # Sfondo bianco o quasi bianco
            is_white = r > 225 and g > 225 and b > 225

            # Pixel molto chiari: li escludiamo comunque
            is_light = r > 210 and g > 210 and b > 210

            if not is_white and not is_light:
                mask_pixels[x, y] = 255

    # Rimuove archi esterni residui del vecchio bordo circolare
    mask = remove_outer_arc_components(mask)

    # Inspessisce leggermente le forme
    if THICKEN_PIXELS > 0:
        for _ in range(THICKEN_PIXELS):
            mask = mask.filter(ImageFilter.MaxFilter(3))

    return mask


def remove_outer_arc_components(mask):
    """
    Rimuove componenti isolate esterne, come gli archi del vecchio bordo.

    A differenza di un taglio circolare, non cancella tutto ciò che sta
    lontano dal centro. Cerca solo componenti sottili, esterne e isolate.
    """

    arr = np.array(mask)
    binary = arr > 0

    height, width = binary.shape

    visited = np.zeros_like(binary, dtype=bool)
    cleaned = arr.copy()

    cx = width / 2
    cy = height / 2

    # Più basso = rimuove più facilmente cose esterne.
    # Più alto = conserva più dettagli.
    outer_radius = min(width, height) * 0.36

    directions = [
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)
    ]

    for y0 in range(height):
        for x0 in range(width):

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

                    if 0 <= xn < width and 0 <= yn < height:
                        if binary[yn, xn] and not visited[yn, xn]:
                            visited[yn, xn] = True
                            queue.append((xn, yn))

            xs = [p[0] for p in component_pixels]
            ys = [p[1] for p in component_pixels]

            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)

            comp_w = x_max - x_min + 1
            comp_h = y_max - y_min + 1
            comp_area = len(component_pixels)

            bbox_area = comp_w * comp_h
            fill_ratio = comp_area / bbox_area

            distances = [
                ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                for x, y in component_pixels
            ]
            mean_distance = sum(distances) / len(distances)

            # Criteri per riconoscere gli archi:
            # - sono lontani dal centro
            # - sono sottili / poco pieni
            # - non sono micro-rumore
            is_outer = mean_distance > outer_radius
            is_thin = fill_ratio < 0.18
            is_large_enough = comp_area > 200

            if is_outer and is_thin and is_large_enough:
                for x, y in component_pixels:
                    cleaned[y, x] = 0

    return Image.fromarray(cleaned).convert("L")


def crop_to_content(mask):
    """
    Trova la bounding box del contenuto.
    """

    bbox = mask.getbbox()

    if bbox is None:
        raise ValueError("Non è stato trovato nessun contenuto nel logo.")

    return bbox


# ============================================================
# ICON GENERATION
# ============================================================

def create_badge_icon(input_path, output_path, size=1024):
    """
    Crea un badge circolare blu con silhouette bianca del logo.
    """

    img = Image.open(input_path).convert("RGBA")

    mask = make_mask_from_logo(img)

    bbox = crop_to_content(mask)
    cropped_mask = mask.crop(bbox)

    w, h = cropped_mask.size

    # Padding di sicurezza per non tagliare goccia/canali.
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

    # Ridimensiona il contenuto interno
    content_size = int(size * CONTENT_SCALE)
    content = padded.resize(
        (content_size, content_size),
        Image.Resampling.LANCZOS
    )

    # Crea badge trasparente
    badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Cerchio blu
    circle = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(circle)
    draw.ellipse(
        (0, 0, size - 1, size - 1),
        fill=BLUE
    )

    badge.alpha_composite(circle)

    # Silhouette bianca
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
    """
    Esporta il master nelle dimensioni richieste.
    """

    master = Image.open(master_path).convert("RGBA")

    for export_size in EXPORT_SIZES:
        out = master.resize(
            (export_size, export_size),
            Image.Resampling.LANCZOS
        )

        output_path = OUTPUT_DIR / f"{OUTPUT_BASENAME}_{export_size}.png"
        out.save(output_path)


def create_all_versions():
    """
    Crea il master e tutte le versioni ridimensionate.
    """

    master_path = OUTPUT_DIR / f"{OUTPUT_BASENAME}_{CANVAS_SIZE}.png"

    create_badge_icon(
        input_path=INPUT_LOGO,
        output_path=master_path,
        size=CANVAS_SIZE
    )

    export_resized_versions(master_path)

    print("Done.")
    print(f"Files saved in: {OUTPUT_DIR}")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    create_all_versions()
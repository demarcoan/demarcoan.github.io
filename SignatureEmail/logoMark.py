from pathlib import Path
from PIL import Image, ImageDraw


# ============================================================
# PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

NETWORK_PATH = (
    BASE_DIR / "../assets/images/logos/email_icon/network_isolated_white_transparent_4096canvas.png"
).resolve()

DROPLET_PATH = (
    BASE_DIR / "../assets/images/logos/email_icon/droplet_white_2.png"
).resolve()

OUTPUT_DIR = (BASE_DIR / "../assets/images/logos/email_icon").resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SETTINGS
# ============================================================

BLUE = "#253D8B"

CANVAS_SIZE = 1024

EXPORT_SIZES = []

OUTPUT_BASENAME = "logo_mark_network_badge"


# ------------------------------------------------------------
# FORMA DEL BADGE BLU
# ------------------------------------------------------------
# "circle" = cerchio blu
# "pinch" = goccia blu, usando DROPLET_PATH come maschera

BADGE_SHAPE = "pinch"


# ------------------------------------------------------------
# ELEMENTI INTERNI
# ------------------------------------------------------------
# "network" = solo rete
# "droplet" = solo goccia bianca interna
# "both" = rete + goccia bianca interna

ELEMENTS_TO_DRAW = "network"


# ------------------------------------------------------------
# RETE
# ------------------------------------------------------------

CONTENT_SCALE = 0.42

SHIFT_X_RATIO = -0.165     # positivo = destra
SHIFT_Y_RATIO = 0.05     # positivo = giù


# ------------------------------------------------------------
# SAGOMA BLU A GOCCIA
# ------------------------------------------------------------

# Quanto grande deve essere la sagoma blu rispetto al canvas
PINCH_BADGE_SCALE = 1.05

# Spostamento della sagoma blu
PINCH_BADGE_SHIFT_X_RATIO = 0.00
PINCH_BADGE_SHIFT_Y_RATIO = 0.00


# ------------------------------------------------------------
# GOCCIA BIANCA INTERNA
# ------------------------------------------------------------

DROPLET_SCALE = 0.38

DROPLET_SHIFT_X_RATIO = -0.19
DROPLET_SHIFT_Y_RATIO = 0.19


# ============================================================
# FUNCTIONS
# ============================================================

def hex_to_rgba(hex_color, alpha=255):
    """
    Converte colore HEX in RGBA.
    """

    hex_color = hex_color.lstrip("#")

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return (r, g, b, alpha)


def crop_to_content(img):
    """
    Ritaglia l'immagine intorno al contenuto non trasparente.
    """

    img = img.convert("RGBA")
    alpha = img.getchannel("A")

    bbox = alpha.getbbox()

    if bbox is None:
        raise ValueError(
            "L'immagine è vuota o completamente trasparente."
        )

    return img.crop(bbox)


def center_and_fit_to_canvas(img, canvas_size, padding_ratio=0.03):
    """
    Prende l'immagine finale, ritaglia tutto il contenuto non trasparente,
    lo riscalo al massimo spazio disponibile e lo ricentra nella canvas.

    padding_ratio:
    - 0.00 = occupa tutto lo spazio possibile
    - 0.03 = lascia un piccolo margine del 3%
    - 0.06 = lascia più aria intorno
    """

    img = img.convert("RGBA")

    alpha = img.getchannel("A")
    bbox = alpha.getbbox()

    if bbox is None:
        raise ValueError("L'immagine finale è vuota.")

    cropped = img.crop(bbox)

    w, h = cropped.size

    available_size = int(canvas_size * (1 - 2 * padding_ratio))

    scale = min(
        available_size / w,
        available_size / h
    )

    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cropped.resize(
        (new_w, new_h),
        Image.Resampling.LANCZOS
    )

    final_img = Image.new(
        "RGBA",
        (canvas_size, canvas_size),
        (0, 0, 0, 0)
    )

    x = (canvas_size - new_w) // 2
    y = (canvas_size - new_h) // 2

    final_img.alpha_composite(resized, (x, y))

    return final_img

def prepare_icon(img_path, final_size):
    """
    Carica una PNG trasparente, la ritaglia sul contenuto,
    la centra in un quadrato e la ridimensiona.
    """

    img = Image.open(img_path).convert("RGBA")
    img = crop_to_content(img)

    w, h = img.size
    square_size = max(w, h)

    square = Image.new(
        "RGBA",
        (square_size, square_size),
        (0, 0, 0, 0)
    )

    square.paste(
        img,
        (
            (square_size - w) // 2,
            (square_size - h) // 2
        ),
        img
    )

    resized = square.resize(
        (final_size, final_size),
        Image.Resampling.LANCZOS
    )

    return resized


def create_blue_circle(size):
    """
    Crea un cerchio blu con sfondo trasparente.
    """

    antialias_scale = 4
    big_size = size * antialias_scale

    badge = Image.new(
        "RGBA",
        (big_size, big_size),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(badge)

    draw.ellipse(
        (0, 0, big_size - 1, big_size - 1),
        fill=BLUE
    )

    badge = badge.resize(
        (size, size),
        Image.Resampling.LANCZOS
    )

    return badge


def create_blue_shape_from_png(shape_path, size, scale=1.0, shift_x_ratio=0.0, shift_y_ratio=0.0):
    """
    Usa una PNG trasparente come maschera.
    La sagoma viene colorata di blu.

    In pratica:
    - prende l'alpha della goccia bianca
    - lo usa come maschera
    - riempie quella maschera con BLUE
    """

    shape = Image.open(shape_path).convert("RGBA")
    shape = crop_to_content(shape)

    target_size = int(size * scale)

    shape_resized = prepare_icon(
        img_path=shape_path,
        final_size=target_size
    )

    alpha = shape_resized.getchannel("A")

    blue_shape = Image.new(
        "RGBA",
        shape_resized.size,
        hex_to_rgba(BLUE, 255)
    )

    blue_shape.putalpha(alpha)

    badge = Image.new(
        "RGBA",
        (size, size),
        (0, 0, 0, 0)
    )

    x = (size - target_size) // 2
    y = (size - target_size) // 2

    x += int(size * shift_x_ratio)
    y += int(size * shift_y_ratio)

    badge.alpha_composite(blue_shape, (x, y))

    return badge


def create_blue_badge(size, badge_shape="circle"):
    """
    Crea la parte blu del logo.

    badge_shape:
    - "circle"
    - "pinch"
    """

    valid_shapes = ["circle", "pinch"]

    if badge_shape not in valid_shapes:
        raise ValueError(
            f"badge_shape deve essere uno tra: {valid_shapes}"
        )

    if badge_shape == "circle":
        return create_blue_circle(size)

    if badge_shape == "pinch":
        return create_blue_shape_from_png(
            shape_path=DROPLET_PATH,
            size=size,
            scale=PINCH_BADGE_SCALE,
            shift_x_ratio=PINCH_BADGE_SHIFT_X_RATIO,
            shift_y_ratio=PINCH_BADGE_SHIFT_Y_RATIO
        )


def create_badge_from_png(
    network_path,
    droplet_path,
    output_path,
    size=1024,
    elements_to_draw="both",
    badge_shape="circle"
):
    """
    Crea il badge finale.
    """

    valid_elements = ["network", "droplet", "both"]

    if elements_to_draw not in valid_elements:
        raise ValueError(
            f"elements_to_draw deve essere uno tra: {valid_elements}"
        )

    badge = create_blue_badge(
        size=size,
        badge_shape=badge_shape
    )

    # ========================================================
    # RETE
    # ========================================================

    if elements_to_draw in ["network", "both"]:

        content_size = int(size * CONTENT_SCALE)

        network_resized = prepare_icon(
            img_path=network_path,
            final_size=content_size
        )

        x = (size - content_size) // 2
        y = (size - content_size) // 2

        x += int(size * SHIFT_X_RATIO)
        y += int(size * SHIFT_Y_RATIO)

        badge.alpha_composite(network_resized, (x, y))

    # ========================================================
    # GOCCIA BIANCA INTERNA
    # ========================================================

    if elements_to_draw in ["droplet", "both"]:

        droplet_size = int(size * DROPLET_SCALE)

        droplet_resized = prepare_icon(
            img_path=droplet_path,
            final_size=droplet_size
        )

        dx = (size - droplet_size) // 2
        dy = (size - droplet_size) // 2

        dx += int(size * DROPLET_SHIFT_X_RATIO)
        dy += int(size * DROPLET_SHIFT_Y_RATIO)

        badge.alpha_composite(droplet_resized, (dx, dy))

    # ========================================================
    # CENTRATURA FINALE SU CANVAS
    # ========================================================

    badge = center_and_fit_to_canvas(
        img=badge,
        canvas_size=size,
        padding_ratio=0.00
    )

    badge.save(output_path)

def export_resized_versions(master_path):
    """
    Esporta il master in varie dimensioni.
    """

    master = Image.open(master_path).convert("RGBA")

    for export_size in EXPORT_SIZES:
        out = master.resize(
            (export_size, export_size),
            Image.Resampling.LANCZOS
        )

        output_path = (
            OUTPUT_DIR
            / f"{OUTPUT_BASENAME}_{BADGE_SHAPE}_{ELEMENTS_TO_DRAW}_{export_size}.png"
        )

        out.save(output_path)


def create_all_versions():
    """
    Crea il badge master e le versioni ridimensionate.
    """

    master_path = (
        OUTPUT_DIR
        / f"{OUTPUT_BASENAME}_{BADGE_SHAPE}_{ELEMENTS_TO_DRAW}_master_{CANVAS_SIZE}.png"
    )

    create_badge_from_png(
        network_path=NETWORK_PATH,
        droplet_path=DROPLET_PATH,
        output_path=master_path,
        size=CANVAS_SIZE,
        elements_to_draw=ELEMENTS_TO_DRAW,
        badge_shape=BADGE_SHAPE
    )

    export_resized_versions(master_path)

    print("Done.")
    print(f"Badge shape: {BADGE_SHAPE}")
    print(f"Elements drawn: {ELEMENTS_TO_DRAW}")
    print(f"Network used: {NETWORK_PATH}")
    print(f"Droplet shape used: {DROPLET_PATH}")
    print(f"Files saved in: {OUTPUT_DIR}")
    print(f"Master file: {master_path.name}")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    create_all_versions()
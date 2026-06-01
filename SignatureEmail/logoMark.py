from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


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
WHITE = "#FFFFFF"

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
# CORNICE / SFONDO INTERNO
# ------------------------------------------------------------
# True  = aggiunge cornice bianca esterna al logo
# False = nessuna cornice

ADD_LOGO_FRAME = True

# True  = le zone interne trasparenti della goccia diventano bianche
# False = restano trasparenti

FILL_INTERNAL_TRANSPARENCY_WITH_WHITE = True

# Larghezza cornice esterna in punti
FRAME_WIDTH_PT = 10

# DPI usati per convertire punti -> pixel
# 4 pt a 300 dpi = circa 17 px

FRAME_DPI = 1000


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

CONTENT_SCALE = 0.3

SHIFT_X_RATIO = -0.165    # positivo = destra
SHIFT_Y_RATIO = 0.03      # positivo = giù


# ------------------------------------------------------------
# SAGOMA BLU A GOCCIA
# ------------------------------------------------------------

PINCH_BADGE_SCALE = 1.05

PINCH_BADGE_SHIFT_X_RATIO = 0.00
PINCH_BADGE_SHIFT_Y_RATIO = 0.00


# ------------------------------------------------------------
# GOCCIA BIANCA INTERNA
# ------------------------------------------------------------

DROPLET_SCALE = 0.38

DROPLET_SHIFT_X_RATIO = -0.19
DROPLET_SHIFT_Y_RATIO = 0.19


# ------------------------------------------------------------
# CENTRATURA FINALE SU CANVAS
# ------------------------------------------------------------

FINAL_PADDING_RATIO = 0.0


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


def pt_to_px(points, dpi):
    """
    Converte punti tipografici in pixel.

    1 pt = 1/72 inch.
    """

    return int(round(points * dpi / 72))


def get_frame_width_px():
    """
    Restituisce la larghezza della cornice in pixel.
    """

    if ADD_LOGO_FRAME:
        return pt_to_px(FRAME_WIDTH_PT, FRAME_DPI)

    return 0


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
    Ritaglia il contenuto non trasparente, lo riscalo
    e lo ricentra nella canvas finale.
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


def fill_inside_closed_shape(alpha_mask):
    """
    Riempie l'interno di una forma chiusa.

    Serve per trasformare:
    - una goccia fatta solo da contorno

    in:
    - una maschera piena che include anche l'interno.

    Questa maschera viene usata per fare lo sfondo bianco interno.
    """

    alpha_mask = alpha_mask.convert("L")
    arr = np.array(alpha_mask)

    solid = arr > 10

    h, w = solid.shape

    outside = np.zeros((h, w), dtype=bool)

    stack = []

    for x in range(w):
        if not solid[0, x]:
            outside[0, x] = True
            stack.append((0, x))

        if not solid[h - 1, x]:
            outside[h - 1, x] = True
            stack.append((h - 1, x))

    for y in range(h):
        if not solid[y, 0]:
            outside[y, 0] = True
            stack.append((y, 0))

        if not solid[y, w - 1]:
            outside[y, w - 1] = True
            stack.append((y, w - 1))

    while stack:
        y, x = stack.pop()

        neighbours = [
            (y - 1, x),
            (y + 1, x),
            (y, x - 1),
            (y, x + 1)
        ]

        for ny, nx in neighbours:
            if 0 <= ny < h and 0 <= nx < w:
                if not solid[ny, nx] and not outside[ny, nx]:
                    outside[ny, nx] = True
                    stack.append((ny, nx))

    filled = ~outside

    filled_arr = (filled.astype(np.uint8) * 255)

    return Image.fromarray(filled_arr, mode="L")


def create_white_internal_fill_from_alpha(alpha_mask):
    """
    Crea il bianco interno del logo.

    Usa una maschera piena della goccia:
    tutto ciò che era trasparente dentro la goccia diventa bianco.
    """

    filled_alpha = fill_inside_closed_shape(alpha_mask)

    white_fill = Image.new(
        "RGBA",
        alpha_mask.size,
        hex_to_rgba(WHITE, 255)
    )

    white_fill.putalpha(filled_alpha)

    return white_fill


def create_external_white_frame_from_alpha(alpha_mask, frame_width_px):
    """
    Crea una cornice bianca esterna intorno al logo.

    La cornice è solo esterna:
    prende la maschera del logo, la espande,
    e sottrae la maschera originale.
    """

    alpha_mask = alpha_mask.convert("L")

    kernel_size = 2 * frame_width_px + 1

    expanded_alpha = alpha_mask.filter(
        ImageFilter.MaxFilter(kernel_size)
    )

    expanded_arr = np.array(expanded_alpha).astype(np.int16)
    original_arr = np.array(alpha_mask).astype(np.int16)

    frame_arr = np.clip(
        expanded_arr - original_arr,
        0,
        255
    ).astype(np.uint8)

    frame_alpha = Image.fromarray(frame_arr, mode="L")

    white_frame = Image.new(
        "RGBA",
        alpha_mask.size,
        hex_to_rgba(WHITE, 255)
    )

    white_frame.putalpha(frame_alpha)

    return white_frame


def create_colored_shape_from_alpha(alpha_mask, color):
    """
    Crea una forma colorata usando una maschera alpha.
    """

    colored_shape = Image.new(
        "RGBA",
        alpha_mask.size,
        hex_to_rgba(color, 255)
    )

    colored_shape.putalpha(alpha_mask)

    return colored_shape

def create_blue_shape_from_png(
    shape_path,
    size,
    scale=1.0,
    shift_x_ratio=0.0,
    shift_y_ratio=0.0,
    add_logo_frame=False,
    fill_internal_transparency=False,
    frame_width_pt=4,
    frame_dpi=300
):
    """
    Crea la goccia/logo.

    Metodo:
    1. crea la sagoma bianca esterna più grande
    2. crea eventualmente il riempimento bianco interno
    3. rimette sopra il logo blu originale
    4. allinea logo blu e cornice usando il centro reale delle sagome
    """

    frame_width_px = pt_to_px(frame_width_pt, frame_dpi) if add_logo_frame else 0

    # Dimensione totale del blocco: cornice inclusa
    local_size = int(size * scale)

    if local_size <= 0:
        raise ValueError("local_size non valido.")

    # Dimensione del logo blu interno
    inner_size = local_size - 2 * frame_width_px

    if inner_size <= 0:
        raise ValueError("La cornice è troppo grande rispetto alla goccia.")

    # ========================================================
    # LOGO INTERNO
    # ========================================================

    shape_resized = prepare_icon(
        img_path=shape_path,
        final_size=inner_size
    )

    alpha_original_inner = shape_resized.getchannel("A")

    # Sagoma piena del logo interno
    silhouette_inner = fill_inside_closed_shape(alpha_original_inner)

    # ========================================================
    # SAGOMA ESTERNA BIANCA
    # ========================================================

    # Cornice ottenuta ingrandendo la sagoma piena,
    # NON dilatandola con MaxFilter.
    outer_silhouette = silhouette_inner.resize(
        (local_size, local_size),
        Image.Resampling.LANCZOS
    )

    local_shape = Image.new(
        "RGBA",
        (local_size, local_size),
        (0, 0, 0, 0)
    )

    # ========================================================
    # FUNZIONE INTERNA: CENTRO DELLA BBOX
    # ========================================================

    def bbox_center(alpha):
        """
        Restituisce il centro reale del contenuto non trasparente.
        """

        bbox = alpha.getbbox()

        if bbox is None:
            raise ValueError("Maschera vuota.")

        left, top, right, bottom = bbox

        cx = (left + right) / 2
        cy = (top + bottom) / 2

        return cx, cy

    # Centro reale della sagoma bianca esterna
    outer_cx, outer_cy = bbox_center(outer_silhouette)

    # Centro reale del logo blu interno
    inner_cx, inner_cy = bbox_center(alpha_original_inner)

    # Offset necessario per far coincidere i centri reali
    inner_x = int(round(outer_cx - inner_cx))
    inner_y = int(round(outer_cy - inner_cy))

    # Micro-correzioni opzionali.
    # positivo = destra / giù
    INNER_LOGO_FINE_SHIFT_X = 0
    INNER_LOGO_FINE_SHIFT_Y = 15

    inner_x += INNER_LOGO_FINE_SHIFT_X
    inner_y += INNER_LOGO_FINE_SHIFT_Y

    # ========================================================
    # 1. BIANCO: CORNICE + INTERNO
    # ========================================================

    if add_logo_frame:
        if fill_internal_transparency:
            # Bianco pieno sotto tutta la sagoma esterna:
            # fa sia cornice esterna sia interno bianco.
            white_alpha = outer_silhouette

        else:
            # Solo cornice esterna:
            # sagoma esterna - sagoma interna.
            inner_silhouette_on_local = Image.new(
                "L",
                (local_size, local_size),
                0
            )

            inner_silhouette_on_local.paste(
                silhouette_inner,
                (inner_x, inner_y)
            )

            outer_arr = np.array(outer_silhouette).astype(np.int16)
            inner_arr = np.array(inner_silhouette_on_local).astype(np.int16)

            frame_arr = np.clip(
                outer_arr - inner_arr,
                0,
                255
            ).astype(np.uint8)

            white_alpha = Image.fromarray(frame_arr, mode="L")

        white_layer = Image.new(
            "RGBA",
            (local_size, local_size),
            hex_to_rgba(WHITE, 255)
        )

        white_layer.putalpha(white_alpha)

        local_shape.alpha_composite(white_layer, (0, 0))

    else:
        if fill_internal_transparency:
            white_internal = Image.new(
                "RGBA",
                (inner_size, inner_size),
                hex_to_rgba(WHITE, 255)
            )

            white_internal.putalpha(silhouette_inner)

            local_shape.alpha_composite(
                white_internal,
                (inner_x, inner_y)
            )

    # ========================================================
    # 2. LOGO BLU ORIGINALE SOPRA
    # ========================================================

    blue_logo_inner = create_colored_shape_from_alpha(
        alpha_mask=alpha_original_inner,
        color=BLUE
    )

    local_shape.alpha_composite(
        blue_logo_inner,
        (inner_x, inner_y)
    )

    # ========================================================
    # 3. POSIZIONAMENTO SULLA CANVAS FINALE
    # ========================================================

    badge = Image.new(
        "RGBA",
        (size, size),
        (0, 0, 0, 0)
    )

    x = (size - local_size) // 2
    y = (size - local_size) // 2

    x += int(size * shift_x_ratio)
    y += int(size * shift_y_ratio)

    badge.alpha_composite(local_shape, (x, y))

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
        badge = create_blue_circle(size)

        return badge

    if badge_shape == "pinch":
        badge = create_blue_shape_from_png(
            shape_path=DROPLET_PATH,
            size=size,
            scale=PINCH_BADGE_SCALE,
            shift_x_ratio=PINCH_BADGE_SHIFT_X_RATIO,
            shift_y_ratio=PINCH_BADGE_SHIFT_Y_RATIO,
            add_logo_frame=ADD_LOGO_FRAME,
            fill_internal_transparency=FILL_INTERNAL_TRANSPARENCY_WITH_WHITE,
            frame_width_pt=FRAME_WIDTH_PT,
            frame_dpi=FRAME_DPI
        )

        return badge


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
    # GOCCIA BIANCA INTERNA COME ELEMENTO GRAFICO
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
        padding_ratio=FINAL_PADDING_RATIO
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

    frame_label = "frame" if ADD_LOGO_FRAME else "noframe"
    fill_label = "whiteinside" if FILL_INTERNAL_TRANSPARENCY_WITH_WHITE else "transparentinside"

    master_path = (
        OUTPUT_DIR
        / f"{OUTPUT_BASENAME}_{BADGE_SHAPE}_{ELEMENTS_TO_DRAW}_{frame_label}_{fill_label}_master_{CANVAS_SIZE}.png"
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
    print(f"Add logo frame: {ADD_LOGO_FRAME}")
    print(f"Fill internal transparency with white: {FILL_INTERNAL_TRANSPARENCY_WITH_WHITE}")
    print(f"Frame width: {FRAME_WIDTH_PT} pt")
    print(f"Frame width in px: {pt_to_px(FRAME_WIDTH_PT, FRAME_DPI)} px at {FRAME_DPI} dpi")
    print(f"Network used: {NETWORK_PATH}")
    print(f"Droplet shape used: {DROPLET_PATH}")
    print(f"Files saved in: {OUTPUT_DIR}")
    print(f"Master file: {master_path.name}")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    create_all_versions()
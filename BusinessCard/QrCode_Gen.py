import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageDraw
from pathlib import Path


# =========================
# PARAMETRI
# =========================

URL = "https://demarcoan.github.io/"

BASE_DIR = Path(__file__).resolve().parent

LOGO_PATH = (BASE_DIR / "../assets/images/logos/email_icon/logo_mark_network_badge_pinch_network_frame_whiteinside_master_1024.png").resolve()
OUTPUT_PATH = (BASE_DIR / "../assets/images/QrCode/qr_with_logo_2.png").resolve()

QR_SIZE_CM = 5.4
LOGO_SIZE_CM = 2.5

DPI = 1000
SUPERSAMPLING = 10

QR_COLOR = "#253D8B"
BACKGROUND_COLOR = "white"

# 1 = quadrati pieni
# 0.85 = moduli separati ma ancora leggibili
# 0.70 = più “puntini”, ma meno robusto
CHANNEL_SCALE = 0.82       # spessore dei canali
DOT_SCALE = 0.82           # grandezza dei puntini isolati
CHANNEL_MODE = "mixed"     # "mixed", "horizontal", "vertical", "dots"

# Arrotondamento dei puntini
# True = cerchietti / pillole
# False = quadratini
ROUND_DOTS = True

# Arrotondamento degli occhi del QR
EYE_ROUNDING = 0.28


# =========================
# FUNZIONI
# =========================

def cm_to_px(cm, dpi):
    return round(cm / 2.54 * dpi)


def module_center(row, col, module_px):
    x = col * module_px + module_px / 2
    y = row * module_px + module_px / 2
    return x, y


def draw_dot(draw, row, col, module_px):
    cx, cy = module_center(row, col, module_px)

    size = module_px * DOT_SCALE

    draw.ellipse(
        [
            cx - size / 2,
            cy - size / 2,
            cx + size / 2,
            cy + size / 2
        ],
        fill=QR_COLOR
    )


def draw_channel_between(draw, row1, col1, row2, col2, module_px):
    """
    Disegna un canale arrotondato tra due moduli adiacenti.
    """

    x1, y1 = module_center(row1, col1, module_px)
    x2, y2 = module_center(row2, col2, module_px)

    width = module_px * CHANNEL_SCALE

    draw.line(
        [x1, y1, x2, y2],
        fill=QR_COLOR,
        width=round(width)
    )

    r = width / 2

    # estremità arrotondate
    draw.ellipse(
        [x1 - r, y1 - r, x1 + r, y1 + r],
        fill=QR_COLOR
    )

    draw.ellipse(
        [x2 - r, y2 - r, x2 + r, y2 + r],
        fill=QR_COLOR
    )

def in_finder_zone(row, col, border, n_modules):
    """
    Esclude finder + separatore bianco intorno.
    I finder veri sono 7x7 moduli.
    Aggiungiamo 1 modulo di margine per evitare compenetrazioni.
    """

    zones = [
        # alto sinistra
        (border - 1, border - 1),

        # alto destra
        (n_modules - border - 7 - 1, border - 1),

        # basso sinistra
        (border - 1, n_modules - border - 7 - 1),
    ]

    for x0, y0 in zones:
        if y0 <= row < y0 + 9 and x0 <= col < x0 + 9:
            return True

    return False


def draw_drop_shape(draw, box, corner, fill):
    """
    Disegna una forma tipo goccia dentro un box quadrato.

    corner indica dove punta la goccia:
    - "br" = punta in basso a destra
    - "bl" = punta in basso a sinistra
    - "tr" = punta in alto a destra
    - "tl" = punta in alto a sinistra
    """

    x0, y0, x1, y1 = box
    s = x1 - x0

    radius = s * 0.75

    # corpo principale arrotondato
    draw.rounded_rectangle(
        [x0, y0, x1, y1],
        radius=radius,
        fill=fill
    )

    tip = 0.48*s

    # punta della goccia
    if corner == "br":
        triangle = [
            (x1, y1),
            (x1 - tip, y1),
            (x1, y1 - tip)
        ]

    elif corner == "bl":
        triangle = [
            (x0, y1),
            (x0 + tip, y1),
            (x0, y1 - tip)
        ]

    elif corner == "tr":
        triangle = [
            (x1, y0),
            (x1 - tip, y0),
            (x1, y0 + tip)
        ]

    elif corner == "tl":
        triangle = [
            (x0, y0),
            (x0 + tip, y0),
            (x0, y0 + tip)
        ]

    draw.polygon(triangle, fill=fill)


def draw_eye(draw, x, y, module_px, corner="br"):
    """
    Finder pattern a forma di goccia.

    Mantiene le tre zone:
    esterno blu, interno bianco, centro blu.
    """

    outer_size = 7 * module_px
    middle_margin = 1.05 * module_px
    inner_margin = 2.25 * module_px

    # goccia esterna blu
    outer_box = [
        x,
        y,
        x + outer_size,
        y + outer_size
    ]

    draw_drop_shape(
        draw,
        outer_box,
        corner=corner,
        fill=QR_COLOR
    )

    # goccia interna bianca
    middle_box = [
        x + middle_margin,
        y + middle_margin,
        x + outer_size - middle_margin,
        y + outer_size - middle_margin
    ]

    draw_drop_shape(
        draw,
        middle_box,
        corner=corner,
        fill=BACKGROUND_COLOR
    )

    # centro blu
    inner_box = [
        x + inner_margin,
        y + inner_margin,
        x + outer_size - inner_margin,
        y + outer_size - inner_margin
    ]

    draw_drop_shape(
        draw,
        inner_box,
        corner=corner,
        fill=QR_COLOR
    )


def add_logo(img, logo_path, qr_size_px, logo_size_px):
    logo = Image.open(logo_path).convert("RGBA")

    # forza la larghezza del logo alla misura richiesta
    ratio = logo_size_px / logo.width
    new_h = round(logo.height * ratio)
    logo = logo.resize((logo_size_px, new_h), Image.LANCZOS)

    draw = ImageDraw.Draw(img)

    logo_x = (qr_size_px - logo.width) // 2
    logo_y = (qr_size_px - logo.height) // 2


    img.paste(logo, (logo_x, logo_y), logo)

    return img


# =========================
# CREA QR
# =========================

qr = qrcode.QRCode(
    version=None,
    error_correction=ERROR_CORRECT_H,
    border=3,
    box_size=10
)

qr.add_data(URL)
qr.make(fit=True)

matrix = qr.get_matrix()
n_modules = len(matrix)

border = qr.border

qr_size_px_final = cm_to_px(QR_SIZE_CM, DPI)
qr_size_px_work = qr_size_px_final * SUPERSAMPLING

module_px = qr_size_px_work / n_modules

img = Image.new(
    "RGB",
    (qr_size_px_work, qr_size_px_work),
    BACKGROUND_COLOR
)

draw = ImageDraw.Draw(img)


# =========================
# DISEGNA MODULI NORMALI
# =========================

drawn_as_channel = set()

for row in range(n_modules):
    for col in range(n_modules):

        if not matrix[row][col]:
            continue

        if in_finder_zone(row, col, border, n_modules):
            continue

        current = (row, col)

        # vicino a destra
        right_exists = (
            col + 1 < n_modules
            and matrix[row][col + 1]
            and not in_finder_zone(row, col + 1, border, n_modules)
        )

        # vicino sotto
        down_exists = (
            row + 1 < n_modules
            and matrix[row + 1][col]
            and not in_finder_zone(row + 1, col, border, n_modules)
        )

        if CHANNEL_MODE == "dots":
            draw_dot(draw, row, col, module_px)

        elif CHANNEL_MODE == "horizontal":
            if right_exists:
                draw_channel_between(draw, row, col, row, col + 1, module_px)
                drawn_as_channel.add(current)
                drawn_as_channel.add((row, col + 1))
            elif current not in drawn_as_channel:
                draw_dot(draw, row, col, module_px)

        elif CHANNEL_MODE == "vertical":
            if down_exists:
                draw_channel_between(draw, row, col, row + 1, col, module_px)
                drawn_as_channel.add(current)
                drawn_as_channel.add((row + 1, col))
            elif current not in drawn_as_channel:
                draw_dot(draw, row, col, module_px)

        elif CHANNEL_MODE == "mixed":
            if right_exists:
                draw_channel_between(draw, row, col, row, col + 1, module_px)
                drawn_as_channel.add(current)
                drawn_as_channel.add((row, col + 1))

            if down_exists:
                draw_channel_between(draw, row, col, row + 1, col, module_px)
                drawn_as_channel.add(current)
                drawn_as_channel.add((row + 1, col))

            if not right_exists and not down_exists and current not in drawn_as_channel:
                draw_dot(draw, row, col, module_px)


# =========================
# DISEGNA FINDER PATTERN
# =========================

eye_positions = [
    # alto sinistra
    (border * module_px, border * module_px),

    # alto destra
    ((n_modules - border - 7) * module_px, border * module_px),

    # basso sinistra
    (border * module_px, (n_modules - border - 7) * module_px),
]

draw_eye(draw, eye_positions[0][0], eye_positions[0][1], module_px, corner="br")
draw_eye(draw, eye_positions[1][0], eye_positions[1][1], module_px, corner="bl")
draw_eye(draw, eye_positions[2][0], eye_positions[2][1], module_px, corner="tr")


# =========================
# LOGO
# =========================

logo_size_px_work = cm_to_px(LOGO_SIZE_CM, DPI) * SUPERSAMPLING
img = add_logo(img, LOGO_PATH, qr_size_px_work, logo_size_px_work)


# =========================
# RIDIMENSIONA E SALVA
# =========================

img = img.resize(
    (qr_size_px_final, qr_size_px_final),
    Image.LANCZOS
)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

img.save(OUTPUT_PATH, dpi=(DPI, DPI))

print("QR salvato in:")
print(OUTPUT_PATH)
print()
print(f"QR: {QR_SIZE_CM} cm")
print(f"Logo: {LOGO_SIZE_CM} cm")
print(f"Pixel finali: {qr_size_px_final} x {qr_size_px_final}")
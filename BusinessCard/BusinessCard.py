from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

import numpy as np
from PIL import Image

# ============================================================
# PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

QR_PATH = (BASE_DIR / "../assets/images/QrCode/qr_with_logo.png").resolve()

FRONT_PDF_PATH = (BASE_DIR / "business_card_front.pdf").resolve()
BACK_PDF_PATH = (BASE_DIR / "business_card_back.pdf").resolve()

ICONS_DIR = (BASE_DIR / "../assets/images/icons").resolve()

LINKEDIN_ICON = (ICONS_DIR / "linkedin.png").resolve()
GITHUB_ICON = (ICONS_DIR / "github.png").resolve()
ORCID_ICON = (ICONS_DIR / "ORCID.png").resolve()


# ============================================================
# FONT
# ============================================================

FONT_REGULAR = (BASE_DIR / "../assets_all/fonts/NotoSerif-Regular.ttf").resolve()
FONT_ITALIC = (BASE_DIR / "../assets_all/fonts/NotoSerif-Italic.ttf").resolve()
FONT_BOLD = (BASE_DIR / "../assets_all/fonts/NotoSerif-SemiBold.ttf").resolve()

pdfmetrics.registerFont(TTFont("NotoSerif", str(FONT_REGULAR)))
pdfmetrics.registerFont(TTFont("NotoSerif-Italic", str(FONT_ITALIC)))
pdfmetrics.registerFont(TTFont("NotoSerif-SemiBold", str(FONT_BOLD)))


# ============================================================
# DIMENSIONI
# ============================================================
CARD_W = 55 * mm
CARD_H = 55 * mm

DROP_SIZE = 3.5 * mm      # 0.32 cm = 3.2 mm
DROP_STROKE = 1.5    # spessore 1.5 pt
CENTER_SIZE = 1.1 * mm   # 0.14 cm = 1.4 mm

# posizione della punta della goccia
TIP_X = 4.25 * mm          # 0.4 cm da sinistra
TIP_Y = 4.25 * mm          # 0.4 cm dal basso

# siccome corner="tr", la punta sta in alto a destra del box
DROP_X = TIP_X - DROP_SIZE
DROP_Y = TIP_Y - DROP_SIZE

# ============================================================
# COLORI
# ============================================================
BLUE = HexColor("#253D8B")
WHITE = HexColor("#FFFFFF")


# ============================================================
# FUNZIONI UTILI
# ============================================================

def draw_underlined_text(c, x, y, text, font_name, font_size, color, underline_offset=1.3):
    c.setFillColor(color)
    c.setFont(font_name, font_size)
    c.drawString(x, y, text)

    text_w = c.stringWidth(text, font_name, font_size)

    c.setStrokeColor(color)
    c.setLineWidth(0.35)
    c.line(x, y - underline_offset, x + text_w, y - underline_offset)


def draw_link_text(c, x, y, text, font_name, font_size, color):
    draw_underlined_text(
        c,
        x,
        y,
        text,
        font_name,
        font_size,
        color,
        underline_offset=1.0
    )


# ============================================================
# FRONTE - SOLO QR CODE + CORNICE
# ============================================================

front = canvas.Canvas(str(FRONT_PDF_PATH), pagesize=(CARD_W, CARD_H))

# QR a tutta pagina
front.drawImage(
    str(QR_PATH),
    0,
    0,
    width=CARD_W,
    height=CARD_H,
    mask="auto"
)

# Cornice blu da 6 pt
BORDER_WIDTH = 6  # 6 pt

front.setStrokeColor(BLUE)
front.setLineWidth(BORDER_WIDTH)

# rettangolo centrato sul bordo della pagina
# uso BORDER_WIDTH / 2 per evitare che metà linea finisca fuori dal PDF
front.rect(
    BORDER_WIDTH / 2,
    BORDER_WIDTH / 2,
    CARD_W - BORDER_WIDTH,
    CARD_H - BORDER_WIDTH,
    fill=False,
    stroke=True
)

front.save()

# ============================================================
# RETRO
# ============================================================

back = canvas.Canvas(str(BACK_PDF_PATH), pagesize=(CARD_W, CARD_H))

# Sfondo bianco
back.setFillColor(WHITE)
back.rect(0, 0, CARD_W, CARD_H, fill=True, stroke=False)

# Fascia blu superiore
bottom_h = 20.5 * mm
back.setFillColor(BLUE)
back.rect(0, bottom_h, CARD_W, CARD_H, fill=True, stroke=False)

# Linea bianca orizzontale in alto
back.setStrokeColor(WHITE)
back.setLineWidth(1.5)
back.line(3.75 * mm, CARD_H-3.5 * mm, CARD_W-DROP_SIZE-2*mm, CARD_H-3.5 * mm)

# Linea verticale sinistra
back.setStrokeColor(WHITE)
back.setLineWidth(1.5)
back.line( 4 * mm, CARD_H-3.5 * mm, 4 * mm, bottom_h)

back.setStrokeColor(BLUE)
back.setLineWidth(1.5)
back.line( 4 * mm, bottom_h, 4 * mm, 4 * mm)

# Linea blu orizzontale in basso
back.setStrokeColor(BLUE)
back.setLineWidth(1.5)
back.line(4 * mm, 4 * mm, CARD_W, 4 * mm)

# Piccolo simbolo angolare in basso a sinistra:
# stessa "goccia" usata negli occhi del QR code

def draw_pdf_drop(c, x, y, size, corner, color):
    """
    Disegna una goccia vettoriale in ReportLab.
    x, y = angolo basso-sinistro del box
    size = lato del box
    corner = dove punta la goccia: "br", "bl", "tr", "tl"
    """

    c.setFillColor(color)
    c.setStrokeColor(color)

    r = size * 0.5

    # Corpo arrotondato principale
    c.roundRect(
        x,
        y,
        size,
        size,
        r,
        fill=True,
        stroke=False
    )

    tip = size * 0.48

    # Punta della goccia
    p = c.beginPath()

    if corner == "br":
        p.moveTo(x + size, y)
        p.lineTo(x + size - tip, y)
        p.lineTo(x + size, y + tip)

    elif corner == "bl":
        p.moveTo(x, y)
        p.lineTo(x + tip, y)
        p.lineTo(x, y + tip)

    elif corner == "tr":
        p.moveTo(x + size, y + size)
        p.lineTo(x + size - tip, y + size)
        p.lineTo(x + size, y + size - tip)

    elif corner == "tl":
        p.moveTo(x, y + size)
        p.lineTo(x + tip, y + size)
        p.lineTo(x, y + size - tip)

    p.close()

    c.drawPath(p, fill=True, stroke=False)


# goccia esterna blu: 0.32 cm x 0.32 cm
draw_pdf_drop(
    back,
    DROP_X,
    DROP_Y,
    DROP_SIZE,
    "tr",
    BLUE
)

# goccia interna bianca: crea bordo blu da 1.5 pt
draw_pdf_drop(
    back,
    DROP_X + DROP_STROKE,
    DROP_Y + DROP_STROKE,
    DROP_SIZE - 2 * DROP_STROKE,
    "tr",
    WHITE
)

# goccia centrale blu: 0.14 cm x 0.14 cm
center_offset = (DROP_SIZE - CENTER_SIZE) / 2

draw_pdf_drop(
    back,
    DROP_X + center_offset,
    DROP_Y + center_offset,
    CENTER_SIZE,
    "tr",
    BLUE
)

#### GOCCIA BIANCA IN ALTO A DESTRA

def draw_drop_symbol_rotated(c, tip_x, tip_y, size, angle_deg, outer_color, middle_color, center_color):
    """
    Disegna il simbolo a goccia ruotato.

    tip_x, tip_y = posizione della punta
    size = dimensione della goccia esterna
    angle_deg = rotazione in gradi
    """

    c.saveState()

    # porto l'origine sulla punta
    c.translate(tip_x, tip_y)

    # ruoto tutto il simbolo
    c.rotate(angle_deg)

    # Nel sistema locale uso sempre corner="tr"
    # perché la punta locale è in alto a destra, cioè in (0, 0) dopo lo shift.
    local_x = -size
    local_y = -size

    draw_pdf_drop(
        c,
        local_x,
        local_y,
        size,
        "tr",
        outer_color
    )

    draw_pdf_drop(
        c,
        local_x + DROP_STROKE,
        local_y + DROP_STROKE,
        size - 2 * DROP_STROKE,
        "tr",
        middle_color
    )

    center_offset = (size - CENTER_SIZE) / 2

    draw_pdf_drop(
        c,
        local_x + center_offset,
        local_y + center_offset,
        CENTER_SIZE,
        "tr",
        center_color
    )

    c.restoreState()


#### GOCCIA BIANCA IN ALTO A DESTRA

WHITE_DROP_TIP_X = CARD_W - 6.5 * mm
WHITE_DROP_TIP_Y = CARD_H - 3.5 * mm

draw_drop_symbol_rotated(
    back,
    WHITE_DROP_TIP_X,
    WHITE_DROP_TIP_Y,
    DROP_SIZE,
    135,
    WHITE,
    BLUE,
    WHITE
)



#############################

# Nome
draw_underlined_text(
    back,
    6.5 * mm,
    45.0 * mm,
    "Andrea de Marco",
    "NotoSerif-Italic",
    12,
    WHITE,
    underline_offset=1.0
)

# Ruolo
back.setFillColor(WHITE)
back.setFont("NotoSerif-SemiBold", 9)
back.drawString(6.5 * mm, 39.0 * mm, "Physics of Soft Matter")
back.drawString(6.5 * mm, 35.3 * mm, "and Microfluidics")

# Sito
draw_link_text(
    back,
    6.5 * mm,
    28.5 * mm,
    "https://demarcoan.github.io/",
    "NotoSerif",
    9,
    WHITE
)

# Email
draw_link_text(
    back,
    6.5 * mm,
    24 * mm,
    "andrea.demarco.research@gmail.com",
    "NotoSerif",
    7,
    WHITE
)


def draw_tracking_text(c, x, y, text, font_name, font_size, color, tracking=0):
    """
    Disegna testo con spaziatura personalizzata tra caratteri.

    tracking:
    - 0 = normale
    - negativo = caratteri più vicini
    - positivo = caratteri più lontani

    In ReportLab l'unità base è il point.
    Quindi tracking=-1 significa ridurre di 1 pt tra ogni carattere.
    """

    c.setFillColor(color)
    c.setFont(font_name, font_size)

    current_x = x

    for char in text:
        c.drawString(current_x, y, char)
        current_x += c.stringWidth(char, font_name, font_size) + tracking


# Motto in basso
font_name = "NotoSerif-Italic"
font_size = 11
tracking = -1   # riduce la spaziatura tra caratteri di 1 pt

draw_tracking_text(
    back,
    5.2 * mm,
    14.9 * mm,
    "Let's connect through",
    font_name,
    font_size,
    BLUE,
    tracking
)

draw_tracking_text(
    back,
    5.2 * mm,
    10.7 * mm,
    "research, collaboration,",
    font_name,
    font_size,
    BLUE,
    tracking
)

draw_tracking_text(
    back,
    5.2 * mm,
    6.5 * mm,
    "and scientific ideas.",
    font_name,
    font_size,
    BLUE,
    tracking
)

##################################

def get_visible_bbox(path, ignore_right_fraction=0.0):
    """
    Trova il bounding box dei pixel visibili/non bianchi.
    ignore_right_fraction serve SOLO per il calcolo dell'allineamento,
    non taglia l'immagine.
    """

    img = Image.open(path).convert("RGBA")
    arr = np.array(img)

    alpha = arr[:, :, 3]
    rgb = arr[:, :, :3]

    visible = alpha > 20
    non_white = np.any(rgb < 245, axis=2)

    mask = visible & non_white

    if ignore_right_fraction > 0:
        max_x = int(img.width * (1 - ignore_right_fraction))
        mask[:, max_x:] = False

    ys, xs = np.where(mask)

    return xs.min(), ys.min(), xs.max(), ys.max(), img.width, img.height

def draw_icon_aligned_by_visible_part(
    c,
    path,
    align_center_x,
    center_y,
    max_w,
    max_h,
    ignore_right_fraction=0.0
):
    """
    Disegna tutta l'icona, ma centra solo la parte visibile principale.
    Utile per LinkedIn con il marchio ®.
    """

    img = ImageReader(str(path))
    img_w, img_h = img.getSize()

    x0, y0, x1, y1, pil_w, pil_h = get_visible_bbox(
        path,
        ignore_right_fraction=ignore_right_fraction
    )

    visible_w = x1 - x0
    visible_h = y1 - y0

    # Scala rispetto alla parte principale visibile
    ratio = min(max_w / visible_w, max_h / visible_h)

    draw_w = img_w * ratio
    draw_h = img_h * ratio

    visible_center_x = ((x0 + x1) / 2) * ratio
    visible_center_y = ((pil_h - (y0 + y1) / 2)) * ratio

    draw_x = align_center_x - visible_center_x
    draw_y = center_y - visible_center_y

    c.drawImage(
        img,
        draw_x,
        draw_y,
        width=draw_w,
        height=draw_h,
        mask="auto"
    )


def get_fitted_icon_size(path, max_w, max_h):
    """
    Restituisce la dimensione effettiva con cui l'icona verrà disegnata,
    mantenendo le proporzioni.
    """
    img = ImageReader(str(path))
    img_w, img_h = img.getSize()

    ratio = min(max_w / img_w, max_h / img_h)

    draw_w = img_w * ratio
    draw_h = img_h * ratio

    return img, draw_w, draw_h


def draw_icon_centered(c, path, center_x, center_y, max_w, max_h):
    """
    Disegna un'icona centrata in center_x, center_y,
    mantenendo le proporzioni.
    """
    img, draw_w, draw_h = get_fitted_icon_size(path, max_w, max_h)

    x = center_x - draw_w / 2
    y = center_y - draw_h / 2

    c.drawImage(
        img,
        x,
        y,
        width=draw_w,
        height=draw_h,
        mask="auto"
    )

    return draw_w, draw_h


# ============================================================
# ICONE
# ============================================================

# Centro orizzontale comune delle tre icone
icon_center_x = 51.0 * mm

# Limiti verticali reali
top_limit = bottom_h       # fascia blu sopra
bottom_limit = 4.0 * mm    # linea blu sotto

# Box massimi disponibili per ciascuna icona
linkedin_max_w = 4.2 * mm
linkedin_max_h = 4.2 * mm

github_max_w = 4.0 * mm
github_max_h = 4.0 * mm

orcid_max_w = 4.0 * mm
orcid_max_h = 4.0 * mm

# Calcolo dimensioni effettive delle icone, senza deformarle
_, linkedin_w, linkedin_h = get_fitted_icon_size(
    LINKEDIN_ICON,
    linkedin_max_w,
    linkedin_max_h
)

_, github_w, github_h = get_fitted_icon_size(
    GITHUB_ICON,
    github_max_w,
    github_max_h
)

_, orcid_w, orcid_h = get_fitted_icon_size(
    ORCID_ICON,
    orcid_max_w,
    orcid_max_h
)

# Spazio disponibile tra fascia blu e linea blu
available_h = top_limit - bottom_limit

# Somma delle altezze reali disegnate
icons_total_h = linkedin_h + github_h + orcid_h

# Quattro spazi uguali:
# fascia blu -> LinkedIn
# LinkedIn -> GitHub
# GitHub -> ORCID
# ORCID -> linea blu
gap = (available_h - icons_total_h) / 4

# Coordinate dei centri
orcid_center_y = bottom_limit + gap + orcid_h / 2
github_center_y = orcid_center_y + orcid_h / 2 + gap + github_h / 2
linkedin_center_y = github_center_y + github_h / 2 + gap + linkedin_h / 2

# Disegno centrato
draw_icon_aligned_by_visible_part(
    back,
    LINKEDIN_ICON,
    icon_center_x,
    linkedin_center_y,
    4.2 * mm,
    4.2 * mm,
    ignore_right_fraction=0.16
)

draw_icon_centered(
    back,
    GITHUB_ICON,
    icon_center_x,
    github_center_y,
    github_max_w,
    github_max_h
)

draw_icon_centered(
    back,
    ORCID_ICON,
    icon_center_x,
    orcid_center_y,
    orcid_max_w,
    orcid_max_h
)



###################

back.save()


print("PDF creati:")
print(FRONT_PDF_PATH)
print(BACK_PDF_PATH)
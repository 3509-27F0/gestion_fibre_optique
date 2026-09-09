from io import BytesIO
from pathlib import Path
import base64

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.lib.utils import ImageReader


BASE = Path(__file__).parent
LOGO = BASE / "assets" / "logo_vipnet.png"
BACKGROUND = BASE / "assets" / "arriere_plan_fibre.jpeg"
UPLOADS = BASE / "uploads"


def generate_pdf(intervention):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=55,
        bottomMargin=45,
        title="Intervention " + str(intervention["numero"]),
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PDFTitle",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0b3fa5"),
        spaceAfter=12,
    )

    section_style = ParagraphStyle(
        "PDFSection",
        parent=styles["Heading2"],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0b3fa5"),
        spaceBefore=8,
        spaceAfter=5,
    )

    normal_style = ParagraphStyle(
        "PDFNormal",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
    )

    elements = []

    if LOGO.exists():
        logo = Image(str(LOGO))
        logo.drawHeight = 40
        logo.drawWidth = 125
        elements.append(logo)
        elements.append(Spacer(1, 8))

    elements.append(
        Paragraph(
            "FICHE D'INTERVENTION FIBRE OPTIQUE",
            title_style
        )
    )

    elements.append(
        Paragraph(
            "<b>Numéro :</b> "
            + str(intervention["numero"])
            + " &nbsp;&nbsp;&nbsp; "
            + "<b>Date :</b> "
            + str(intervention["date_intervention"]),
            normal_style,
        )
    )

    elements.append(Spacer(1, 10))

    def value(key):
        v = intervention[key]
        if v is None or str(v).strip() == "":
            return "-"
        return (
            str(v)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )

    sections = [
        (
            "Informations générales",
            [
                ("Technicien(s)", "techniciens"),
                ("Client / Société", "client"),
                ("Site", "site"),
                ("Localisation", "localisation"),
                ("Type d'intervention", "type_intervention"),
                ("Équipement concerné", "equipement"),
                ("Type de fibre", "fibre_type"),
            ],
        ),
        (
            "Horaires",
            [
                ("Heure de début", "heure_debut"),
                ("Heure de fin", "heure_fin"),
            ],
        ),
        (
            "Diagnostic et mesures",
            [
                ("Nature du problème / demande", "probleme"),
                ("Diagnostic effectué", "diagnostic"),
                ("Distance du défaut", "distance_defaut"),
                ("Puissance avant", "puissance_avant"),
                ("Puissance après", "puissance_apres"),
            ],
        ),
        (
            "Travaux et matériel",
            [
                ("Travaux réalisés", "travaux"),
                ("Matériel utilisé", "materiel"),
            ],
        ),
        (
            "Résultat et suivi",
            [
                ("Résultat", "resultat"),
                ("Recommandations", "recommandations"),
                ("Observations", "observations"),
            ],
        ),
    ]

    for section_name, fields in sections:
        elements.append(
            Paragraph(section_name, section_style)
        )

        data = [
            [
                Paragraph("<b>Champ</b>", normal_style),
                Paragraph("<b>Informations</b>", normal_style),
            ]
        ]

        for label, key in fields:
            data.append(
                [
                    Paragraph("<b>" + label + "</b>", normal_style),
                    Paragraph(value(key), normal_style),
                ]
            )

        table = Table(
            data,
            colWidths=[145, 365],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#0b3fa5"),
                    ),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#c8d2e3"),
                    ),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    (
                        "BACKGROUND",
                        (0, 1),
                        (0, -1),
                        colors.HexColor("#eef3fb"),
                    ),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 7))

    # -------------------------------------------------------------------------
    # PHOTOS / PREUVES
    # Les photos sont récupérées automatiquement dans uploads/NUMERO/
    # -------------------------------------------------------------------------
    photo_folder = UPLOADS / str(intervention["numero"])

    if photo_folder.exists():
        photos = [
            p for p in sorted(photo_folder.iterdir())
            if p.is_file()
            and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
        ]

        if photos:
            elements.append(PageBreak())
            elements.append(
                Paragraph("Photos / preuves de l'intervention", section_style)
            )
            elements.append(Spacer(1, 8))

            for photo_path in photos:
                try:
                    img = Image(str(photo_path))
                    img._restrictSize(500, 300)

                    elements.append(img)
                    elements.append(Spacer(1, 6))

                    elements.append(
                        Paragraph(
                            "<b>Photo :</b> "
                            + photo_path.name.replace("&", "&amp;"),
                            normal_style,
                        )
                    )
                    elements.append(Spacer(1, 14))

                except Exception:
                    elements.append(
                        Paragraph(
                            "Impossible d'afficher la photo : "
                            + photo_path.name,
                            normal_style,
                        )
                    )

    def watermark(canvas, document):
        canvas.saveState()

        if BACKGROUND.exists():
            try:
                image = ImageReader(str(BACKGROUND))
                canvas.setFillAlpha(0.10)
                canvas.drawImage(
                    image,
                    55,
                    150,
                    width=485,
                    height=485,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                canvas.setFillAlpha(1)
            except Exception:
                pass

        canvas.setStrokeColor(colors.HexColor("#0b3fa5"))
        canvas.line(
            40,
            A4[1] - 42,
            A4[0] - 40,
            A4[1] - 42,
        )

        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(
            A4[0] / 2,
            25,
            "VIPNET • Gestion Fibre Optique • "
            + str(intervention["numero"]),
        )

        canvas.restoreState()

    doc.build(
        elements,
        onFirstPage=watermark,
        onLaterPages=watermark,
    )

    return buffer.getvalue()


def pdf_preview(pdf_bytes):
    encoded = base64.b64encode(pdf_bytes).decode("utf-8")

    return (
        '<iframe '
        'src="data:application/pdf;base64,'
        + encoded
        + '" width="100%" height="850" '
        'style="border:1px solid #d0d7e2; '
        'border-radius:10px;"></iframe>'
    )

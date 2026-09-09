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


def generate_ot_pdf(ot):
    """
    Génère le PDF d'une Demande d'Autorisation OT.
    Le PDF reflète toujours le statut actuel de l'OT.
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=55,
        bottomMargin=45,
        title="Demande OT " + str(ot["numero"]),
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "OTTitle",
        parent=styles["Title"],
        fontSize=17,
        leading=21,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0b3fa5"),
        spaceAfter=10,
    )

    section_style = ParagraphStyle(
        "OTSection",
        parent=styles["Heading2"],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0b3fa5"),
        spaceBefore=8,
        spaceAfter=5,
    )

    normal_style = ParagraphStyle(
        "OTNormal",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
    )

    status_style = ParagraphStyle(
        "OTStatus",
        parent=styles["BodyText"],
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.white,
    )

    elements = []

    def value(key):
        v = ot[key]
        if v is None or str(v).strip() == "":
            return "-"
        return (
            str(v)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )

    # -------------------------------------------------------------------------
    # LOGO
    # -------------------------------------------------------------------------
    if LOGO.exists():
        logo = Image(str(LOGO))
        logo.drawHeight = 40
        logo.drawWidth = 125
        elements.append(logo)
        elements.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # TITRE
    # -------------------------------------------------------------------------
    elements.append(
        Paragraph(
            "DEMANDE D'AUTORISATION (OT)",
            title_style,
        )
    )

    elements.append(
        Paragraph(
            "<b>Ordre de Travail</b> &nbsp;&nbsp; "
            "<b>Numéro :</b> " + value("numero") +
            " &nbsp;&nbsp;&nbsp; "
            "<b>Date :</b> " + value("date_demande"),
            normal_style,
        )
    )

    elements.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # STATUT
    # -------------------------------------------------------------------------
    statut = str(ot["statut"] or "En attente de validation")

    if statut == "Validée":
        status_text = "VALIDÉE"
        status_background = colors.HexColor("#198754")
    elif statut == "Refusée":
        status_text = "REFUSÉE"
        status_background = colors.HexColor("#dc3545")
    else:
        status_text = "EN ATTENTE DE VALIDATION"
        status_background = colors.HexColor("#f0ad00")

    status_table = Table(
        [[Paragraph("<b>" + status_text + "</b>", status_style)]],
        colWidths=[510],
    )

    status_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), status_background),
                ("BOX", (0, 0), (-1, -1), 0.8, status_background),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elements.append(status_table)
    elements.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # INFORMATIONS GÉNÉRALES
    # -------------------------------------------------------------------------
    sections = [
        (
            "Informations de la demande",
            [
                ("Demandeur", "demandeur"),
                ("Client / Société", "client"),
                ("Site", "site"),
                ("Localisation", "localisation"),
            ],
        ),
        (
            "Travaux demandés",
            [
                ("Objet du travail", "objet_travail"),
                ("Description des travaux", "description_travaux"),
                ("Équipe / Techniciens concernés", "equipe"),
            ],
        ),
        (
            "Planning",
            [
                ("Date de début", "date_debut"),
                ("Date de fin", "date_fin"),
                ("Heure de début", "heure_debut"),
                ("Heure de fin", "heure_fin"),
            ],
        ),
        (
            "Observations",
            [
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
            colWidths=[170, 340],
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
    # ZONE DE VALIDATION
    # -------------------------------------------------------------------------
    elements.append(
        Paragraph(
            "Validation de la demande",
            section_style,
        )
    )

    validateur = value("validateur")
    date_validation = value("date_validation")
    mode_validation = value("mode_validation")
    observation_validation = value("observation_validation")

    if statut == "Validée":
        validation_data = [
            [
                Paragraph("<b>Statut</b>", normal_style),
                Paragraph("VALIDÉE", normal_style),
            ],
            [
                Paragraph("<b>Validateur</b>", normal_style),
                Paragraph(validateur, normal_style),
            ],
            [
                Paragraph("<b>Date de validation</b>", normal_style),
                Paragraph(date_validation, normal_style),
            ],
            [
                Paragraph("<b>Mode de validation</b>", normal_style),
                Paragraph(mode_validation, normal_style),
            ],
            [
                Paragraph("<b>Observation</b>", normal_style),
                Paragraph(observation_validation, normal_style),
            ],
        ]
    elif statut == "Refusée":
        validation_data = [
            [
                Paragraph("<b>Statut</b>", normal_style),
                Paragraph("REFUSÉE", normal_style),
            ],
            [
                Paragraph("<b>Validateur</b>", normal_style),
                Paragraph(validateur, normal_style),
            ],
            [
                Paragraph("<b>Date</b>", normal_style),
                Paragraph(date_validation, normal_style),
            ],
            [
                Paragraph("<b>Observation / Motif</b>", normal_style),
                Paragraph(observation_validation, normal_style),
            ],
        ]
    else:
        validation_data = [
            [
                Paragraph("<b>Statut</b>", normal_style),
                Paragraph("EN ATTENTE DE VALIDATION", normal_style),
            ],
            [
                Paragraph(
                    "<b>Validation physique</b>",
                    normal_style,
                ),
                Paragraph(
                    "☐ Autorisée &nbsp;&nbsp;&nbsp; ☐ Refusée",
                    normal_style,
                ),
            ],
            [
                Paragraph("<b>Nom du responsable</b>", normal_style),
                Paragraph("________________________________", normal_style),
            ],
            [
                Paragraph("<b>Fonction</b>", normal_style),
                Paragraph("________________________________", normal_style),
            ],
            [
                Paragraph("<b>Signature</b>", normal_style),
                Paragraph(
                    "________________________________<br/><br/>",
                    normal_style,
                ),
            ],
            [
                Paragraph("<b>Date</b>", normal_style),
                Paragraph("________________________________", normal_style),
            ],
        ]

    validation_table = Table(
        validation_data,
        colWidths=[170, 340],
    )

    validation_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#c8d2e3"),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#eef3fb"),
                ),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    elements.append(validation_table)
    elements.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # FILIGRANE ET PIED DE PAGE
    # -------------------------------------------------------------------------
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
            "VIPNET • Demande d'Autorisation OT • "
            + str(ot["numero"]),
        )

        canvas.restoreState()

    doc.build(
        elements,
        onFirstPage=watermark,
        onLaterPages=watermark,
    )

    return buffer.getvalue()

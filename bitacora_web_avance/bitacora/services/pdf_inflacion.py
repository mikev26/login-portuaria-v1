import os
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any

from django.conf import settings

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        Image,
        KeepTogether,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


if REPORTLAB_AVAILABLE:
    class NumberedCanvas(canvas.Canvas):
        """Canvas personalizado para numeración de páginas 'Página X de Y'."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_number(num_pages)
                super().showPage()
            super().save()

        def draw_page_number(self, page_count):
            self.saveState()
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#475569"))
            page_text = f"Página {self._pageNumber} de {page_count}"
            self.drawRightString(letter[0] - 36, 20, page_text)
            self.restoreState()
else:
    NumberedCanvas = None


def formatear_fecha_espanol(fecha_str: str | None) -> str:
    """Convierte YYYY-MM-DD a formato '8 de enero de 2026'."""
    if not fecha_str:
        hoy = datetime.now()
        meses = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
        ]
        return f"{hoy.day} de {meses[hoy.month - 1]} de {hoy.year}"
    try:
        dt = datetime.strptime(str(fecha_str).strip(), "%Y-%m-%d")
        meses = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
        ]
        return f"{dt.day} de {meses[dt.month - 1]} de {dt.year}"
    except Exception:
        return str(fecha_str)


def generar_pdf_tarifario_inflacion(
    tarifas: List[Dict[str, Any]],
    anio: int,
    porcentaje: float,
    fecha_inflacion: str | None = None,
    detalle: str = "",
) -> bytes:
    """
    Genera un documento PDF con el diseño y colores exactos de Plantilla_Inflacion.xlsx.
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError(
            "La librería 'reportlab' no está instalada en el entorno virtual. "
            "Ejecute: pip install reportlab"
        )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=32,
        title=f"Tarifa Inflación {anio}",
        author="Autoridad Portuaria de Manta",
        subject=f"Tarifario del Terminal Pesquero y Cabotaje {anio}",
        creator="Autoridad Portuaria de Manta",
    )

    styles = getSampleStyleSheet()
    
    # 🎨 Color exacto de cabecera Excel (Theme 7 Tint 0.8 / Gold Lighter 80%: #FFF2CC)
    COLOR_EXCEL_HEADER = colors.HexColor("#FFF2CC")
    COLOR_BLACK = colors.HexColor("#000000")
    
    # Tipografías y estilos
    title_main_style = ParagraphStyle(
        "ExcelTitleMain",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=15,
        alignment=TA_CENTER,
        textColor=COLOR_BLACK,
    )
    
    title_sub_style = ParagraphStyle(
        "ExcelTitleSub",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        alignment=TA_CENTER,
        textColor=COLOR_BLACK,
    )
    
    title_legal_style = ParagraphStyle(
        "ExcelTitleLegal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        alignment=TA_CENTER,
        textColor=COLOR_BLACK,
    )

    tbl_header_style = ParagraphStyle(
        "ExcelTableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=COLOR_BLACK,
    )

    tbl_cell_center = ParagraphStyle(
        "ExcelCellCenter",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=COLOR_BLACK,
    )

    tbl_cell_left = ParagraphStyle(
        "ExcelCellLeft",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
        textColor=COLOR_BLACK,
    )

    tbl_cell_right = ParagraphStyle(
        "ExcelCellRight",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=TA_RIGHT,
        textColor=COLOR_BLACK,
    )

    tbl_cell_right_bold = ParagraphStyle(
        "ExcelCellRightBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_RIGHT,
        textColor=COLOR_BLACK,
    )

    note_taxes_center = ParagraphStyle(
        "ExcelNoteTaxesCenter",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=COLOR_BLACK,
    )

    note_circular_left = ParagraphStyle(
        "ExcelNoteCircular",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
        textColor=COLOR_BLACK,
    )

    note_legal_text = ParagraphStyle(
        "ExcelNoteLegal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.8,
        leading=8.5,
        alignment=TA_JUSTIFY,
        textColor=COLOR_BLACK,
    )

    note_responsable_text = ParagraphStyle(
        "ExcelNoteResponsable",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        alignment=TA_LEFT,
        textColor=COLOR_BLACK,
    )

    story = []

    # 1. ENCABEZADO CON LOGO Y TÍTULOS IDÉNTICOS AL EXCEL
    logo_path = os.path.join(
        settings.BASE_DIR, "bitacora", "static", "bitacora", "img", "logo_manta.png"
    )
    
    titles_flowable = [
        Paragraph("TARIFARIO DEL TERMINAL PESQUERO Y CABOTAJE", title_main_style),
        Spacer(1, 2),
        Paragraph("TRÁFICO NACIONAL", title_sub_style),
        Spacer(1, 2),
        Paragraph("R.O. 228 de marzo 14 de 2006 / Reforma 30 de Oct.2019", title_legal_style),
    ]

    if os.path.exists(logo_path):
        try:
            # Preservar la relación de aspecto original de la imagen (336 x 307 -> 1.0945)
            img_height = 46.0
            img_width = img_height * 1.09446  # ~ 50.35 pt
            img = Image(logo_path, width=img_width, height=img_height)
            
            # Tabla simétrica de 3 columnas para que los títulos queden exactamente en el centro de la página
            # Columna Izquierda (Logo): 60 pt, Columna Central (Títulos): 420 pt, Columna Derecha (Balance): 60 pt
            header_table = Table(
                [[img, titles_flowable, ""]],
                colWidths=[60, 420, 60],
            )
            header_table.setStyle(
                TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "CENTER"),
                    ("ALIGN", (2, 0), (2, 0), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ])
            )
            story.append(header_table)
        except Exception:
            for tf in titles_flowable:
                story.append(tf)
    else:
        for tf in titles_flowable:
            story.append(tf)

    story.append(Spacer(1, 14))

    # 2. TABLA CON COLUMNAS Y COLORES EXACTOS DE PLANTILLA_INFLACION.XLSX
    # Las columnas visibles en la plantilla son:
    # ITEM | CÓDIGO | SERVICIOS | INFLACIÓN (%) | TARIFA (año)
    # Anchos calibrados para que el porcentaje quede al lado en una sola línea horizontal
    col_widths = [34, 56, 245, 110, 95]  # Total: 540 pt
    pct_formatted = f"{porcentaje:.2f}%".replace(".", ",")

    table_data = [
        [
            Paragraph("<b>ITEM</b>", tbl_header_style),
            Paragraph("<b>CÓDIGO</b>", tbl_header_style),
            Paragraph("<b>SERVICIOS</b>", tbl_header_style),
            Paragraph(f"<b>INFLACIÓN ({pct_formatted})</b>", tbl_header_style),
            Paragraph(f"<b>TARIFA {anio}</b>", tbl_header_style),
        ]
    ]

    for idx, t in enumerate(tarifas, start=1):
        codigo = str(t.get("codigo", "") or t.get("id", "")).strip()
        servicio = str(t.get("tarifa", "")).strip()
        
        try:
            val_base = float(str(t.get("valor", "0")).replace(",", "."))
        except (ValueError, TypeError):
            val_base = 0.0

        inflacion_monto = val_base * (porcentaje / 100.0)
        tarifa_total = val_base + inflacion_monto

        row = [
            Paragraph(str(idx), tbl_cell_center),
            Paragraph(codigo, tbl_cell_center),
            Paragraph(servicio, tbl_cell_left),
            Paragraph(f"$ {inflacion_monto:,.4f}", tbl_cell_right),
            Paragraph(f"$ {tarifa_total:,.4f}", tbl_cell_right_bold),
        ]
        table_data.append(row)

    if len(tarifas) == 0:
        table_data.append([
            Paragraph("1", tbl_cell_center),
            Paragraph("-", tbl_cell_center),
            Paragraph("No existen tarifas configuradas con aplicación de inflación.", tbl_cell_left),
            Paragraph("$ 0.0000", tbl_cell_right),
            Paragraph("$ 0.0000", tbl_cell_right_bold),
        ])

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # 📐 Cuadrícula idéntica a Excel: Fondo #FFF2CC en cabecera y bordes negros (#000000)
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_EXCEL_HEADER),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_BLACK),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BLACK),
            ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BLACK),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ])
    )
    story.append(table)
    story.append(Spacer(1, 12))

    # 3. NOTAS AL PIE Y TEXTOS LEGALES (Filas 18 a 26 de la plantilla Excel)
    fecha_texto = formatear_fecha_espanol(fecha_inflacion)
    
    nota_transitoria = (
        f"<b>Nota:</b> En las tarifas para el año {anio} se considera la aplicación del literal b) de las "
        "Disposiciones Transitorias del Reglamento Tarifario para la Operación del Puerto Pesquero y Cabotaje "
        "para la Autoridad Portuaria de Manta, que señala: <i>“b) El reajuste anual de las tarifas, por inflación, "
        f"se aplicará a partir del 1 de enero del año siguiente; con fecha {fecha_texto}, el Instituto Nacional de "
        f"Estadísticas y Censos (INEC) emite Boletín Técnico IPC Nro. 12- {anio - 1}-IPC, en el que informa el índice "
        f"de inflación, el cual corresponde al {pct_formatted}.”</i>"
    )

    fuente_legal = (
        "<b>Fuente:</b> Reglamento Tarifario para la Operación del Puerto Pesquero y Cabotaje para la Autoridad "
        "Portuaria de Manta, aprobado con Resolución Nro. DIGMER 001/06 09ENE2006, publicado en el Registro Oficial "
        "Nro. 228 14MAR2006 y sus reformas contenidas en Resolución Nro. SPTMF 007/13 28ENE2013, publicado en el "
        "Registro Oficial Nro. 891 14FEB2013; Resolución Nro. MTOP-SPTM-2015-0119-R 02OCT2015, publicado en el "
        "Registro Oficial Nro. 625 11NOV2015 y Resolución Nro. MTOP-SPTM-2019-0089-R 20SEP2019, publicado en el "
        "Registro Oficial Nro. 71 30OCT2019."
    )

    circular = "Circular Nº.MTOP-SPTM-20-1-CIRC. /GUAYAQUIL, 21 de enero de 2020."
    responsable = "Responsable: Dirección de Promoción y Comercialización APM"

    footer_elements = [
        Paragraph("<b>*No Incluye impuestos*</b>", note_taxes_center),
        Spacer(1, 5),
        Paragraph(circular, note_circular_left),
        Spacer(1, 4),
        Paragraph(fuente_legal, note_legal_text),
        Spacer(1, 4),
        Paragraph(nota_transitoria, note_legal_text),
        Spacer(1, 6),
        Paragraph(responsable, note_responsable_text),
    ]

    story.append(KeepTogether(footer_elements))

    # Construir documento
    doc.build(story, canvasmaker=NumberedCanvas)
    
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value

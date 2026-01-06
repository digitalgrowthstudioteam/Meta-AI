from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from app.billing.invoice_models import Invoice


class InvoicePDFService:
    """
    Generates compliant invoice PDFs.
    Pure service — no DB writes.
    """

    @staticmethod
    def generate_pdf(invoice: Invoice) -> bytes:
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()
        elements = []

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------
        elements.append(Paragraph("<b>Digital Growth Studio</b>", styles["Title"]))
        elements.append(Spacer(1, 12))

        elements.append(
            Paragraph(f"Invoice #: {invoice.invoice_number}", styles["Normal"])
        )
        elements.append(
            Paragraph(
                f"Invoice Date: {invoice.invoice_date.strftime('%d %b %Y')}",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 20))

        # -------------------------------------------------
        # BILLING DETAILS
        # -------------------------------------------------
        elements.append(Paragraph("<b>Billed To</b>", styles["Heading3"]))
        elements.append(Paragraph(invoice.billing_name, styles["Normal"]))
        elements.append(Paragraph(invoice.billing_email, styles["Normal"]))
        elements.append(Spacer(1, 20))

        # -------------------------------------------------
        # PERIOD (IF ANY)
        # -------------------------------------------------
        if invoice.period_from and invoice.period_to:
            elements.append(
                Paragraph(
                    f"Service Period: {invoice.period_from.strftime('%d %b %Y')} "
                    f"to {invoice.period_to.strftime('%d %b %Y')}",
                    styles["Normal"],
                )
            )
            elements.append(Spacer(1, 20))

        # -------------------------------------------------
        # AMOUNT TABLE
        # -------------------------------------------------
        data = [
            ["Description", "Amount (INR)"],
            ["Subtotal", f"{invoice.subtotal / 100:.2f}"],
            ["Tax", f"{invoice.tax_amount / 100:.2f}"],
            ["Total", f"{invoice.total_amount / 100:.2f}"],
        ]

        table = Table(data, colWidths=[300, 150])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONT", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 30))

        # -------------------------------------------------
        # FOOTER
        # -------------------------------------------------
        elements.append(
            Paragraph(
                "This is a system-generated invoice and does not require a signature.",
                styles["Italic"],
            )
        )

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

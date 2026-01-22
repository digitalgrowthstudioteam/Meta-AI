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
from app.billing.company_settings_models import BillingCompanySettings
from app.users.models import User


class InvoicePDFService:
    """
    Generates GST-compliant invoice PDFs with Always-IGST model.
    Pure service — no DB writes.
    """

    IGST_RATE = 18  # always IGST @ 18%

    @staticmethod
    def generate_pdf(
        *,
        invoice: Invoice,
        company: BillingCompanySettings,
        buyer: User,
    ) -> bytes:

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

        # ==================================================
        # SUPPLIER HEADER
        # ==================================================
        elements.append(Paragraph(f"<b>{company.company_name}</b>", styles["Title"]))
        elements.append(Paragraph(company.address_line1, styles["Normal"]))
        if company.address_line2:
            elements.append(Paragraph(company.address_line2, styles["Normal"]))
        elements.append(Paragraph(f"State: {company.state} ({company.state_code})", styles["Normal"]))

        if company.contact_email:
            elements.append(Paragraph(f"Email: {company.contact_email}", styles["Normal"]))
        if company.contact_phone:
            elements.append(Paragraph(f"Phone: {company.contact_phone}", styles["Normal"]))

        # Supplier GST
        if company.gst_registered and company.gstin:
            elements.append(Paragraph(f"GSTIN: {company.gstin}", styles["Normal"]))
        if company.sac_code:
            elements.append(Paragraph(f"SAC: {company.sac_code}", styles["Normal"]))

        elements.append(Spacer(1, 20))

        # ==================================================
        # INVOICE META
        # ==================================================
        elements.append(Paragraph(f"Invoice #: {invoice.invoice_number}", styles["Normal"]))
        elements.append(
            Paragraph(
                f"Invoice Date: {invoice.invoice_date.strftime('%d %b %Y')}",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 20))

        # ==================================================
        # BUYER DETAILS
        # ==================================================
        elements.append(Paragraph("<b>Billed To</b>", styles["Heading3"]))
        elements.append(Paragraph(invoice.billing_name, styles["Normal"]))
        elements.append(Paragraph(invoice.billing_email, styles["Normal"]))

        if buyer.buyer_gstin:
            elements.append(Paragraph(f"Buyer GSTIN: {buyer.buyer_gstin}", styles["Normal"]))

        elements.append(Spacer(1, 20))

        # ==================================================
        # PERIOD (IF ANY)
        # ==================================================
        if invoice.period_from and invoice.period_to:
            elements.append(
                Paragraph(
                    f"Service Period: {invoice.period_from.strftime('%d %b %Y')} "
                    f"to {invoice.period_to.strftime('%d %b %Y')}",
                    styles["Normal"],
                )
            )
            elements.append(Spacer(1, 20))

        # ==================================================
        # TAX LOGIC (ALWAYS IGST MODEL)
        # ==================================================
        subtotal_val = invoice.subtotal / 100
        tax_val = 0
        tax_label = "IGST"

        show_gst = (
            company.gst_registered is True
            and company.gstin is not None
            and not buyer.buyer_turnover_below_threshold
        )

        data = [["Description", "Amount (INR)"]]
        data.append(["Subtotal", f"{subtotal_val:.2f}"])

        if show_gst:
            tax_val = round(subtotal_val * (InvoicePDFService.IGST_RATE / 100), 2)
            data.append([f"IGST @{InvoicePDFService.IGST_RATE}%", f"{tax_val:.2f}"])
            total_val = subtotal_val + tax_val
        else:
            # GST Exempt Case
            data.append(["GST Not Applicable", "0.00"])
            total_val = subtotal_val

        data.append(["Total", f"{total_val:.2f}"])

        # ==================================================
        # AMOUNT TABLE
        # ==================================================
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
        elements.append(Spacer(1, 20))

        # ==================================================
        # GST EXEMPT FOOTER NOTES
        # ==================================================
        if not show_gst and buyer.buyer_turnover_below_threshold:
            elements.append(
                Paragraph(
                    "<i>GST not applicable — Buyer turnover below ₹20 lakh as declared.</i>",
                    styles["Italic"],
                )
            )
            elements.append(
                Paragraph(
                    "<i>Buyer declares annual aggregate turnover below ₹20 lakh and not registered under GST.</i>",
                    styles["Italic"],
                )
            )
            elements.append(Spacer(1, 20))

        # ==================================================
        # FOOTER
        # ==================================================
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

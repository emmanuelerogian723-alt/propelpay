"""PropelPay PDF Generator — Beautiful invoices and receipts using ReportLab"""
import io
from datetime import datetime
from typing import Optional, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                  Spacer, HRFlowable, KeepTogether)
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.colors import HexColor

# Brand colors
INDIGO   = HexColor("#6366f1")
PURPLE   = HexColor("#8b5cf6")
DARK     = HexColor("#0f172a")
CARD     = HexColor("#1e293b")
MUTED    = HexColor("#64748b")
WHITE    = HexColor("#ffffff")
GREEN    = HexColor("#10b981")
RED      = HexColor("#ef4444")
YELLOW   = HexColor("#f59e0b")
BORDER   = HexColor("#334155")
TEXT     = HexColor("#e2e8f0")
LIGHT_BG = HexColor("#f8fafc")
GREY     = HexColor("#94a3b8")

def _currency_symbol(currency: str) -> str:
    return {"NGN": "₦", "USD": "$", "GBP": "£", "EUR": "€", "GHS": "₵", "KES": "Ksh"}.get(currency, currency + " ")

def _fmt_amount(amount: float, currency: str) -> str:
    sym = _currency_symbol(currency)
    return f"{sym}{amount:,.2f}"

def generate_invoice_pdf(
    invoice_number: str,
    business_name: str,
    business_email: str,
    client_name: str,
    client_email: str,
    items: List[dict],
    subtotal: float,
    tax_rate: float,
    tax_amount: float,
    discount: float,
    total: float,
    currency: str,
    due_date: str,
    created_date: str,
    notes: Optional[str] = None,
    terms: Optional[str] = None,
    status: str = "pending",
    paystack_link: Optional[str] = None,
) -> bytes:
    """Generate a beautiful, professional PDF invoice."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )

    story = []
    W = A4[0] - 36*mm  # usable width

    # ── HEADER ─────────────────────────────────────────────────
    header_data = [[
        Paragraph(f'<font size="22" color="#6366f1"><b>⚡ PropelPay</b></font><br/>'
                  f'<font size="9" color="#64748b">Send. Sign. Get Paid.</font>', 
                  ParagraphStyle("logo", fontName="Helvetica")),
        Paragraph(f'<font size="22" color="#0f172a"><b>INVOICE</b></font><br/>'
                  f'<font size="11" color="#6366f1"><b>{invoice_number}</b></font>',
                  ParagraphStyle("inv", alignment=TA_RIGHT, fontName="Helvetica")),
    ]]
    header_table = Table(header_data, colWidths=[W*0.5, W*0.5])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=INDIGO))
    story.append(Spacer(1, 5*mm))

    # ── STATUS BADGE + DATES ───────────────────────────────────
    status_color = {"paid": "#10b981", "pending": "#f59e0b", "overdue": "#ef4444", "draft": "#64748b"}.get(status, "#6366f1")
    info_data = [[
        Paragraph(f'<b>From:</b><br/>'
                  f'<font size="12"><b>{business_name}</b></font><br/>'
                  f'<font size="9" color="#64748b">{business_email}</font>',
                  ParagraphStyle("from", fontName="Helvetica", leading=14)),
        Paragraph(f'<b>Bill To:</b><br/>'
                  f'<font size="12"><b>{client_name}</b></font><br/>'
                  f'<font size="9" color="#64748b">{client_email}</font>',
                  ParagraphStyle("to", fontName="Helvetica", leading=14)),
        Paragraph(f'<b>Issue Date:</b> {created_date}<br/>'
                  f'<b>Due Date:</b> <font color="#ef4444">{due_date}</font><br/>'
                  f'<b>Status:</b> <font color="{status_color}"><b>{status.upper()}</b></font>',
                  ParagraphStyle("dates", fontName="Helvetica", alignment=TA_RIGHT, leading=14)),
    ]]
    info_table = Table(info_data, colWidths=[W*0.35, W*0.35, W*0.30])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BACKGROUND", (0,0), (-1,-1), HexColor("#f8fafc")),
        ("ROUNDEDCORNERS", [4,4,4,4]),
        ("BOX", (0,0), (-1,-1), 0.5, HexColor("#e2e8f0")),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 6*mm))

    # ── LINE ITEMS TABLE ───────────────────────────────────────
    col_w = [W*0.45, W*0.12, W*0.20, W*0.23]
    item_data = [[
        Paragraph("<b>DESCRIPTION</b>", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=9)),
        Paragraph("<b>QTY</b>", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=9, alignment=TA_CENTER)),
        Paragraph("<b>UNIT PRICE</b>", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=9, alignment=TA_RIGHT)),
        Paragraph("<b>TOTAL</b>", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=9, alignment=TA_RIGHT)),
    ]]

    for i, item in enumerate(items):
        row_bg = HexColor("#f8fafc") if i % 2 == 0 else WHITE
        item_data.append([
            Paragraph(str(item.get("description", "")), ParagraphStyle("cell", fontName="Helvetica", fontSize=9, leading=12)),
            Paragraph(str(item.get("quantity", 1)), ParagraphStyle("cell", fontName="Helvetica", fontSize=9, alignment=TA_CENTER)),
            Paragraph(_fmt_amount(float(item.get("unit_price", 0)), currency),
                      ParagraphStyle("cell", fontName="Helvetica", fontSize=9, alignment=TA_RIGHT)),
            Paragraph(_fmt_amount(float(item.get("total", 0)), currency),
                      ParagraphStyle("cell", fontName="Helvetica-Bold", fontSize=9, alignment=TA_RIGHT)),
        ])

    items_table = Table(item_data, colWidths=col_w, repeatRows=1)
    row_styles = [
        ("BACKGROUND", (0,0), (-1,0), INDIGO),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 9),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("GRID", (0,0), (-1,-1), 0.3, HexColor("#e2e8f0")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]
    for i in range(1, len(item_data)):
        if i % 2 == 0:
            row_styles.append(("BACKGROUND", (0,i), (-1,i), HexColor("#f8fafc")))
    items_table.setStyle(TableStyle(row_styles))
    story.append(items_table)
    story.append(Spacer(1, 4*mm))

    # ── TOTALS ─────────────────────────────────────────────────
    totals_data = []
    totals_data.append(["", "Subtotal:", _fmt_amount(subtotal, currency)])
    if tax_rate > 0:
        totals_data.append(["", f"Tax ({tax_rate:.0f}%):", _fmt_amount(tax_amount, currency)])
    if discount > 0:
        totals_data.append(["", "Discount:", f"-{_fmt_amount(discount, currency)}"])
    totals_data.append(["", "TOTAL DUE:", _fmt_amount(total, currency)])

    totals_table = Table(totals_data, colWidths=[W*0.55, W*0.25, W*0.20])
    total_row = len(totals_data) - 1
    totals_table.setStyle(TableStyle([
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("FONTNAME", (1,0), (-1,-2), "Helvetica"),
        ("FONTNAME", (1,total_row), (-1,total_row), "Helvetica-Bold"),
        ("FONTSIZE", (1,0), (-1,-2), 9),
        ("FONTSIZE", (1,total_row), (-1,total_row), 13),
        ("TEXTCOLOR", (1,total_row), (-1,total_row), INDIGO),
        ("BACKGROUND", (1,total_row), (-1,total_row), HexColor("#eef2ff")),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (1,0), (-1,-1), 8),
        ("LINEABOVE", (1,total_row), (-1,total_row), 1.5, INDIGO),
        ("BOX", (1,total_row), (-1,total_row), 0.5, INDIGO),
    ]))
    story.append(totals_table)

    # ── PAYMENT LINK ───────────────────────────────────────────
    if paystack_link and status != "paid":
        story.append(Spacer(1, 5*mm))
        pay_data = [[
            Paragraph(f'<font color="#10b981" size="11"><b>💳 Pay Online:</b></font>  '
                      f'<font color="#6366f1" size="9">{paystack_link}</font>',
                      ParagraphStyle("pay", fontName="Helvetica"))
        ]]
        pay_table = Table(pay_data, colWidths=[W])
        pay_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), HexColor("#f0fdf4")),
            ("BOX", (0,0), (-1,-1), 1, GREEN),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
            ("LEFTPADDING", (0,0), (-1,-1), 12),
        ]))
        story.append(pay_table)

    # ── NOTES & TERMS ──────────────────────────────────────────
    if notes or terms:
        story.append(Spacer(1, 5*mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#e2e8f0")))
        story.append(Spacer(1, 3*mm))
        if notes:
            story.append(Paragraph(f"<b>Notes:</b> {notes}",
                ParagraphStyle("notes", fontName="Helvetica", fontSize=8, textColor=HexColor("#475569"))))
            story.append(Spacer(1, 2*mm))
        if terms:
            story.append(Paragraph(f"<b>Terms:</b> {terms}",
                ParagraphStyle("terms", fontName="Helvetica", fontSize=8, textColor=HexColor("#475569"))))

    # ── FOOTER ─────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=INDIGO))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        '<font size="8" color="#94a3b8">Generated by PropelPay · propelpay.io · '
        'Send. Sign. Get Paid. · Thank you for your business!</font>',
        ParagraphStyle("footer", alignment=TA_CENTER, fontName="Helvetica")))

    doc.build(story)
    return buf.getvalue()


def generate_receipt_pdf(
    invoice_number: str,
    business_name: str,
    business_email: str,
    client_name: str,
    client_email: str,
    total: float,
    currency: str,
    paid_at: str,
    payment_method: str = "Paystack",
    transaction_ref: Optional[str] = None,
) -> bytes:
    """Generate a clean payment receipt PDF."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=25*mm, rightMargin=25*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )
    story = []
    W = A4[0] - 50*mm

    # Header
    story.append(Paragraph(
        '<font size="26" color="#6366f1"><b>⚡ PropelPay</b></font>',
        ParagraphStyle("logo", alignment=TA_CENTER, fontName="Helvetica")))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        '<font size="10" color="#64748b">Send. Sign. Get Paid.</font>',
        ParagraphStyle("tagline", alignment=TA_CENTER, fontName="Helvetica")))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=INDIGO))
    story.append(Spacer(1, 6*mm))

    # RECEIPT title
    story.append(Paragraph(
        '<font size="20" color="#0f172a"><b>PAYMENT RECEIPT</b></font>',
        ParagraphStyle("title", alignment=TA_CENTER, fontName="Helvetica-Bold")))
    story.append(Spacer(1, 2*mm))

    # Big green checkmark amount
    receipt_box = [[
        Paragraph(f'<font size="36" color="#10b981"><b>✓</b></font><br/>'
                  f'<font size="28" color="#10b981"><b>{_fmt_amount(total, currency)}</b></font><br/>'
                  f'<font size="11" color="#64748b">Payment Confirmed</font>',
                  ParagraphStyle("amount", alignment=TA_CENTER, fontName="Helvetica", leading=36))
    ]]
    box_table = Table(receipt_box, colWidths=[W])
    box_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), HexColor("#f0fdf4")),
        ("BOX", (0,0), (-1,-1), 1.5, GREEN),
        ("TOPPADDING", (0,0), (-1,-1), 20),
        ("BOTTOMPADDING", (0,0), (-1,-1), 20),
        ("ROUNDEDCORNERS", [8,8,8,8]),
    ]))
    story.append(box_table)
    story.append(Spacer(1, 6*mm))

    # Details table
    details = [
        ["Invoice Number:", invoice_number],
        ["Date Paid:", paid_at],
        ["Payment Method:", payment_method],
        ["Paid By:", f"{client_name} ({client_email})"],
        ["Received By:", f"{business_name} ({business_email})"],
    ]
    if transaction_ref:
        details.append(["Transaction Ref:", transaction_ref])

    det_table = Table(details, colWidths=[W*0.38, W*0.62])
    det_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("TEXTCOLOR", (0,0), (0,-1), HexColor("#475569")),
        ("TEXTCOLOR", (1,0), (1,-1), HexColor("#0f172a")),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LINEBELOW", (0,0), (-1,-2), 0.3, HexColor("#e2e8f0")),
        ("BACKGROUND", (0,0), (-1,-1), HexColor("#f8fafc")),
        ("BOX", (0,0), (-1,-1), 0.5, HexColor("#e2e8f0")),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
    ]))
    story.append(det_table)
    story.append(Spacer(1, 8*mm))

    story.append(Paragraph(
        '<font size="10" color="#475569">This is an official payment receipt from PropelPay. '
        'Please keep this for your records.</font>',
        ParagraphStyle("note", alignment=TA_CENTER, fontName="Helvetica")))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=INDIGO))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        '<font size="8" color="#94a3b8">PropelPay · propelpay.io · Thank you for your payment!</font>',
        ParagraphStyle("footer", alignment=TA_CENTER, fontName="Helvetica")))

    doc.build(story)
    return buf.getvalue()

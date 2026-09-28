"""
Phase 4 Attachment Parser Module

Extracts clean text content from uploaded PDF, XLSX, CSV, and text files.
Supports openpyxl for Excel workbooks and pypdf for PDF documents, with regex stream fallback.
"""
import io
import re
from typing import Dict, Any, Optional

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import pypdf
except ImportError:
    pypdf = None


def extract_text_from_attachment(filename: str, content_bytes: bytes) -> str:
    """
    Extract text content from uploaded PDF, XLSX, CSV, or TXT file bytes.
    """
    ext = f".{filename.split('.')[-1].lower()}" if "." in filename else ""

    if ext in (".xlsx", ".xls"):
        return _extract_xlsx_text(content_bytes)
    elif ext == ".pdf":
        return _extract_pdf_text(content_bytes)
    else:
        try:
            return content_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return f"File: {filename}"


def _extract_xlsx_text(content_bytes: bytes) -> str:
    """Extract cell text content from Excel workbook rows."""
    if not openpyxl:
        try:
            return content_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    try:
        wb = openpyxl.load_workbook(io.BytesIO(content_bytes), data_only=True)
        lines = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            lines.append(f"--- Sheet: {sheet_name} ---")
            for row in ws.iter_rows(values_only=True):
                row_cells = [str(cell).strip() for cell in row if cell is not None and str(cell).strip() != ""]
                if row_cells:
                    lines.append(" | ".join(row_cells))
        return "\n".join(lines)
    except Exception:
        try:
            return content_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return ""


def _extract_pdf_text(content_bytes: bytes) -> str:
    """Extract text from PDF pages using pypdf with fallback stream extraction."""
    extracted = ""
    if pypdf:
        try:
            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            page_texts = []
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    page_texts.append(txt)
            if page_texts:
                extracted = "\n".join(page_texts)
        except Exception:
            extracted = ""

    if not extracted.strip():
        try:
            raw_str = content_bytes.decode("latin-1", errors="ignore")
            matches = re.findall(r"\(([^()]{2,})\)\s*T[jJ]", raw_str)
            if matches:
                extracted = "\n".join(matches)
            else:
                matches_bt = re.findall(r"BT\s*(.*?)\s*ET", raw_str, re.DOTALL)
                cleaned = []
                for m in matches_bt:
                    sub = re.findall(r"\(([^()]+)\)", m)
                    cleaned.extend(sub)
                if cleaned:
                    extracted = "\n".join(cleaned)
        except Exception:
            extracted = ""

    return extracted if extracted.strip() else content_bytes.decode("utf-8", errors="ignore")


def parse_quotation_text_fields(prompt_text: str) -> Dict[str, Any]:
    """
    Intelligently parse quotation financial and commercial fields from text prompt.
    Supports table pipe delimiters '|', colons ':', equals '=', and whitespace.
    Raises ValueError if financial quotation data cannot be extracted.
    """
    if not prompt_text or not prompt_text.strip():
        raise ValueError("Empty or unparseable quotation document content.")

    delim = r"\s*[:\s\|\=\-]*"

    up_m = re.search(r"(?:Unit\s*Price|Price\s*/\s*Unit|Price\s*per\s*unit|Rate)" + delim + r"\$?\s*([0-9\.,]+)", prompt_text, re.IGNORECASE)
    tp_m = re.search(r"(?:Total\s*Price|Total\s*Quote|Total\s*Amount)\s*[:\s\|\=\-]*\$?\s*([0-9\.,]+)", prompt_text, re.IGNORECASE)
    lt_m = re.search(r"(?:Lead\s*Time|Delivery\s*Time)\s*[:\s\|\=\-]*([0-9]+)", prompt_text, re.IGNORECASE)
    moq_m = re.search(r"(?:MOQ|Minimum\s*Order)\s*[:\s\|\=\-]*([0-9]+\s*\w*)", prompt_text, re.IGNORECASE)
    pt_m = re.search(r"(?:Payment\s*Terms?)\s*[:\s\|\=\-]*([^\n,\|]+)", prompt_text, re.IGNORECASE)
    w_m = re.search(r"(?:Warranty|Guarantee)\s*[:\s\|\=\-]*([^\n,\|]+)", prompt_text, re.IGNORECASE)
    val_m = re.search(r"(?:Validity\s*Period|Valid\s*For|Quote\s*Valid)\s*[:\s\|\=\-]*([^\n,\|]+)", prompt_text, re.IGNORECASE)

    if not up_m and not tp_m:
        raise ValueError("Could not extract financial unit price or total price from quotation content.")

    unit_price = float(up_m.group(1).replace(",", "").rstrip(".")) if up_m else 0.0
    total_price = float(tp_m.group(1).replace(",", "").rstrip(".")) if tp_m else 0.0

    if unit_price > 0 and total_price == 0:
        qty_m = re.search(r"(?:Quantity|Qty)\s*[:\s\|\=\-]*([0-9]+)", prompt_text, re.IGNORECASE)
        qty = int(qty_m.group(1)) if qty_m else 1
        total_price = round(unit_price * qty, 2)
    elif total_price > 0 and unit_price == 0:
        qty_m = re.search(r"(?:Quantity|Qty)\s*[:\s\|\=\-]*([0-9]+)", prompt_text, re.IGNORECASE)
        qty = int(qty_m.group(1)) if qty_m else 1
        unit_price = round(total_price / qty, 2)

    lead_time_days = int(lt_m.group(1)) if lt_m else 14
    moq = moq_m.group(1).strip() if moq_m else "100 units"
    payment_terms = pt_m.group(1).strip() if pt_m else "Net 30"
    notes = f"Warranty: {w_m.group(1).strip()}" if w_m else "Standard manufacturer warranty included."
    validity_period = val_m.group(1).strip() if val_m else "30 days"

    return {
        "unit_price": unit_price,
        "total_price": total_price,
        "currency": "USD",
        "moq": moq,
        "lead_time_days": lead_time_days,
        "validity_period": validity_period,
        "payment_terms": payment_terms,
        "notes": notes,
        "confidence_score": 0.95,
    }

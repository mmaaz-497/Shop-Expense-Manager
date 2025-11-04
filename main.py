# app.py
"""
AR Monthly Shop Expense Manager (Option A - JSON/CSV local storage)
Author: Tailored for user (single-file Streamlit)
Features:
 - PIN lock each start (4-digit)
 - Auto days per month (leap-year aware)
 - Integer-only daily sales
 - Profit = percentage of total sales
 - Dynamic expenses (default Rent)
 - Pie chart for expense breakdown
 - Warning banner if expenses > profit
 - Save records as JSON files to records/ folder + generate PDF (ReportLab)
 - Upload custom logo (ar_logo.png) or use uploaded image in session
"""

import streamlit as st
from datetime import datetime
import calendar
import os
import json
import hashlib
import io
from typing import List, Dict, Any

import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image

# -----------------------
# Config
# -----------------------
RECORDS_DIR = "records"
PIN_FILE = ".pin_hash"
LOGO_FILENAME_DEFAULT = "ar_logo.png"  # app will use this file if present in app folder
CURRENCY_SYMBOL = "₨"

os.makedirs(RECORDS_DIR, exist_ok=True)

# -----------------------
# Utility functions
# -----------------------
def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def set_pin(pin: str):
    with open(PIN_FILE, "w") as f:
        f.write(sha256(pin))

def check_pin(pin: str) -> bool:
    if not os.path.exists(PIN_FILE):
        return False
    with open(PIN_FILE, "r") as f:
        stored = f.read().strip()
    return stored == sha256(pin)

def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]

def compute_total_sales(daily: List[int]) -> int:
    return sum(int(x or 0) for x in daily)

def compute_profit(total_sales: int, pct: float) -> float:
    return total_sales * (pct / 100.0)

def compute_total_expenses(expenses: List[Dict[str, Any]]) -> float:
    return sum(float(e.get("amount", 0) or 0) for e in expenses)

def fmt_pk(num: float) -> str:
    # integer formatting with commas
    return f"{CURRENCY_SYMBOL}{int(round(num)):,}"

def save_record_json(record: Dict[str, Any]) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"record_{record['month_name']}_{record['year']}_{ts}.json"
    path = os.path.join(RECORDS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return path

def list_saved_records() -> List[str]:
    files = [f for f in os.listdir(RECORDS_DIR) if f.endswith(".json")]
    files.sort(reverse=True)
    return files

def load_record(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_pdf_bytes(record: Dict[str, Any], daily_sales: List[int], logo_path: str = None) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph(f"{record.get('shop_name', 'AR Shop')} — {record['month_name']} {record['year']}", styles["Title"]))
    elements.append(Spacer(1, 8))

    # Logo (if provided)
    if logo_path and os.path.exists(logo_path):
        try:
            rl_img = RLImage(logo_path, width=80, height=80)
            elements.append(rl_img)
            elements.append(Spacer(1, 8))
        except Exception:
            pass

    # Summary
    summary = f"""
    <b>Total Sales:</b> {fmt_pk(record['total_sales'])} <br/>
    <b>Profit %:</b> {record['profit_pct']}% <br/>
    <b>Profit Amount:</b> {fmt_pk(record['profit_amount'])} <br/>
    <b>Total Expenses:</b> {fmt_pk(record['total_expenses'])} <br/>
    <b>Remaining Profit:</b> {fmt_pk(record['remaining_profit'])}
    """
    elements.append(Paragraph(summary, styles["Normal"]))
    elements.append(Spacer(1, 10))

    # Daily sales table
    data = [["Day", f"Sales ({CURRENCY_SYMBOL})"]]
    for i, s in enumerate(daily_sales, start=1):
        data.append([str(i), f"{int(s):,}"])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                               ("GRID", (0,0), (-1,-1), 0.4, colors.black),
                               ("ALIGN",(0,0),(-1,-1),"CENTER")]))
    elements.append(Paragraph("Daily Sales", styles["Heading3"]))
    elements.append(table)
    elements.append(Spacer(1,12))

    # Expenses table
    edata = [["Expense Name", f"Amount ({CURRENCY_SYMBOL})"]]
    for e in record["expenses"]:
        edata.append([e.get("name", ""), f"{int(round(float(e.get('amount',0)))):,}"])
    etable = Table(edata, repeatRows=1)
    etable.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                                ("GRID", (0,0), (-1,-1), 0.4, colors.black),
                                ("ALIGN",(0,0),(-1,-1),"CENTER")]))
    elements.append(Paragraph("Expenses", styles["Heading3"]))
    elements.append(etable)
    elements.append(Spacer(1,12))

    # Tagline footer if exists
    if record.get("tagline"):
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(record.get("tagline"), styles["Italic"]))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

# -----------------------
# Streamlit app UI
# -----------------------
st.set_page_config(page_title="AR Monthly Expense", layout="wide")
st.title("AR — Monthly Shop Expense Manager")

# PIN setup/login
if not os.path.exists(PIN_FILE):
    st.warning("Please set a 4-digit PIN. You will be asked for this PIN every time the app starts.")
    pin = st.text_input("Set 4-digit PIN", type="password", max_chars=4, key="set_pin")
    if st.button("Set PIN"):
        if not (pin.isdigit() and len(pin) == 4):
            st.error("PIN must be exactly 4 digits.")
        else:
            set_pin(pin)
            st.success("PIN saved. Please refresh the page and login.")
            st.stop()
    else:
        st.stop()
else:
    with st.sidebar:
        pin_attempt = st.text_input("Enter 4-digit PIN", type="password", max_chars=4, key="pin_attempt")
        if st.button("Unlock"):
            if check_pin(pin_attempt):
                st.success("Unlocked")
                st.session_state["unlocked"] = True
            else:
                st.error("Incorrect PIN")
                st.session_state["unlocked"] = False
    if not st.session_state.get("unlocked", False):
        st.info("Enter your PIN in the sidebar and press Unlock.")
        st.stop()

with st.form("meta"):
    shop_name = st.text_input("Shop Name (used in PDF header)", value="AR Book Mart")
    tagline = st.text_input("Shop Tagline (appears in PDF footer)", value="AR Book Mart — Excellence in Service & Savings")
    c1, c2 = st.columns(2)
    with c1:
        month_name = st.selectbox("Select Month", list(calendar.month_name)[1:], index=datetime.now().month - 1)
    with c2:
        year = st.number_input("Year", min_value=2000, max_value=2100, value=datetime.now().year, step=1)
    submitted = st.form_submit_button("Set Month & Year")
month_number = list(calendar.month_name).index(month_name)
num_days = days_in_month(int(year), month_number)

st.markdown(f"### Enter daily sales for **{month_name} {int(year)}** — {num_days} day(s)")

# Daily sales inputs (integers) arranged in 7-column grid
daily_sales = []
cols = st.columns(7)
for day in range(1, num_days + 1):
    with cols[(day - 1) % 7]:
        v = st.number_input(f"{day}", min_value=0, value=0, step=1, format="%d", key=f"day_{day}")
        daily_sales.append(int(v))

total_sales = compute_total_sales(daily_sales)
st.metric("Total Sales", fmt_pk(total_sales))

# Profit %
profit_pct = st.slider("Profit Percentage (%)", min_value=0.0, max_value=100.0, value=20.0, step=0.1)
profit_amount = compute_profit(total_sales, profit_pct)
st.metric("Profit Amount", fmt_pk(profit_amount))

# Expenses dynamic rows
st.header("Shop Expenses")
if "expenses" not in st.session_state:
    st.session_state["expenses"] = [{"name": "Rent", "amount": 0}]

def add_row():
    st.session_state.expenses.append({"name": "", "amount": 0})

def remove_row(i):
    if len(st.session_state.expenses) > 1:
        st.session_state.expenses.pop(i)

for idx, ex in enumerate(st.session_state.expenses):
    r1, r2, r3 = st.columns([3,2,1])
    with r1:
        st.session_state.expenses[idx]["name"] = st.text_input(f"Expense name #{idx+1}", key=f"ex_name_{idx}", value=ex.get("name",""))
    with r2:
        amt = st.number_input(f"Amount #{idx+1}", key=f"ex_amt_{idx}", min_value=0, value=int(ex.get("amount",0)), step=1, format="%d")
        st.session_state.expenses[idx]["amount"] = int(amt)
    with r3:
        if st.button("Remove", key=f"rm_{idx}"):
            remove_row(idx)
            st.rerun()

if st.button("Add Expense Field"):
    add_row()
    st.rerun()

# Pie chart of expenses
total_expenses = compute_total_expenses(st.session_state.expenses)
st.write("### Expense Breakdown")
if total_expenses > 0:
    labels = [e.get("name","Unnamed") or "Unnamed" for e in st.session_state.expenses]
    sizes = [float(e.get("amount",0) or 0) for e in st.session_state.expenses]
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct=lambda p: f"{p:.1f}%" if p>0 else "", startangle=90)
    ax.axis("equal")
    st.pyplot(fig)
else:
    st.info("Add expense amounts to populate pie chart.")

# Warning banner if expenses > profit
remaining_profit = profit_amount - total_expenses
if total_expenses > profit_amount:
    st.error(f"Alert: Total expenses {fmt_pk(total_expenses)} exceed expected profit {fmt_pk(profit_amount)}. Remaining profit: {fmt_pk(remaining_profit)}")

# Calculate / Save / Export
st.header("Calculate & Save")
if st.button("Calculate Summary"):
    st.session_state["_last_summary"] = {
        "total_sales": total_sales,
        "profit_pct": profit_pct,
        "profit_amount": profit_amount,
        "total_expenses": total_expenses,
        "remaining_profit": remaining_profit
    }
    st.success("Summary calculated. You can now save or generate PDF.")

col1, col2 = st.columns(2)
with col1:
    if st.button("Save Record (JSON)"):
        record = {
            "created_at": datetime.now().isoformat(),
            "month": month_number,
            "month_name": month_name,
            "year": int(year),
            "shop_name": shop_name,
            "tagline": tagline,
            "profit_pct": float(profit_pct),
            "total_sales": int(total_sales),
            "profit_amount": float(profit_amount),
            "total_expenses": float(total_expenses),
            "remaining_profit": float(remaining_profit),
            "daily_sales": daily_sales.copy(),
            "expenses": [e.copy() for e in st.session_state.expenses]
        }
        path = save_record_json(record)
        st.success(f"Record saved: {path}")

with col2:
    if st.button("Generate PDF (Save & Download)"):
        # Build record dict (same as save)
        record = {
            "created_at": datetime.now().isoformat(),
            "month": month_number,
            "month_name": month_name,
            "year": int(year),
            "shop_name": shop_name,
            "tagline": tagline,
            "profit_pct": float(profit_pct),
            "total_sales": int(total_sales),
            "profit_amount": float(profit_amount),
            "total_expenses": float(total_expenses),
            "remaining_profit": float(remaining_profit),
            "daily_sales": daily_sales.copy(),
            "expenses": [e.copy() for e in st.session_state.expenses]
        }
        # Save JSON for persistence
        json_path = save_record_json(record)
        # Generate PDF bytes
        logo_path = logo_to_use if logo_to_use else None
        pdf_bytes = generate_pdf_bytes(record, daily_sales, logo_path)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_name = f"AR_Report_{month_name}_{year}_{ts}.pdf"
        pdf_path = os.path.join(RECORDS_DIR, pdf_name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        st.success(f"PDF saved: {pdf_path}")
        st.download_button("Download PDF", data=pdf_bytes, file_name=pdf_name, mime="application/pdf")

# Show last calculation summary
if "_last_summary" in st.session_state:
    s = st.session_state["_last_summary"]
    st.subheader("Last Calculation")
    st.write({
        "Total Sales": fmt_pk(s["total_sales"]),
        "Profit %": f"{s['profit_pct']}%",
        "Profit Amount": fmt_pk(s["profit_amount"]),
        "Total Expenses": fmt_pk(s["total_expenses"]),
        "Remaining Profit": fmt_pk(s["remaining_profit"])
    })

# Saved records (JSON) listing & edit/load
st.header("Saved Records (JSON files)")
files = list_saved_records()
if not files:
    st.info("No saved records yet.")
else:
    # Show as expandable cards for mobile friendliness
    for fname in files:
        p = os.path.join(RECORDS_DIR, fname)
        rec = load_record(p)
        title = f"{rec['month_name']} {rec['year']} — {fmt_pk(rec['remaining_profit'])}"
        with st.expander(title):
            st.write(f"Saved at: {rec['created_at']}")
            st.write(f"Shop: {rec.get('shop_name','')}")
            st.write(f"Total Sales: {fmt_pk(rec['total_sales'])}")
            st.write(f"Profit %: {rec['profit_pct']}%")
            st.write(f"Total Expenses: {fmt_pk(rec['total_expenses'])}")
            # Download JSON
            with open(p, "rb") as f:
                btn_label = f"Download JSON ({fname})"
                st.download_button(btn_label, data=f, file_name=fname, mime="application/json")
            # Download PDF built from this record
            if st.button(f"Generate & Download PDF for {fname}", key=f"pdf_{fname}"):
                pdf_bytes = generate_pdf_bytes(rec, rec["daily_sales"], logo_to_use)
                pdf_name = fname.replace(".json", ".pdf")
                pdf_path = os.path.join(RECORDS_DIR, pdf_name)
                with open(pdf_path, "wb") as fpdf:
                    fpdf.write(pdf_bytes)
                st.success(f"PDF saved: {pdf_path}")
                st.download_button("Download PDF", data=pdf_bytes, file_name=pdf_name, mime="application/pdf")
            # Load / Edit button
            if st.button(f"Load this record to edit", key=f"load_{fname}"):
                # populate session_state for editing
                st.session_state["editing_file"] = p
                st.session_state["editing_data"] = rec
                st.rerun()

# Edit loaded record (if any)
if st.session_state.get("editing_data"):
    ed = st.session_state["editing_data"]
    st.header("Edit Loaded Record")
    new_shop = st.text_input("Shop Name", value=ed.get("shop_name",""))
    new_tagline = st.text_input("Tagline", value=ed.get("tagline",""))
    new_profit_pct = st.slider("Profit %", min_value=0.0, max_value=100.0, value=float(ed.get("profit_pct",20.0)), step=0.1)
    # edit daily sales (respect number of days)
    dlist = ed.get("daily_sales", [])
    # ensure length matches num_days (for the current month) — but allow editing full list
    edit_days = st.number_input("Days in record (for edit convenience)", min_value=1, max_value=31, value=len(dlist), step=1, key="edit_days_len")
    while len(dlist) < edit_days:
        dlist.append(0)
    edited_daily = []
    for i in range(edit_days):
        v = st.number_input(f"Day {i+1}", min_value=0, value=int(dlist[i]), step=1, key=f"edit_day_{i}")
        edited_daily.append(int(v))
    # edit expenses
    edit_expenses = ed.get("expenses", [])
    if "edit_expenses" not in st.session_state:
        st.session_state["edit_expenses"] = edit_expenses.copy()
    # render editable expense rows
    for idx, ex in enumerate(st.session_state["edit_expenses"]):
        e1, e2, e3 = st.columns([3,2,1])
        with e1:
            st.session_state["edit_expenses"][idx]["name"] = st.text_input(f"Expense name #{idx+1}", key=f"edit_ex_name_{idx}", value=ex.get("name",""))
        with e2:
            amt = st.number_input(f"Expense amount #{idx+1}", key=f"edit_ex_amt_{idx}", min_value=0, value=int(ex.get("amount",0)), step=1, format="%d")
            st.session_state["edit_expenses"][idx]["amount"] = int(amt)
        with e3:
            if st.button("Remove", key=f"edit_rm_{idx}"):
                st.session_state["edit_expenses"].pop(idx)
                st.rerun()
    if st.button("Add Expense (edit)"):
        st.session_state["edit_expenses"].append({"name": "", "amount": 0})
        st.rerun()

    if st.button("Save Changes to JSON"):
        # recompute totals
        t_sales = compute_total_sales(edited_daily)
        p_amt = compute_profit(t_sales, float(new_profit_pct))
        t_exp = compute_total_expenses(st.session_state["edit_expenses"])
        rem = p_amt - t_exp
        # update record dict
        ed["shop_name"] = new_shop
        ed["tagline"] = new_tagline
        ed["profit_pct"] = float(new_profit_pct)
        ed["total_sales"] = int(t_sales)
        ed["profit_amount"] = float(p_amt)
        ed["total_expenses"] = float(t_exp)
        ed["remaining_profit"] = float(rem)
        ed["daily_sales"] = edited_daily
        ed["expenses"] = st.session_state["edit_expenses"].copy()
        # overwrite file
        edit_path = st.session_state["editing_file"]
        with open(edit_path, "w", encoding="utf-8") as f:
            json.dump(ed, f, ensure_ascii=False, indent=2)
        st.success(f"Record updated: {edit_path}")
        # clear editing state
        del st.session_state["editing_data"]
        del st.session_state["editing_file"]
        if "edit_expenses" in st.session_state:
            del st.session_state["edit_expenses"]
        st.rerun()


st.markdown(
    """
    <div style="text-align:center; font-size:0.9rem; color:gray;">
        Records saved as JSON + PDF in the <b>'records/'</b> folder.<br>
        On mobile, use the Download buttons to save files to your device's Downloads folder.<br><br>
        Developed by <b>Muhammad Maaz</b>. © 2025.
    </div>
    """,
    unsafe_allow_html=True
)

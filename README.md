# 🏪 AR Monthly Shop Expense App  
> A clean, mobile-friendly Streamlit app to calculate and manage your monthly shop sales, profit, and expenses — complete with PDF reports and charts.

![Streamlit](https://img.shields.io/badge/Framework-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- 📅 **Automatic Month & Year Selection**  
  Automatically detects days in the selected month.

- 💰 **Daily Sales Tracker**  
  Enter daily sales (whole numbers only) and get total monthly sales.

- 📊 **Profit Calculation**  
  Set a profit percentage to auto-calculate total and remaining profits.

- 🧾 **Dynamic Expense Fields**  
  Add unlimited expenses (name + amount). Default: 1 expense field.

- 📈 **Pie Chart Visualization**  
  Instantly view a profit vs. expense chart.

- 📄 **Downloadable PDF Report**  
  Generate a beautiful report with your shop’s data (transparent background).

- 🔐 **4-Digit PIN Protection**  
  App requires a PIN on startup for secure access.

- 💾 **Local Storage (No Cloud)**  
  Saves reports as JSON + PDF directly to your device’s storage.

- 🌞 **Clean Light Theme**  
  Minimal, responsive, and modern design.

---

## 🧰 Tech Stack

| Tool | Purpose |
|------|----------|
| **Python** | Core app logic |
| **Streamlit** | Web UI |
| **Pandas** | Data handling |
| **Matplotlib** | Pie charts |
| **ReportLab** | PDF generation |
| **Pillow** | Image management |

---

## ⚙️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/monthly-expense.git
cd monthly-expense

# 2. Install dependencies
pip install streamlit pandas matplotlib reportlab pillow

# 3. Run the app
streamlit run app.py

<!--
SEO Keywords:
Streamlit expense tracker, monthly profit calculator, Python finance app, sales tracking, 
shop expense management, business profit app, Streamlit PDF generator, local storage app
-->

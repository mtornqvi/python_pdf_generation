import datetime
import importlib.util
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Get current date
today = datetime.date.today()
date_str = today.strftime("%Y-%m-%d")   # e.g. 2025-09-05

# Define file path
data_file = Path("raw_data") / f"{date_str}.py"

if not data_file.exists():
    raise FileNotFoundError(f"Data file not found: {data_file}")

# Load items dynamically
spec = importlib.util.spec_from_file_location("items_module", data_file)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
items = module.items

# Sort items alphabetically
items_sorted = sorted(items, key=lambda x: x[0])

# Create PDF in results folder
results_dir = Path("results")
results_dir.mkdir(exist_ok=True)  # Create the directory if it doesn't exist
filename = results_dir / f"receipt_{date_str}_alphabetical.pdf"
doc = SimpleDocTemplate(filename, pagesize=A4)
elements = []

styles = getSampleStyleSheet()
title_style = ParagraphStyle(name="Title", fontSize=16, alignment=1, fontName="Helvetica-Bold")
elements.append(Paragraph(f"Ostoskuitti {date_str} – tuotteet aakkosjärjestyksessä", title_style))
elements.append(Spacer(1, 12))

data = [["Tuote", "Määrä", "Hinta"]] + items_sorted
table = Table(data, colWidths=[250, 100, 100])
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
]))

elements.append(table)
doc.build(elements)

print(f"PDF created: {filename}")

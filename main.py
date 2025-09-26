import datetime
import importlib.util
import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from preprocess import process_raw_file

# Get current date
today = datetime.date.today()
date_str = today.strftime("%Y-%m-%d")   # e.g. 2025-09-05
# Format date in Finnish style (d.m.YYYY) without leading zeros
date_str_fi = f"{today.day}.{today.month}.{today.year}"  # e.g. 26.9.2025

# Check for raw file first
raw_file = Path("raw_data") / f"{date_str}.raw"
if raw_file.exists():
    process_raw_file(raw_file)

# Define Python data file path
data_file = Path("raw_data") / f"{date_str}.py"

if not data_file.exists():
    raise FileNotFoundError(f"Data file not found: {data_file}")

# Load items dynamically
spec = importlib.util.spec_from_file_location("items_module", data_file)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
items = module.items

# Function to extract price as float
def extract_price(price_str: str) -> float:
    return float(price_str.replace(" €", "").replace(",", "."))

# Function to format quantity
def format_quantity(qty: str) -> str:
    # If quantity is just "1", add "kpl"
    if qty == "1":
        return "1 kpl"
    
    # Convert KPL and KG to lowercase
    qty_lower = qty.replace("KPL", "kpl").replace("KG", "kg")
    
    # If there's a number followed by a space and unit, ensure the unit is lowercase
    if ' ' in qty_lower:
        number, unit = qty_lower.split(' ', 1)
        return f"{number} {unit.lower()}"
    
    return qty_lower

# Split items into material and non-material items
non_material_patterns = [
    r"^TOIMITUSMAKSU.*",
    r"^PANTTI.*",
    r"^VERKKOK\.PAKKAUSMATERIAALIMAKSU.*"
]

material_items = []
non_material_items = []

for item in items:
    is_non_material = any(re.match(pattern, item[0]) for pattern in non_material_patterns)
    if is_non_material:
        non_material_items.append(item)
    else:
        material_items.append(item)

# Sort both lists alphabetically and format quantities
material_items_sorted = [(item[0], format_quantity(item[1]), item[2]) for item in sorted(material_items, key=lambda x: x[0])]
non_material_items_sorted = [(item[0], format_quantity(item[1]), item[2]) for item in sorted(non_material_items, key=lambda x: x[0])]

# Calculate totals
material_total = sum(extract_price(item[2]) for item in material_items)
non_material_total = sum(extract_price(item[2]) for item in non_material_items)
grand_total = material_total + non_material_total

# Create PDF in results folder
results_dir = Path("results")
results_dir.mkdir(exist_ok=True)  # Create the directory if it doesn't exist
filename = str(results_dir / f"ostoskuitti_{date_str}_aakkosjarjestyksessa.pdf")  # Convert Path to string
doc = SimpleDocTemplate(filename, pagesize=A4)
elements = []

styles = getSampleStyleSheet()
title_style = ParagraphStyle(name="Title", fontSize=16, alignment=1, fontName="Helvetica-Bold")
subtitle_style = ParagraphStyle(name="Subtitle", fontSize=14, alignment=1, fontName="Helvetica-Bold", spaceBefore=20)
total_style = ParagraphStyle(name="Total", fontSize=12, alignment=2, fontName="Helvetica-Bold", spaceBefore=10)

elements.append(Paragraph(f"Ostoskuitti {date_str_fi}", title_style))
elements.append(Spacer(1, 12))

# Material items table
elements.append(Paragraph("Tuotteet", subtitle_style))
elements.append(Spacer(1, 15))  # Add margin after the subtitle
data = [["Tuote", "Määrä", "Hinta"]] + material_items_sorted
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
elements.append(Paragraph(f"Tuotteet yhteensä: {material_total:.2f} €".replace(".", ","), total_style))

# Non-material items table
if non_material_items:
    elements.append(Paragraph("Muut maksut", subtitle_style))
    elements.append(Spacer(1, 15))  # Add margin after the subtitle
    data = [["Kuvaus", "Määrä", "Hinta"]] + non_material_items_sorted
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
    elements.append(Paragraph(f"Muut maksut yhteensä: {non_material_total:.2f} €".replace(".", ","), total_style))

# Grand total
elements.append(Spacer(1, 20))
elements.append(Paragraph(f"Loppusumma: {grand_total:.2f} €".replace(".", ","), total_style))

doc.build(elements)

print(f"PDF luotu: {filename}")

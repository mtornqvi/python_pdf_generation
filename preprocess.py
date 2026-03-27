import re
from pathlib import Path
from typing import List, Tuple

def extract_items(raw_content: str) -> List[Tuple[str, str, str]]:
    """
    Extract items from raw receipt content.
    Returns list of tuples: (product_name, quantity, price)
    """
    items = []
    lines = raw_content.split('\n')
    
    # Skip header until the dashed line
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('-' * 20):
            start_idx = i + 1
            break
    
    current_item = None
    for line in lines[start_idx:]:
        # Skip empty lines and the final summary section
        if not line.strip() or line.startswith('-' * 20):
            continue
        
        if 'VÄLISUMMA' in line or 'YHTEENSÄ' in line:
            break

        # Ignore indented campaign detail rows like:
        # "  NORM.                      17,90"
        # "  ALENNUS                   -10,10"
        if re.match(r'^\s+(?:NORM\.|ALENNUS)\s+-?\d+,\d{2}\s*$', line):
            continue
            
        # Match only top-level rows (no leading indentation) that end with a price.
        # This avoids treating indented helper rows as separate items.
        price_match = re.match(r'^\S.*\s+(-?\d+,\d{2})\s*$', line)
        if price_match:
            product = line[:line.rfind(price_match.group(1))].strip()
            price = price_match.group(1) + ' €'
            current_item = (product, "1", price)
            items.append(current_item)
        else:
            # Check for quantity information
            qty_match = re.match(r'\s+(\d+(?:,\d+)?\s+(?:KG|KPL))\s+(\d+,\d{2})\s+€/(?:KG|KPL)', line)
            if qty_match and current_item:
                # Update the previous item's quantity
                product, _, price = current_item
                items[-1] = (product, qty_match.group(1), price)
                
    return items

def process_raw_file(raw_file: Path) -> None:
    """
    Process a raw receipt file and save it as a Python file.
    """
    # Read the raw file
    with open(raw_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract items
    items = extract_items(content)
    
    # Create Python file content
    date_str = raw_file.stem  # Get filename without extension
    py_content = [f'# Receipt data {date_str}']
    py_content.append('items = [')
    
    # Format items as Python tuples
    for item in items:
        py_content.append(f'    {repr(item)},')
    
    py_content.append(']')
    py_content.append('')  # Add final newline
    
    # Save as Python file
    py_file = raw_file.parent / f"{date_str}.py"
    with open(py_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(py_content))
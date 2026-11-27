import pdfplumber
import re

pdf_path = "input/drawing.pdf"
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    words = page.extract_words()

    print(f"Page: {page.width:.0f} x {page.height:.0f}\n")

    # Print ALL words sorted top-to-bottom, left-to-right
    # Group words that are on the same "line" (within 5px vertically)
    sorted_words = sorted(words, key=lambda w: (round(w["top"] / 5) * 5, w["x0"]))

    current_y = None
    line = []
    lines = []
    for w in sorted_words:
        y = round(w["top"] / 5) * 5
        if current_y is None or abs(y - current_y) <= 5:
            line.append(w)
            current_y = y
        else:
            if line:
                lines.append(line)
            line = [w]
            current_y = y
    if line:
        lines.append(line)

    # Print lines that look like they could be workpoint data
    # (numbers, coordinates, WP labels, etc.)
    print("=== LINES WITH NUMERIC/COORDINATE CONTENT ===\n")
    for line in lines:
        text = " | ".join(w["text"] for w in line)
        # Check if line has numbers that look like coordinates or WP ids
        has_big_num = any(re.match(r'^\d{5,}', w["text"]) for w in line)
        has_wp = any(re.match(r'^WP\d*$|^W\.P\.|^WORKPOINT', w["text"].upper()) for w in line)
        has_decimal = any(re.match(r'^\d+\.\d+$', w["text"]) for w in line)
        if has_big_num or has_wp or len(line) >= 3 and has_decimal:
            y0 = line[0]["top"]
            x0 = line[0]["x0"]
            print(f"[y={y0:.0f}, x={x0:.0f}] {text}")

    print("\n\n=== ALL LINES (full dump) ===\n")
    for line in lines:
        y0 = line[0]["top"]
        x0 = line[0]["x0"]
        text = " | ".join(w["text"] for w in line)
        print(f"[y={y0:.0f}] {text}")

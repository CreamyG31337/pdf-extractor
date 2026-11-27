import pymupdf

pdf_path = "input/drawing.pdf"
doc = pymupdf.open(pdf_path)
page = doc[0]

print(f"Page rect: {page.rect}")
print(f"Rotation: {page.rotation}")

# Get all text with detailed positioning
blocks = page.get_text("dict", flags=pymupdf.TEXT_PRESERVE_WHITESPACE)["blocks"]
print(f"\nTotal text blocks: {len(blocks)}\n")

# Look for workpoint-related content
for b in blocks:
    if b["type"] != 0:  # skip non-text
        continue
    for line in b["lines"]:
        for span in line["spans"]:
            txt = span["text"].strip()
            if txt and ("WP" in txt.upper() or "WORKPOINT" in txt.upper() or
                        "NORTH" in txt.upper() or "EASTING" in txt.upper() or
                        "ELEV" in txt.upper()):
                print(f"HIT [{span['bbox']}]: {txt!r}")

print("\n=== ALL TEXT BLOCKS ===")
for b in blocks:
    if b["type"] != 0:
        continue
    bbox = b["bbox"]
    text_lines = []
    for line in b["lines"]:
        line_text = " ".join(s["text"] for s in line["spans"]).strip()
        if line_text:
            text_lines.append(line_text)
    if text_lines:
        full = " / ".join(text_lines)
        print(f"[{bbox[0]:.0f},{bbox[1]:.0f} -> {bbox[2]:.0f},{bbox[3]:.0f}] {full[:200]}")

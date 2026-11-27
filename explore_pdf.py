import pdfplumber

pdf_path = "input/drawing.pdf"
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    words = page.extract_words()

    # Print all words sorted by y then x to read the document naturally
    print(f"Page size: {page.width:.0f} x {page.height:.0f}")
    print(f"Total words: {len(words)}\n")

    # Find all words near "WORK" vertically
    for w in words:
        if "WORK" in w["text"].upper() or w["text"].upper().startswith("WP"):
            cx = (w["x0"] + w["x1"]) / 2
            cy = (w["top"] + w["bottom"]) / 2
            nearby = [ww for ww in words if abs((ww["top"] + ww["bottom"]) / 2 - cy) < 60]
            label = w["text"]
            print(f"Near '{label}' at y={cy:.0f}:")
            for nw in sorted(nearby, key=lambda x: x["x0"]):
                print(f"  [{nw['x0']:.0f},{nw['top']:.0f}] {nw['text']}")
            print()

    # Print all tables
    tables = page.extract_tables()
    print(f"\nTables found: {len(tables)}")
    for i, t in enumerate(tables):
        print(f"\nTable {i+1}:")
        for row in t:
            print(row)

    # Print all text in coordinate order (top-to-bottom, left-to-right)
    print("\n\n=== ALL WORDS BY POSITION ===")
    for w in sorted(words, key=lambda x: (round(x["top"] / 20) * 20, x["x0"])):
        print(f"[{w['x0']:.0f},{w['top']:.0f}] {w['text']}")

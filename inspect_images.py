import pymupdf

pdf_path = "input/drawing.pdf"
doc = pymupdf.open(pdf_path)
page = doc[0]

# List all embedded images
images = page.get_images(full=True)
print(f"Embedded images: {len(images)}")
for img in images:
    xref = img[0]
    info = doc.extract_image(xref)
    print(f"  xref={xref}, size={info['width']}x{info['height']}, colorspace={info['colorspace']}, ext={info['ext']}")

# Check if the page IS mostly a raster image vs vector
print(f"\nPage drawings (vector paths): {len(page.get_drawings())}")
print(f"Page text chars: {len(page.get_text())}")

# Render a cropped region to image to inspect the workpoints table
# First render the whole page thumbnail
mat = pymupdf.Matrix(0.3, 0.3)
clip = None
pix = page.get_pixmap(matrix=mat, clip=clip)
pix.save("page_thumbnail.png")
print("\nSaved page_thumbnail.png (30% scale)")

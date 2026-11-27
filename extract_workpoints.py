"""
Extract workpoints table from a PDF engineering drawing using a vision API.
Handles PDFs where the table is a raster image (not selectable text).

Usage:
    uv run python extract_workpoints.py <pdf_file> [output_csv]
    uv run python extract_workpoints.py "input/drawing.pdf"
    uv run python extract_workpoints.py "input/drawing.pdf" output/workpoints.csv

Use --provider openai-compatible for OpenAI or an OpenAI-compatible service.
"""

import argparse
import base64
import csv
import json
import os
import re
from pathlib import Path
from typing import Any

import anthropic
import pymupdf
from openai import OpenAI


EXTRACTION_PROMPT = (
    "This is an engineering drawing. Find the workpoints table "
    "(columns: WORKPOINT or WP label, EASTING, NORTHING). "
    "Extract every row and return ONLY a JSON array, no explanation. "
    "Format: [{\"workpoint\": \"WP-001\", \"easting\": 1000.000, "
    "\"northing\": 2000.000}, ...]. Include all workpoints exactly as shown."
)


def render_pdf_page(pdf_path: str, page_index: int = 0, dpi: int = 200) -> bytes:
    """Render a PDF page to PNG bytes at the given DPI."""
    doc = pymupdf.open(pdf_path)
    page = doc[page_index]
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    return pix.tobytes("png")


def parse_workpoints_response(text: str) -> list[dict]:
    """Parse the JSON array returned by a vision provider."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON array found in response:\n{text}")

    return json.loads(match.group())


def extract_with_anthropic(image_bytes: bytes, client: anthropic.Anthropic, model: str) -> list[dict]:
    """Send the page image to Anthropic and extract the workpoints table."""
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": EXTRACTION_PROMPT,
                    },
                ],
            }
        ],
    )

    text = next(b.text for b in response.content if b.type == "text")
    return parse_workpoints_response(text)


def extract_with_openai_compatible(image_bytes: bytes, client: OpenAI, model: str) -> list[dict]:
    """Send the page image to OpenAI or an OpenAI-compatible vision API."""
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": EXTRACTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            }
        ],
        max_tokens=4096,
    )
    text = response.choices[0].message.content
    if not text:
        raise ValueError("The vision provider returned an empty response")
    return parse_workpoints_response(text)


def extract_workpoints_from_image(
    image_bytes: bytes, provider: str, client: Any, model: str
) -> list[dict]:
    """Extract workpoints using the selected vision provider."""
    if provider == "anthropic":
        return extract_with_anthropic(image_bytes, client, model)
    if provider == "openai-compatible":
        return extract_with_openai_compatible(image_bytes, client, model)
    raise ValueError(f"Unsupported provider: {provider}")


def write_csv(workpoints: list[dict], output_path: str) -> None:
    """Write workpoints to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["WORKPOINT", "EASTING", "NORTHING"])
        for wp in workpoints:
            writer.writerow([wp["workpoint"], wp["easting"], wp["northing"]])
    print(f"Wrote {len(workpoints)} workpoints to {output_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_file")
    parser.add_argument("output_csv", nargs="?")
    parser.add_argument(
        "--provider",
        choices=("anthropic", "openai-compatible"),
        default=os.getenv("WORKPOINT_PROVIDER", "anthropic"),
        help="Vision provider to use (default: %(default)s)",
    )
    args = parser.parse_args()

    pdf_path = args.pdf_file
    output_csv = args.output_csv or Path("output") / f"{Path(pdf_path).stem}_workpoints.csv"

    if not Path(pdf_path).exists():
        print(f"Error: {pdf_path} not found")
        return 1

    print(f"Rendering PDF: {pdf_path}")
    image_bytes = render_pdf_page(pdf_path, dpi=200)
    print(f"Rendered {len(image_bytes):,} bytes")

    if args.provider == "anthropic":
        model = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7")
        client = anthropic.Anthropic()
    else:
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL") or None,
        )

    print(f"Extracting workpoints via {args.provider} vision API...")
    workpoints = extract_workpoints_from_image(image_bytes, args.provider, client, model)

    print(f"Found {len(workpoints)} workpoints:")
    for wp in workpoints:
        print(f"  {wp['workpoint']}: E={wp['easting']}, N={wp['northing']}")

    write_csv(workpoints, output_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

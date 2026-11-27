# PDF Workpoint Extractor

Extract workpoint coordinates from engineering-drawing PDFs whose workpoint table is stored as a raster image or is otherwise difficult to read with ordinary PDF text extraction.

The main script renders the first PDF page to a PNG image, sends that image to a vision API, and writes the extracted workpoints to a CSV file. It supports Anthropic and OpenAI-compatible providers.

## Requirements

- Python 3.14 or newer
- [`uv`](https://docs.astral.sh/uv/)
- An API key for the selected vision provider

## Setup

On the survey PC the dependencies are already in the shared `C:\Projects\.venv`; run
`C:\Projects\.venv\Scripts\python.exe extract_workpoints.py ...` (see `C:\Projects\TOOLS.md`). Elsewhere, install
the project dependencies with `uv`:

```powershell
uv sync
```

For Anthropic:

```powershell
$env:ANTHROPIC_API_KEY = "your-api-key"
```

For OpenAI or an OpenAI-compatible service:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
$env:OPENAI_MODEL = "gpt-4o"
```

For a compatible gateway, also set its endpoint:

```powershell
$env:OPENAI_BASE_URL = "https://your-service.example/v1"
```

Do not commit the API key or place it in source control.

## Usage

Place source PDFs in `input/` and generated CSVs in `output/`. Both folders are ignored by Git.

Run the extractor with an input PDF:

```powershell
uv run python extract_workpoints.py "input/drawing.pdf"
```

When no output path is supplied, the script writes `output/<input-name>_workpoints.csv`. Provide a path explicitly when needed:

```powershell
uv run python extract_workpoints.py "input/drawing.pdf" "output/workpoints.csv"
```

The script prints the extracted rows and reports the number of workpoints written.

### Select a provider

Anthropic remains the default for compatibility with the original script:

```powershell
uv run python extract_workpoints.py "drawing.pdf" --provider anthropic
```

Use the OpenAI-compatible adapter for OpenAI or a compatible service:

```powershell
uv run python extract_workpoints.py "drawing.pdf" --provider openai-compatible
```

The provider can also be selected with `WORKPOINT_PROVIDER`. The OpenAI-compatible adapter expects a chat-completions API that accepts a base64 PNG data URL as an image and returns text containing the JSON array.

## Output

The generated CSV contains one row per workpoint with this header:

```csv
WORKPOINT,EASTING,NORTHING
WP-001,1000.000,2000.000
WP-002,1001.250,2002.500
```

Coordinates are returned by the vision model as shown in the drawing. Review the CSV against the source drawing before using it for surveying, construction, or other operational work.

## Extraction pipeline

1. Open the input PDF with PyMuPDF.
2. Render page 1 at 200 DPI as PNG bytes.
3. Send the image to the selected vision provider with instructions to find the `WORKPOINT`, `EASTING`, and `NORTHING` columns.
4. Parse the model response as a JSON array.
5. Write the results to CSV.

The Anthropic model defaults to `claude-opus-4-7` and can be changed with `ANTHROPIC_MODEL`. The OpenAI-compatible model defaults to `gpt-4o` and can be changed with `OPENAI_MODEL`. The current implementation processes only the first page; it does not automatically search later pages or validate coordinate values against PDF geometry.

## Project files

| File | Purpose |
| --- | --- |
| `extract_workpoints.py` | Main extraction CLI and CSV writer |
| `explore_pdf.py` | Inspect selectable text and tables with `pdfplumber` |
| `explore_fitz.py` | Inspect PDF text blocks and positions with PyMuPDF |
| `find_workpoints.py` | Search extracted PDF text for likely workpoint rows |
| `inspect_images.py` | Inspect embedded images and create a page thumbnail |
| `main.py` | Minimal starter entry point; not part of the extraction workflow |
| `input/` | Git-ignored source PDFs |
| `output/` | Git-ignored generated CSV files |

The exploratory scripts use `input/drawing.pdf` as their sample path. Update their `pdf_path` variable before using them with another drawing.

## Troubleshooting

### Provider API key is missing

Set the environment variable for the selected provider in the shell running `uv run`, then run the command again. A Claude.ai subscription and a ChatGPT subscription do not automatically provide API access; those APIs require their own provider accounts and billing.

### The selected model cannot read images

Choose a vision-capable model. The OpenAI-compatible adapter requires an endpoint that supports the OpenAI chat-completions image format; an arbitrary text-only endpoint will not work.

### No JSON array found in response

The model response did not contain the expected JSON array. Check that the PDF page contains a readable workpoint table and that the table is visible in the first page render.

### The extracted values are incomplete or incorrect

This project uses vision-based extraction, so results should be treated as an automated first pass. Confirm the rows and coordinates against the drawing, and increase the render DPI or adjust the extraction prompt in `extract_workpoints.py` for drawings with small or low-contrast tables.

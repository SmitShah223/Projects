# AI Study Notes Generator

> **Hackathon Project** — Generative AI-powered study notes PDF generator  
> **Stack:** Python · OpenAI GPT · FPDF2 · PyMuPDF · Tkinter · React (Material-UI)  
> **Output:** Styled, formatted PDF with Proxima Nova fonts · Optional AES-256 encryption

---

## Overview

An AI-powered tool that takes a **subject → module → subtopics** as input, calls **OpenAI GPT** to generate detailed 500-word explanations for each subtopic, and renders the output as a **professionally styled PDF** using custom Proxima Nova fonts.

Two interfaces:
- **Desktop GUI** — Tkinter app (`src/gui/app.py`)
- **Web UI** — React + Material-UI frontend (`src/frontend/`)

Optional feature: **AES-256 PDF encryption** locked to the generating machine's MAC address — prevents the PDF from being opened on other devices.

---

## Features

| Feature | Detail |
|---|---|
| AI content generation | OpenAI GPT (gpt-3.5-turbo) generates 500-word notes per subtopic |
| Multiple modules | Add as many modules/chapters as needed before generating |
| Styled PDF output | Proxima Nova fonts · bold module headings · italic red subtopics · justified body |
| Token tracking | Prints token count + estimated cost after generation |
| AES-256 encryption | Optional — PDF locked to machine MAC address (Caesar +3 key derivation) |
| Desktop GUI | Tkinter app with add/remove modules, output path picker |
| React Web UI | Material-UI form with dynamic module/subtopic rows |

---

## Repository Structure

```
GENERATIVE AI/
├── src/
│   ├── backend/
│   │   └── generator.py          # Core engine — GPT → FPDF2 PDF generation
│   ├── gui/
│   │   └── app.py                # Tkinter desktop GUI
│   ├── utils/
│   │   ├── pdf_encrypt.py        # AES-256 PDF encryption/decryption (MAC-locked)
│   │   └── open_pdf.py           # Cross-platform PDF opener
│   └── frontend/                 # React web UI
│       ├── src/
│       │   ├── App.js             # Main React component (Material-UI form)
│       │   ├── index.js
│       │   └── styles/
│       ├── public/
│       └── package.json
│
├── fonts/                        # Proxima Nova font files (not committed — see note)
│   ├── proximanova.ttf
│   ├── proximanovabold.otf
│   └── proximanovaitalics.otf
│
├── .env.example                  # Copy to .env and add your OpenAI API key
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up API key

```bash
cp .env.example .env
# Edit .env and set: OPENAI_API_KEY=sk-...
```

### 3. Add fonts

Place these font files in the `fonts/` folder:
- `proximanova.ttf`
- `proximanovabold.otf`
- `proximanovaitalics.otf`

(Free alternatives: use `DejaVu` or `Arial` by changing font names in `generator.py`)

### 4. Run — Desktop GUI

```bash
python3 src/gui/app.py
```

### 5. Run — Command Line

```python
from src.backend.generator import main
main("Machine Learning", "Dimensionality Reduction", ["PCA", "NMF", "ICA"])
```

### 6. Run — React Web UI

```bash
cd src/frontend
npm install
npm start
# Open http://localhost:3000
```

---

## PDF Encryption

The encryption utility derives an AES-256 key from the machine's MAC address:

```python
from src.utils.pdf_encrypt import encrypt_pdf, decrypt_pdf

encrypt_pdf("output.pdf", "encrypted.pdf")   # lock to this machine
decrypt_pdf("encrypted.pdf", "plain.pdf")    # only works on same machine
```

The encryption key is: MAC address with each character's ASCII value shifted by +3.

---

## Generated PDF Style

- **Subject title** — 40pt bold, centred
- **Module heading** — 15pt bold, left-aligned, blue underline
- **Subtopic heading** — 12pt italic, red
- **Body text** — 10pt regular, justified, latin-1 encoded

"""
backend/generator.py — Core AI study notes generation engine.

Takes subject → module → subtopics, calls OpenAI GPT,
and generates a formatted PDF with styled Proxima Nova fonts.

Usage:
    from backend.generator import main
    main("Machine Learning", "Dimensionality Reduction", ["PCA", "NMF", "ICA"])

Or run directly:
    python3 src/backend/generator.py

Dependencies:
    pip install openai fpdf2 tiktoken python-dotenv
"""

import os
import tiktoken
from fpdf import FPDF
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# ─── Font paths (relative to project root) ────────────────────────────────────
FONT_REGULAR = os.path.join(os.path.dirname(__file__), "../../fonts/proximanova.ttf")
FONT_BOLD    = os.path.join(os.path.dirname(__file__), "../../fonts/proximanovabold.otf")
FONT_ITALIC  = os.path.join(os.path.dirname(__file__), "../../fonts/proximanovaitalics.otf")

tokens_count = 0
pdf = None
width  = 190
height = 10


def generate_study_notes(input_text: str) -> list[str]:
    """
    Call OpenAI GPT to generate 500-word study notes for a given topic.
    Returns a list of strings (one per completion choice).
    """
    response = openai.ChatCompletion.create(
        model    = "gpt-3.5-turbo",    # Updated from deprecated text-davinci-003
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert academic tutor. Generate detailed, well-structured "
                    "study notes in plain text that is compatible with PDF rendering. "
                    "Do not use markdown symbols like ** or ##."
                )
            },
            {"role": "user", "content": input_text}
        ],
        temperature = 0.2,
        max_tokens  = 1000,
    )
    return [choice["message"]["content"].strip() for choice in response["choices"]]


def num_tokens_from_string(string: str, encoding_name: str = "gpt2") -> int:
    """Returns the number of tokens in a text string."""
    encoding  = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(string))


def pdf_generator(modules: str, subtopics: list[str], subject: str):
    """
    Render one module section into the PDF.
    - Module title: bold blue, underlined
    - Subtopic headings: italic red
    - Body: regular black, justified
    """
    global tokens_count, pdf

    # ── Module heading ─────────────────────────────────────────────────────────
    pdf.set_font("ProximaNova-B", size=15)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(w=width, h=height, align='L', new_x="LMARGIN", new_y="NEXT", txt=modules + " :")

    # Blue underline beneath the module title
    pdf.set_line_width(0.2)
    pdf.set_draw_color(0, 0, 200)
    x          = pdf.get_x()
    y          = pdf.get_y()
    text_width = pdf.get_string_width(modules + " :")
    pdf.line(x, y - 1, x + text_width, y - 1)

    # ── Subtopics ──────────────────────────────────────────────────────────────
    for subtopic in subtopics:
        subtopic = subtopic.strip()

        # Subtopic heading — italic red
        pdf.set_text_color(255, 0, 0)
        pdf.set_font("ProximaNova-I", size=12)
        pdf.multi_cell(w=width, h=height, align='L', new_x="LMARGIN", new_y="NEXT", txt=subtopic + " :")

        # Build prompt
        prompt = (
            f"In 500 words and in detail explain what is '{subtopic}' in '{modules}' "
            f"in '{subject}'. Provide code examples only if directly relevant. "
            f"If there are important sub-types, methods, or variants, cover those too. "
            f"Write in plain text only — no markdown symbols."
        )
        notes = generate_study_notes(prompt)

        # Body text — regular black, justified
        pdf.set_font("ProximaNova", size=10)
        pdf.set_text_color(0, 0, 0)
        for note in notes:
            encoded = note.encode("latin-1", "ignore").decode("latin-1")
            pdf.multi_cell(w=width, h=4, align='J', new_x="LMARGIN", new_y="NEXT", txt=encoded)
            tokens_count += num_tokens_from_string(encoded)

    pdf.ln(5)


def main(subject: str, modules: str, subtopics: list[str], output_path: str = "output.pdf"):
    """
    Generate a study notes PDF for the given subject/module/subtopics.

    Args:
        subject     : e.g. "Machine Learning"
        modules     : e.g. "Dimensionality Reduction"
        subtopics   : e.g. ["PCA", "NMF", "ICA"]
        output_path : output PDF filename (default: output.pdf)
    """
    global pdf, tokens_count
    tokens_count = 0

    pdf = FPDF()
    pdf.add_page()

    # Register Proxima Nova fonts
    pdf.add_font("ProximaNova",   fname=FONT_REGULAR)
    pdf.add_font("ProximaNova-B", fname=FONT_BOLD)
    pdf.add_font("ProximaNova-I", fname=FONT_ITALIC)

    # Subject title
    pdf.set_font("ProximaNova-B", size=40)
    pdf.multi_cell(w=width, h=height, align='C', new_x="LMARGIN", new_y="NEXT", txt=subject)
    pdf.ln(10)

    # Generate content
    pdf_generator(modules, subtopics, subject)

    pdf.output(output_path)

    cost = round((tokens_count / 1000) * 0.002, 4)
    print(f"[DONE] Tokens used: {tokens_count}")
    print(f"[DONE] Approximate cost: ${cost}")
    print(f"[DONE] PDF saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    main(
        subject     = "Machine Learning",
        modules     = "Dimensionality Reduction",
        subtopics   = ["PCA", "NMF", "ICA"],
        output_path = "output.pdf"
    )

"""
gui/app.py — Tkinter Desktop GUI for Study Notes Generator.

This is the final, clean version of the desktop app
(consolidates masti.py, masti2.py, masti3.py from the hackathon).

Features:
  - Enter subject name
  - Add multiple modules/chapters with comma-separated subtopics
  - Click "Generate PDF" → calls generator.py → creates styled PDF
  - Optional AES-256 encryption of output PDF (MAC-address locked)

Usage:
    python3 src/gui/app.py

Dependencies:
    pip install openai fpdf2 tiktoken pymupdf python-dotenv
"""

import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import threading
import os
import sys

# Allow running as standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.generator import main as generate_pdf
from utils.pdf_encrypt  import encrypt_pdf


class StudyNotesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Study Notes Generator")
        self.geometry("700x520")
        self.resizable(True, True)
        self.configure(bg="#f5f5f5")

        self.modules = []   # list of {"topic": str, "subtopics": [str]}

        self._build_ui()

    def _build_ui(self):
        # ── Title ──────────────────────────────────────────────────────────────
        tk.Label(self, text="AI Study Notes Generator",
                 font=("Helvetica", 18, "bold"), bg="#f5f5f5", fg="#333"
                 ).grid(row=0, column=0, columnspan=4, pady=(16, 8))

        # ── Subject ────────────────────────────────────────────────────────────
        tk.Label(self, text="Subject:", bg="#f5f5f5").grid(
            row=1, column=0, sticky="e", padx=10, pady=6)
        self.subject_entry = tk.Entry(self, width=40, font=("Helvetica", 11))
        self.subject_entry.grid(row=1, column=1, columnspan=2, sticky="w", pady=6)

        # ── Module / Chapter ──────────────────────────────────────────────────
        tk.Label(self, text="Module / Chapter:", bg="#f5f5f5").grid(
            row=2, column=0, sticky="e", padx=10, pady=6)
        self.module_entry = tk.Entry(self, width=40, font=("Helvetica", 11))
        self.module_entry.grid(row=2, column=1, columnspan=2, sticky="w", pady=6)

        # ── Subtopics ─────────────────────────────────────────────────────────
        tk.Label(self, text="Subtopics (comma-separated):", bg="#f5f5f5").grid(
            row=3, column=0, sticky="e", padx=10, pady=6)
        self.subtopic_entry = tk.Entry(self, width=40, font=("Helvetica", 11))
        self.subtopic_entry.grid(row=3, column=1, columnspan=2, sticky="w", pady=6)

        # ── Add Module button ─────────────────────────────────────────────────
        tk.Button(self, text="+ Add Module", command=self._add_module,
                  bg="#4a90d9", fg="white", font=("Helvetica", 10, "bold"),
                  relief="flat", padx=10
                  ).grid(row=4, column=1, sticky="w", pady=6)

        # ── Module list ───────────────────────────────────────────────────────
        tk.Label(self, text="Added Modules:", bg="#f5f5f5",
                 font=("Helvetica", 10, "bold")).grid(
            row=5, column=0, sticky="ne", padx=10, pady=6)

        self.module_listbox = tk.Listbox(self, height=6, width=60,
                                          font=("Helvetica", 9))
        self.module_listbox.grid(row=5, column=1, columnspan=2, pady=6)

        tk.Button(self, text="Remove Selected", command=self._remove_module,
                  bg="#e74c3c", fg="white", font=("Helvetica", 9),
                  relief="flat"
                  ).grid(row=6, column=1, sticky="w", pady=2)

        # ── Encryption toggle ─────────────────────────────────────────────────
        self.encrypt_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Encrypt PDF (AES-256, MAC-locked)",
                       variable=self.encrypt_var, bg="#f5f5f5"
                       ).grid(row=7, column=1, sticky="w", pady=4)

        # ── Output path ───────────────────────────────────────────────────────
        tk.Label(self, text="Output file:", bg="#f5f5f5").grid(
            row=8, column=0, sticky="e", padx=10)
        self.output_var = tk.StringVar(value="study_notes.pdf")
        tk.Entry(self, textvariable=self.output_var, width=32,
                 font=("Helvetica", 10)).grid(row=8, column=1, sticky="w")
        tk.Button(self, text="Browse", command=self._browse_output,
                  relief="flat"
                  ).grid(row=8, column=2, sticky="w", padx=4)

        # ── Generate button ───────────────────────────────────────────────────
        self.gen_btn = tk.Button(
            self, text="▶  Generate PDF",
            command=self._start_generation,
            bg="#27ae60", fg="white",
            font=("Helvetica", 12, "bold"),
            relief="flat", padx=14, pady=6
        )
        self.gen_btn.grid(row=9, column=0, columnspan=4, pady=16)

        # ── Status bar ────────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(self, textvariable=self.status_var, bg="#f5f5f5",
                 fg="#555", font=("Helvetica", 9, "italic")
                 ).grid(row=10, column=0, columnspan=4, pady=(0, 10))

    # ── Callbacks ─────────────────────────────────────────────────────────────
    def _add_module(self):
        topic     = self.module_entry.get().strip()
        subtopics = [s.strip() for s in self.subtopic_entry.get().split(",") if s.strip()]

        if not topic:
            messagebox.showerror("Error", "Module name cannot be empty.")
            return
        if not subtopics:
            messagebox.showerror("Error", "Please enter at least one subtopic.")
            return

        self.modules.append({"topic": topic, "subtopics": subtopics})
        display = f"{topic}  →  {', '.join(subtopics)}"
        self.module_listbox.insert(tk.END, display)

        self.module_entry.delete(0, tk.END)
        self.subtopic_entry.delete(0, tk.END)
        self.status_var.set(f"Module '{topic}' added. Total: {len(self.modules)}")

    def _remove_module(self):
        sel = self.module_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.module_listbox.delete(idx)
        removed = self.modules.pop(idx)
        self.status_var.set(f"Removed: {removed['topic']}")

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save PDF as"
        )
        if path:
            self.output_var.set(path)

    def _start_generation(self):
        subject = self.subject_entry.get().strip()
        if not subject:
            messagebox.showerror("Error", "Please enter a subject name.")
            return
        if not self.modules:
            messagebox.showerror("Error", "Please add at least one module.")
            return

        self.gen_btn.configure(state="disabled")
        self.status_var.set("Generating... this may take a few minutes.")
        self.update()

        # Run in background thread so GUI stays responsive
        thread = threading.Thread(target=self._run_generation,
                                   args=(subject,), daemon=True)
        thread.start()

    def _run_generation(self, subject: str):
        output_path = self.output_var.get()
        try:
            for mod in self.modules:
                self.status_var.set(f"Generating: {mod['topic']}...")
                self.update()
                generate_pdf(
                    subject     = subject,
                    modules     = mod["topic"],
                    subtopics   = mod["subtopics"],
                    output_path = output_path,
                )

            if self.encrypt_var.get():
                enc_path = output_path.replace(".pdf", "_encrypted.pdf")
                encrypt_pdf(output_path, enc_path)
                self.status_var.set(f"Done! Encrypted PDF: {enc_path}")
            else:
                self.status_var.set(f"Done! PDF saved: {output_path}")

            messagebox.showinfo("Success",
                f"Study notes PDF generated successfully!\n{output_path}")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set(f"Error: {e}")
        finally:
            self.gen_btn.configure(state="normal")


if __name__ == "__main__":
    app = StudyNotesApp()
    app.mainloop()

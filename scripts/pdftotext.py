import pdfplumber

def pdf_to_txt(pdf_path, txt_path):
    with pdfplumber.open(pdf_path) as pdf, open(txt_path, "w", encoding="utf-8") as out:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                # simple cleanup: strip extra whitespace
                cleaned = "\n".join(line.strip() for line in text.split("\n") if line.strip())
                out.write(cleaned + "\n\n")

if __name__ == "__main__":
    pdf_to_txt("/home/abdulwahab-bhai/personal/tradia_ai_backend/backend/docs/doc-import-declaration-guide.pdf", "importguidepython.txt")
    pdf_to_txt("/home/abdulwahab-bhai/personal/tradia_ai_backend/backend/docs/export_declaration_helpguide.pdf", "exportguidepython.txt")

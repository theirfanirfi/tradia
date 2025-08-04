import PyPDF2

def parse_pdf_to_txt(pdf_path: str, output_txt_path: str):
    """
    Extract text from each page of a PDF, clean up whitespace and empty lines,
    and write the result to a plain-text file.
    """
    # 1. Open the PDF
    reader = PyPDF2.PdfReader(pdf_path)
    pages_text = []

    # 2. Loop through pages
    for page in reader.pages:
        raw = page.extract_text()
        if not raw:
            continue

        # 3. Clean: strip each line and drop empty ones
        lines = raw.split("\n")
        cleaned = [line.strip() for line in lines if line.strip()]
        pages_text.append("\n".join(cleaned))

    # 4. Join pages with blank lines and save
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(pages_text))

if __name__ == "__main__":
    pdf_path = "/home/abdulwahab-bhai/personal/tradia_ai_backend/backend/docs/export_declaration_helpguide.pdf"
    output_txt_path = "export_guide_2.txt"
    parse_pdf_to_txt(pdf_path, output_txt_path)
    print(f"Extraction complete — cleaned text in: {output_txt_path}")

def extract_text_from_pdf(pdf_path):
    # Function to extract text from a PDF file
    import PyPDF2

    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text.strip()


def extract_text_from_docx(docx_path):
    # Function to extract text from a DOCX file
    from docx import Document

    doc = Document(docx_path)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text.strip()
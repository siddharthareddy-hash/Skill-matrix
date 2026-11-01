import pdfplumber
from docx import Document

def extract_text(file_storage):
    filename = file_storage.filename.lower()
    if filename.endswith(".pdf"):
        with pdfplumber.open(file_storage) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif filename.endswith(".docx"):
        doc = Document(file_storage)
        return "\n".join(p.text for p in doc.paragraphs)
    elif filename.endswith(".txt"):
        return file_storage.read().decode("utf-8", errors="ignore")
    return None

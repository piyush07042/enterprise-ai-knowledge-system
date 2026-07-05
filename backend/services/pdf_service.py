from pypdf import PdfReader


def clean_extracted_text(text):
    return "\n".join(
        line.strip()
        for line in (text or "").splitlines()
        if line.strip()
    )


def extract_pdf_text(pdf_path):
    reader = PdfReader(pdf_path)

    pages = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        cleaned_page = clean_extracted_text(page_text)

        if cleaned_page:
            pages.append(cleaned_page)

    return "\n\n".join(pages)

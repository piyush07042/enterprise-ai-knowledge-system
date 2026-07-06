from pypdf import PdfReader
import fitz  # PyMuPDF
from rapidocr_onnxruntime import RapidOCR
import io
from PIL import Image


def clean_extracted_text(text):
    return "\n".join(
        line.strip()
        for line in (text or "").splitlines()
        if line.strip()
    )


def ocr_pdf_fallback(pdf_path):
    print("PDF text extraction returned empty. Running OCR fallback using RapidOCR...")
    try:
        doc = fitz.open(pdf_path)
        ocr = RapidOCR()
        
        ocr_pages = []
        for i in range(len(doc)):
            page = doc[i]
            pix = page.get_pixmap(dpi=150)  # Use 150 DPI for balance between speed and quality
            
            # Save the pixmap to image bytes
            image_bytes = pix.tobytes("png")
            
            # Load into PIL Image
            img = Image.open(io.BytesIO(image_bytes))
            
            # Perform OCR
            result, elapse = ocr(img)
            
            page_text_lines = []
            if result:
                for line in result:
                    text_content = line[1]
                    if text_content.strip():
                        page_text_lines.append(text_content.strip())
            
            page_text = "\n".join(page_text_lines)
            if page_text:
                ocr_pages.append(page_text)
                
        doc.close()
        return "\n\n".join(ocr_pages)
    except Exception as e:
        print("OCR Fallback failed:", e)
        return ""


def extract_pdf_text(pdf_path):
    reader = PdfReader(pdf_path)

    pages = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        cleaned_page = clean_extracted_text(page_text)

        if cleaned_page:
            pages.append(cleaned_page)

    extracted_text = "\n\n".join(pages)
    
    if not extracted_text.strip():
        extracted_text = ocr_pdf_fallback(pdf_path)
        
    return extracted_text

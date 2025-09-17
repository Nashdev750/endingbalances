import os
from google import genai
from google.genai import types
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter

def generate():
    client = genai.Client(api_key="")

    pdf_path = "ocr.pdf"
    output_path = "searchable.pdf"

    # Read the original PDF in binary
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    model = "gemini-2.5-flash"

    # Ask Gemini to perform OCR and return plain text
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    mime_type="application/pdf",
                    data=pdf_data,
                ),
                types.Part.from_text(
                    text="Extract the text from all pages of the PDF, mantain the formatting  and structure of the original PDF, also mantain all the table layouts for any tables in the PDF"
                ),
            ],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0)
    )

    # Collect all text from Gemini
    extracted_text = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.text:
            extracted_text += chunk.text
    return extracted_text        
    # Now create a searchable PDF: overlay recognized text on original images
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    # Split OCR text into pages if Gemini returned with "Page X:" markers
    pages_text = extracted_text.split("Page ")
    pages_text = [p.strip() for p in pages_text if p.strip()]

    for i, page in enumerate(reader.pages):
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        # Put recognized text (as invisible overlay)
        if i < len(pages_text):
            can.setFillColorRGB(1, 1, 1, alpha=0)  # invisible text
            textobject = can.beginText(40, 750)
            for line in pages_text[i].split("\n"):
                textobject.textLine(line)
            can.drawText(textobject)

        can.save()
        packet.seek(0)

        overlay_pdf = PdfReader(packet)
        page.merge_page(overlay_pdf.pages[0])
        writer.add_page(page)

    with open(output_path, "wb") as out:
        writer.write(out)

    print(f"✅ Searchable PDF saved as {output_path}")

if __name__ == "__main__":
    generate()

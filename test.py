import os
from google import genai
from google.genai import types

def generate():
    client = genai.Client(
        api_key="",
    )

    pdf_path = "ocr.pdf"

    # Read the PDF in binary
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    model = "gemini-2.5-flash"

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    mime_type="application/pdf",
                    data=pdf_data,
                ),
                types.Part.from_text(
                    text="Extract the 'Starting Balance' from this PDF. If multiple balances exist, return them all in plain text."
                ),
            ],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0)
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")

if __name__ == "__main__":
    generate()

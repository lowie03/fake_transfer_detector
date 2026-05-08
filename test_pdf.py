import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'fake_transfer_detector')))

from core.screenshot_pipeline import convert_pdf_to_image
import fitz

# create a dummy pdf
doc = fitz.open()
page = doc.new_page()
page.insert_text((50, 50), "Dummy PDF for testing")
pdf_path = "test_dummy.pdf"
doc.save(pdf_path)
doc.close()

print(f"Testing convert_pdf_to_image on {pdf_path}")
res = convert_pdf_to_image(pdf_path)
print(f"Result: {res}")

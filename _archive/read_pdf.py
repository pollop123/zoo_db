import pypdf
import os

def read_pdf(filename):
    print(f"--- Reading {filename} ---")
    try:
        reader = pypdf.PdfReader(filename)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        print(text)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    print(f"--- End of {filename} ---")

files = ["DB114-1_project.pdf", "資料庫管理_期末專案計劃書-2.pdf"]
for f in files:
    if os.path.exists(f):
        read_pdf(f)
    else:
        print(f"File {f} not found.")

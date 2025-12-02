import pypdf

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

if __name__ == "__main__":
    read_pdf("DB114-1_project.pdf")

import os
import re
import pdfplumber
from pathlib import Path

PDF_DIR = "./research_papers"
CLEANED_DIR = "./cleaned_corpus"

def clean_text(text):
    """
    Surgically removes references, equations, and metadata noise.
    """
    if not text:
        return ""
        
    # 1. Strip references/bibliography (usually at the end)
    # Looking for a standalone header like "References"
    split_patterns = [
        r'\n\s*References\s*\n',
        r'\n\s*Bibliography\s*\n',
        r'\n\s*Works Cited\s*\n',
        r'\n\s*REFERENCES\s*\n'
    ]
    for pattern in split_patterns:
        parts = re.split(pattern, text, flags=re.IGNORECASE)
        if len(parts) > 1:
            text = parts[0]
            break
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 2. Heuristic for equations/tables
        # Skip lines with high density of mathematical symbols or isolated numbers
        non_word_chars = len(re.findall(r'[^a-zA-Z0-9\s.,;:?!\'"]', line))
        if len(line) > 0 and non_word_chars / len(line) > 0.3 and len(line) > 10:
            continue
            
        # 3. Remove lines that look like page numbers, short headers, or DOI noise
        if re.match(r'^\d+$', line): # Page number
            continue
        if "doi:" in line.lower() or "http" in line.lower():
            continue
        if len(line) < 10 and not line.endswith(('.', ':', '?', '!')): # Likely a header or fragment
            continue
            
        cleaned_lines.append(line)
        
    return "\n".join(cleaned_lines)

def process_pdfs():
    Path(CLEANED_DIR).mkdir(parents=True, exist_ok=True)
    
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    print(f"Found {len(pdf_files)} PDFs. Starting extraction...")
    
    processed_count = 0
    for filename in pdf_files:
        pdf_path = os.path.join(PDF_DIR, filename)
        output_path = os.path.join(CLEANED_DIR, filename.replace(".pdf", ".txt"))
        
        if os.path.exists(output_path):
            processed_count += 1
            continue
            
        print(f"[{processed_count+1}/{len(pdf_files)}] Processing: {filename}")
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        full_text += extracted + "\n"
                
                cleaned = clean_text(full_text)
                
                if cleaned.strip():
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(cleaned)
                    processed_count += 1
                else:
                    print(f"  Warning: No text extracted/cleaned for {filename}")
        except Exception as e:
            print(f"  Error processing {filename}: {e}")

if __name__ == "__main__":
    if not os.path.exists(PDF_DIR):
        print(f"Error: {PDF_DIR} does not exist. Run the downloader first.")
    else:
        process_pdfs()

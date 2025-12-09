import os
import json
import time
import pdfplumber
import ollama

# --- CONFIGURATION ---
REQUIRED_TEXT_MODEL = 'llama3.2'          # Only the text model is needed now
RESUMES_FOLDER = "Resumes"
JSON_OUTPUT_FOLDER = "json_output_ollama"

# Ensure directories exist
os.makedirs(RESUMES_FOLDER, exist_ok=True)
os.makedirs(JSON_OUTPUT_FOLDER, exist_ok=True)

def extract_text_from_pdf_native(pdf_path):
    """
    Attempts to extract text directly from the PDF digital layer.
    Returns the text and a boolean indicating if extraction was successful.
    """
    text_content = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Check only the first 2 pages to be efficient
            for page in pdf.pages[:2]: 
                extracted = page.extract_text()
                if extracted:
                    text_content += extracted + "\n"
        
        # If we got very little text, it's likely a scanned image PDF or empty
        if len(text_content.strip()) < 50: 
            return None, False
            
        return text_content, True
    except Exception as e:
        print(f"   ⚠️ Native extraction failed: {e}")
        return None, False

def process_with_ai(prompt, model):
    """
    Sends request to Ollama (Text only).
    """
    message_payload = {'role': 'user', 'content': prompt}
    
    response = ollama.chat(
        model=model,
        messages=[message_payload],
        format='json',
        options={'temperature': 0}
    )
    return response['message']['content']

# --- MAIN PROMPT ---
json_structure = """
{
    "Position": "",
    "location": "",
    "qualification": "",
    "experience": "",
    "skills": [],
    "summary": "",
    "work_experience": ""
}
"""

base_prompt = f"""
You are an expert Resume Parser. Extract data from the resume below into strict JSON format.
Follow this exact JSON structure:
{json_structure}

Resume Content:
"""

# --- PIPELINE ---
print(f"--- STARTING DIGITAL-ONLY PIPELINE ---")

# Check if folder exists and has files
if not os.path.exists(RESUMES_FOLDER):
    print(f"Folder '{RESUMES_FOLDER}' not found.")
    exit()

pdf_files = [f for f in os.listdir(RESUMES_FOLDER) if f.endswith('.pdf')]
if not pdf_files:
    print("No PDFs found in Resumes folder.")
    exit()

for pdf_file in pdf_files:
    print(f"\n📄 Processing: {pdf_file}")
    file_path = os.path.join(RESUMES_FOLDER, pdf_file)
    output_json_path = os.path.join(JSON_OUTPUT_FOLDER, pdf_file.replace('.pdf', '.json'))
    
    start_time = time.time()
    
    # 1. Try Native Text Extraction
    print("   ↳ Attempting native text extraction...")
    text_content, is_digital = extract_text_from_pdf_native(file_path)
    
    ai_response = None
    
    if is_digital:
        print(f"   ↳ Sending text to {REQUIRED_TEXT_MODEL}...")
        
        full_prompt = base_prompt + text_content
        try:
            ai_response = process_with_ai(full_prompt, REQUIRED_TEXT_MODEL)
        except Exception as e:
            print(f"   ❌ AI Error: {e}")

        # 2. Save Results
        if ai_response:
            try:
                data = json.loads(ai_response)
                with open(output_json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                print(f"   🎉 Success! Saved to {output_json_path}")
            except json.JSONDecodeError:
                print("   ❌ Failed to decode JSON response.")
    else:
        print("   ⚠️ Skipped: File appears to be a Scanned PDF (No text layer found).")
    
    print(f"   ⏱️ Time taken: {time.time() - start_time:.2f}s")

print("\n--- DONE ---")
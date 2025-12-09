import pandas as pd
from sentence_transformers import SentenceTransformer
import json
from tqdm import tqdm  # For the progress bar

# --- CONFIGURATION ---
INPUT_CSV = "Data.csv"
OUTPUT_FILE = "job_embeddings.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Define the columns you want to embed. 
# These match the actual headers in Data.csv
COLUMNS_TO_EMBED = ['company', 'job description', 'required qualification', 'location'] 

def generate_embeddings():
    print(f"--- Loading data from {INPUT_CSV} ---")
    try:
        df = pd.read_csv(INPUT_CSV)
    except FileNotFoundError:
        print("❌ Error: Data.csv not found. Please make sure the file exists.")
        return

    # check if columns exist
    available_columns = [c for c in COLUMNS_TO_EMBED if c in df.columns]
    if not available_columns:
        print(f"❌ Error: None of the columns {COLUMNS_TO_EMBED} found in CSV.")
        print(f"   Available columns are: {list(df.columns)}")
        return

    print(f"   Found {len(df)} rows.")
    print(f"   Combining columns: {available_columns} to create embedding text...")

    # Load the sentence-transformer model once
    print(f"   Loading model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    print("   ✅ Model loaded successfully!")

    # Prepare the list to store our results
    vector_database = []

    # Iterate through the DataFrame with a progress bar
    for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Generating Embeddings"):
        
        # 1. Create a combined text string for the model to read
        # We combine title, description, etc. into one block of text
        text_parts = []
        for col in available_columns:
            val = str(row[col]) if pd.notna(row[col]) else ""
            text_parts.append(f"{col}: {val}")
        
        text_to_embed = "\n".join(text_parts)

        # 2. Generate Embedding using sentence-transformers
        try:
            # encode() returns a numpy array, convert to list for JSON serialization
            embedding_vector = model.encode(text_to_embed).tolist()

            # 3. Store the data
            # We store the original text metadata + the vector
            entry = {
                "id": index,
                "metadata": row.to_dict(), # Save all CSV info so we can display it later
                "embedding": embedding_vector
            }
            vector_database.append(entry)

        except Exception as e:
            print(f"\n❌ Error generating embedding for row {index}: {e}")
            # You might want to break or continue depending on your needs
            continue

    # 4. Save to file
    print(f"\n--- Saving {len(vector_database)} embeddings to {OUTPUT_FILE} ---")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(vector_database, f)

    print("✅ Done! You can now use this JSON file for the search script.")

if __name__ == "__main__":
    generate_embeddings()
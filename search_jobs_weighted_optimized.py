import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer

# --- CONFIGURATION ---

RESUME_FOLDER = "json_output_ollama"
JOB_EMBEDDINGS_PATH = "job_embeddings.json"
OUTPUT_FOLDER = "matched_job_weighted_optimized"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Weights - Increased importance on Position and Skills
WEIGHTS = {
    "position": 0.45,
    "skills": 0.25,
    "qualification": 0.20,
    "experience": 0.10
}

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_embedding(text, model):
    """Generates an embedding and normalizes it immediately."""
    if not text or not text.strip():
        return np.zeros(384)
    
    try:
        # Use sentence-transformers model to encode text
        vec = model.encode(text, convert_to_numpy=True)
        
        # Normalize the vector (L2 Norm) so dot product = cosine similarity
        norm = np.linalg.norm(vec)
        if norm > 0:
            return vec / norm
        return vec
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return np.zeros(384)

def prepare_job_matrix(job_database):
    """
    Converts the list of job dictionaries into a 2D Numpy Matrix.
    This allows us to search ALL jobs in one math operation.
    """
    print("   Building Job Matrix...")
    
    # Extract embeddings
    embeddings = [job['embedding'] for job in job_database]
    matrix = np.array(embeddings)
    
    # Normalize the entire matrix row by row
    # (This ensures dot product equals cosine similarity later)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    # Avoid division by zero
    norms[norms == 0] = 1 
    normalized_matrix = matrix / norms
    
    return normalized_matrix

def search_jobs():
    print("--- Starting Vectorized Job Matching ---")

    # 1. Load Jobs
    if not os.path.exists(JOB_EMBEDDINGS_PATH):
        print("❌ Job database not found.")
        return

    job_database = load_json(JOB_EMBEDDINGS_PATH)
    
    # 2. Load the sentence-transformer model once
    print(f"   Loading model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    print("   ✅ Model loaded successfully!")
    
    # 3. PRE-CALCULATE THE MATRIX (The "Engine")
    # Shape: (Num_Jobs, 384)
    job_matrix = prepare_job_matrix(job_database)
    print(f"   Matrix Ready: {job_matrix.shape} (Jobs, Dimensions)")

    # 4. Get Resumes
    resume_files = [f for f in os.listdir(RESUME_FOLDER) if f.endswith('.json')]
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # 5. Process Resumes
    for idx, resume_file in enumerate(resume_files, 1):
        print(f"\nProcessing [{idx}/{len(resume_files)}]: {resume_file}")
        resume_data = load_json(os.path.join(RESUME_FOLDER, resume_file))

        # --- A. Generate & Normalize Resume Vectors ---
        # We normalize here so we can use simple Dot Product later
        vec_pos = get_embedding(f"Job Role: {resume_data.get('Position', '')}", model)
        
        skills_text = f"Skills: {resume_data.get('skills', '')} \n Summary: {resume_data.get('summary', '')}"
        vec_skills = get_embedding(skills_text, model)
        
        vec_qual = get_embedding(f"Qualification: {resume_data.get('qualification', '')}", model)
        vec_exp = get_embedding(f"Experience: {resume_data.get('experience', '')} {resume_data.get('work_experience', '')}", model)

        # --- B. VECTORIZED CALCULATION (The Fast Part) ---
        # Instead of a loop, we multiply the Job Matrix by the Resume Vectors.
        # This gives us an array of scores for EVERY job instantly.
        
        # 1. Calculate scores for all jobs for Position
        # Result shape: (Num_Jobs,)
        scores_pos = np.dot(job_matrix, vec_pos)
        
        # 2. Calculate scores for all jobs for Skills
        scores_skills = np.dot(job_matrix, vec_skills)
        
        # 3. Calculate scores for all jobs for Qualification
        scores_qual = np.dot(job_matrix, vec_qual)
        
        # 4. Calculate scores for all jobs for Experience
        scores_exp = np.dot(job_matrix, vec_exp)

        # 5. Apply Weights
        final_scores = (scores_pos * WEIGHTS['position']) + \
                       (scores_skills * WEIGHTS['skills']) + \
                       (scores_qual * WEIGHTS['qualification']) + \
                       (scores_exp * WEIGHTS['experience'])

        # --- C. Sort and Extract Top 20 ---
        # argsort gives indices of the sorted array (ascending), so we flip it [-20:] and reverse
        top_indices = np.argsort(final_scores)[-20:][::-1]

        top_jobs = []
        for i in top_indices:
            top_jobs.append({
                "match_score": float(final_scores[i]),
                "breakdown": {
                    "pos_score": float(scores_pos[i]),
                    "skill_score": float(scores_skills[i]),
                    "qual_score": float(scores_qual[i]),
                    "exp_score": float(scores_exp[i])
                },
                "job_details": job_database[i]['metadata']
            })

        # Save
        output_path = os.path.join(OUTPUT_FOLDER, resume_file.replace('.json', '_matches.json'))
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(top_jobs, f, indent=4)
            
        print(f"✅ Saved top matches to {output_path}")
        print(f"   Top Score: {top_jobs[0]['match_score']:.4f} - {top_jobs[0]['job_details'].get('job title', 'Unknown')}")

if __name__ == "__main__":
    search_jobs()
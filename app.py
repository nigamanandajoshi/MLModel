"""
Flask API for ML Job Matching System
Exposes REST endpoints for job matching functionality
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend connection

# --- CONFIGURATION ---
JOB_EMBEDDINGS_PATH = "job_embeddings.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_N_MATCHES = 20
TOP_N_LOCATION = 10

# Weights for matching
WEIGHTS = {
    "position": 0.45,
    "skills": 0.25,
    "qualification": 0.20,
    "experience": 0.10
}

# Global model and data (loaded once at startup)
model = None
job_database = None
job_matrix = None
geolocator = None

def load_model_and_data():
    """Load the ML model and job database at startup"""
    global model, job_database, job_matrix, geolocator
    
    print("🚀 Starting ML Job Matching API...")
    
    # Load model
    print(f"   Loading model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    print("   ✅ Model loaded!")
    
    # Load job database
    if not os.path.exists(JOB_EMBEDDINGS_PATH):
        print("   ⚠️ Warning: Job embeddings file not found!")
        job_database = []
        job_matrix = np.array([])
    else:
        with open(JOB_EMBEDDINGS_PATH, 'r', encoding='utf-8') as f:
            job_database = json.load(f)
        
        # Prepare job matrix
        embeddings = [job['embedding'] for job in job_database]
        job_matrix = np.array(embeddings)
        
        # Normalize matrix
        norms = np.linalg.norm(job_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1
        job_matrix = job_matrix / norms
        
        print(f"   ✅ Loaded {len(job_database)} jobs")
    
    # Initialize geolocator
    geolocator = Nominatim(user_agent="job_matcher_api")
    print("   ✅ Geolocator initialized")
    
    print("✅ API Ready!\n")

def get_embedding(text):
    """Generate normalized embedding for text"""
    if not text or not text.strip():
        return np.zeros(384)
    
    try:
        vec = model.encode(text, convert_to_numpy=True)
        norm = np.linalg.norm(vec)
        if norm > 0:
            return vec / norm
        return vec
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return np.zeros(384)

def get_coordinates(location_string, retry=3):
    """Get latitude and longitude for a location"""
    for attempt in range(retry):
        try:
            location = geolocator.geocode(location_string, timeout=10)
            if location:
                return (location.latitude, location.longitude)
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            if attempt < retry - 1:
                time.sleep(1)
                continue
            return None

def calculate_distance(coord1, coord2):
    """Calculate distance between two coordinates in km"""
    if coord1 and coord2:
        return geodesic(coord1, coord2).kilometers
    return float('inf')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'jobs_loaded': len(job_database) if job_database else 0
    })

@app.route('/api/match-jobs', methods=['POST'])
def match_jobs():
    """
    Match jobs based on resume data
    
    Request body:
    {
        "position": "Software Engineer",
        "skills": "Python, Machine Learning",
        "summary": "...",
        "qualification": "Bachelor's in CS",
        "experience": "3 years",
        "work_experience": "..."
    }
    """
    try:
        resume_data = request.json
        
        if not resume_data:
            return jsonify({'error': 'No resume data provided'}), 400
        
        # Generate embeddings for resume
        vec_pos = get_embedding(f"Job Role: {resume_data.get('position', '')}")
        
        skills_text = f"Skills: {resume_data.get('skills', '')} \n Summary: {resume_data.get('summary', '')}"
        vec_skills = get_embedding(skills_text)
        
        vec_qual = get_embedding(f"Qualification: {resume_data.get('qualification', '')}")
        vec_exp = get_embedding(f"Experience: {resume_data.get('experience', '')} {resume_data.get('work_experience', '')}")
        
        # Calculate scores for all jobs
        scores_pos = np.dot(job_matrix, vec_pos)
        scores_skills = np.dot(job_matrix, vec_skills)
        scores_qual = np.dot(job_matrix, vec_qual)
        scores_exp = np.dot(job_matrix, vec_exp)
        
        # Apply weights
        final_scores = (scores_pos * WEIGHTS['position']) + \
                       (scores_skills * WEIGHTS['skills']) + \
                       (scores_qual * WEIGHTS['qualification']) + \
                       (scores_exp * WEIGHTS['experience'])
        
        # Get top matches
        top_indices = np.argsort(final_scores)[-TOP_N_MATCHES:][::-1]
        
        top_jobs = []
        for i in top_indices:
            top_jobs.append({
                'match_score': float(final_scores[i]),
                'breakdown': {
                    'pos_score': float(scores_pos[i]),
                    'skill_score': float(scores_skills[i]),
                    'qual_score': float(scores_qual[i]),
                    'exp_score': float(scores_exp[i])
                },
                'job_details': job_database[i]['metadata']
            })
        
        return jsonify({
            'success': True,
            'matches': top_jobs,
            'total_matches': len(top_jobs)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/match-jobs-with-location', methods=['POST'])
def match_jobs_with_location():
    """
    Match jobs and sort by location proximity
    
    Request body:
    {
        "position": "Software Engineer",
        "skills": "Python, Machine Learning",
        "summary": "...",
        "qualification": "Bachelor's in CS",
        "experience": "3 years",
        "work_experience": "...",
        "location": "San Francisco, CA"
    }
    """
    try:
        resume_data = request.json
        
        if not resume_data:
            return jsonify({'error': 'No resume data provided'}), 400
        
        # First, get matched jobs (same as match_jobs endpoint)
        vec_pos = get_embedding(f"Job Role: {resume_data.get('position', '')}")
        skills_text = f"Skills: {resume_data.get('skills', '')} \n Summary: {resume_data.get('summary', '')}"
        vec_skills = get_embedding(skills_text)
        vec_qual = get_embedding(f"Qualification: {resume_data.get('qualification', '')}")
        vec_exp = get_embedding(f"Experience: {resume_data.get('experience', '')} {resume_data.get('work_experience', '')}")
        
        scores_pos = np.dot(job_matrix, vec_pos)
        scores_skills = np.dot(job_matrix, vec_skills)
        scores_qual = np.dot(job_matrix, vec_qual)
        scores_exp = np.dot(job_matrix, vec_exp)
        
        final_scores = (scores_pos * WEIGHTS['position']) + \
                       (scores_skills * WEIGHTS['skills']) + \
                       (scores_qual * WEIGHTS['qualification']) + \
                       (scores_exp * WEIGHTS['experience'])
        
        top_indices = np.argsort(final_scores)[-TOP_N_MATCHES:][::-1]
        
        matched_jobs = []
        for i in top_indices:
            matched_jobs.append({
                'match_score': float(final_scores[i]),
                'breakdown': {
                    'pos_score': float(scores_pos[i]),
                    'skill_score': float(scores_skills[i]),
                    'qual_score': float(scores_qual[i]),
                    'exp_score': float(scores_exp[i])
                },
                'job_details': job_database[i]['metadata']
            })
        
        # Now sort by location if provided
        resume_location = resume_data.get('location', '')
        
        if not resume_location:
            # Return without location sorting
            return jsonify({
                'success': True,
                'matches': matched_jobs[:TOP_N_LOCATION],
                'total_matches': len(matched_jobs),
                'location_sorted': False
            })
        
        # Get resume coordinates
        resume_coords = get_coordinates(resume_location)
        
        if not resume_coords:
            # Return without location sorting if geocoding fails
            return jsonify({
                'success': True,
                'matches': matched_jobs[:TOP_N_LOCATION],
                'total_matches': len(matched_jobs),
                'location_sorted': False,
                'warning': 'Could not geocode resume location'
            })
        
        # Calculate distances for each job
        jobs_with_distance = []
        for job in matched_jobs:
            job_location = job['job_details'].get('location', '')
            job_coords = get_coordinates(job_location)
            
            job_copy = job.copy()
            if job_coords:
                distance = calculate_distance(resume_coords, job_coords)
                job_copy['distance_km'] = round(distance, 2)
                job_copy['job_coordinates'] = job_coords
            else:
                job_copy['distance_km'] = float('inf')
                job_copy['job_coordinates'] = None
            
            jobs_with_distance.append(job_copy)
        
        # Sort by distance
        sorted_jobs = sorted(jobs_with_distance, key=lambda x: x['distance_km'])
        
        # Add location rank
        for rank, job in enumerate(sorted_jobs[:TOP_N_LOCATION], 1):
            job['location_rank'] = rank
        
        return jsonify({
            'success': True,
            'matches': sorted_jobs[:TOP_N_LOCATION],
            'total_matches': len(sorted_jobs),
            'location_sorted': True,
            'resume_coordinates': resume_coords
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Load model and data before starting the server
    load_model_and_data()
    
    # Start Flask server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

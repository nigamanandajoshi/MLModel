"""
Location-based Job Sorting System
Reads matched jobs from matched_job_weighted_optimized and sorts by location proximity
"""

import json
import os
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

# --- CONFIGURATION ---
RESUME_FOLDER = "json_output"
MATCHED_JOBS_FOLDER = "matched_job_weighted_optimized"
OUTPUT_FOLDER = "matched_job_location_sorted"
TOP_N = 10  # Number of closest jobs to return

def get_coordinates(location_string, geolocator, retry=3):
    """
    Get latitude and longitude for a location string
    
    Args:
        location_string: Location to geocode
        geolocator: Nominatim geolocator instance
        retry: Number of retries on failure
        
    Returns:
        Tuple of (latitude, longitude) or None
    """
    for attempt in range(retry):
        try:
            location = geolocator.geocode(location_string, timeout=10)
            if location:
                return (location.latitude, location.longitude)
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            if attempt < retry - 1:
                time.sleep(1)  # Wait before retry
                continue
            print(f"   ⚠️  Geocoding failed for '{location_string}': {e}")
            return None

def calculate_distance(coord1, coord2):
    """
    Calculate distance between two coordinates in kilometers
    
    Args:
        coord1: Tuple of (lat, lon)
        coord2: Tuple of (lat, lon)
        
    Returns:
        Distance in kilometers
    """
    if coord1 and coord2:
        return geodesic(coord1, coord2).kilometers
    return float('inf')  # Return infinity if coordinates not available

def sort_jobs_by_location(resume_location, matched_jobs, geolocator):
    """
    Sort matched jobs by proximity to resume location
    
    Args:
        resume_location: Location string from resume
        matched_jobs: List of matched job dictionaries
        geolocator: Nominatim geolocator instance
        
    Returns:
        List of jobs sorted by distance with rank
    """
    print(f"   📍 Resume Location: {resume_location}")
    
    # Get resume coordinates
    resume_coords = get_coordinates(resume_location, geolocator)
    
    if not resume_coords:
        print(f"   ⚠️  Could not geocode resume location. Returning original order.")
        return matched_jobs[:TOP_N]
    
    print(f"   ✅ Resume Coordinates: {resume_coords}")
    
    # Calculate distances for each job
    jobs_with_distance = []
    for job in matched_jobs:
        job_location = job['job_details'].get('location', '')
        job_coords = get_coordinates(job_location, geolocator)
        
        if job_coords:
            distance = calculate_distance(resume_coords, job_coords)
            job_with_dist = job.copy()
            job_with_dist['distance_km'] = round(distance, 2)
            job_with_dist['job_coordinates'] = job_coords
            jobs_with_distance.append(job_with_dist)
        else:
            # If geocoding fails, assign a very high distance
            job_with_dist = job.copy()
            job_with_dist['distance_km'] = float('inf')
            job_with_dist['job_coordinates'] = None
            jobs_with_distance.append(job_with_dist)
    
    # Sort by distance (ascending - nearest first)
    sorted_jobs = sorted(jobs_with_distance, key=lambda x: x['distance_km'])
    
    # Add rank (1 = nearest)
    for rank, job in enumerate(sorted_jobs[:TOP_N], 1):
        job['location_rank'] = rank
    
    return sorted_jobs[:TOP_N]

def process_all_resumes():
    """
    Process all matched job files and sort by location proximity
    """
    print("="*80)
    print("🗺️  LOCATION-BASED JOB SORTING SYSTEM")
    print("="*80)
    
    # Initialize geolocator
    geolocator = Nominatim(user_agent="job_matcher_app")
    
    # Create output directory
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Get all matched job files
    if not os.path.exists(MATCHED_JOBS_FOLDER):
        print(f"❌ Matched jobs folder not found: {MATCHED_JOBS_FOLDER}")
        return
    
    matched_files = [f for f in os.listdir(MATCHED_JOBS_FOLDER) if f.endswith('.json')]
    
    if not matched_files:
        print(f"⚠️  No matched job files found in {MATCHED_JOBS_FOLDER}")
        return
    
    print(f"\n📁 Found {len(matched_files)} matched job file(s)\n")
    
    for idx, matched_file in enumerate(matched_files, 1):
        print(f"\n{'='*80}")
        print(f"Processing [{idx}/{len(matched_files)}]: {matched_file}")
        print(f"{'='*80}")
        
        # Extract resume name
        resume_name = matched_file.replace('_matches.json', '.json')
        resume_path = os.path.join(RESUME_FOLDER, resume_name)
        
        if not os.path.exists(resume_path):
            print(f"⚠️  Resume file not found: {resume_path}")
            continue
        
        try:
            # Load resume data
            with open(resume_path, 'r', encoding='utf-8') as f:
                resume_data = json.load(f)
            
            resume_location = resume_data.get('location', '')
            
            if not resume_location:
                print(f"⚠️  No location found in resume. Skipping.")
                continue
            
            # Load matched jobs
            matched_path = os.path.join(MATCHED_JOBS_FOLDER, matched_file)
            with open(matched_path, 'r', encoding='utf-8') as f:
                matched_jobs = json.load(f)
            
            print(f"   📊 Total matched jobs: {len(matched_jobs)}")
            
            # Sort by location
            sorted_jobs = sort_jobs_by_location(resume_location, matched_jobs, geolocator)
            
            # Save sorted results
            output_file = os.path.join(OUTPUT_FOLDER, matched_file.replace('_matches.json', '_location_sorted.json'))
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sorted_jobs, f, indent=4, ensure_ascii=False)
            
            print(f"\n   💾 Saved to: {output_file}")
            
            # Display top 3 results
            print(f"\n   🏆 TOP 3 NEAREST JOBS:")
            for job in sorted_jobs[:3]:
                rank = job.get('location_rank', 'N/A')
                distance = job.get('distance_km', 'N/A')
                company = job['job_details'].get('company', 'Unknown')
                location = job['job_details'].get('location', 'Unknown')
                match_score = job.get('match_score', 0)
                
                print(f"      Rank {rank}: {company}")
                print(f"         📍 Location: {location}")
                print(f"         📏 Distance: {distance} km")
                print(f"         🎯 Match Score: {match_score:.4f}")
                print()
            
            # Add a small delay to avoid overwhelming the geocoding service
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Error processing {matched_file}: {str(e)}")
            continue
    
    print("\n" + "="*80)
    print("✅ ALL PROCESSING COMPLETE!")
    print(f"📂 Results saved in: {OUTPUT_FOLDER}")
    print("="*80)

if __name__ == "__main__":
    try:
        process_all_resumes()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")

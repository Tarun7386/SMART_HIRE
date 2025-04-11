# File: process_multiple_jobs.py
import csv
import os
import sys
from datetime import datetime
from agents.jd_analyzer import JDAnalyzer
from agents.cv_parser1 import CVParser
from agents.matcher import MatchingEngine
from agents.scheduler import InterviewScheduler
from utils.document_processor import extract_text_from_file
from db.database import setup_database, store_job

def main():
    # Check arguments
    if len(sys.argv) < 3:
        print("Usage: python process_multiple_jobs.py <jobs_csv_file> <resumes_directory> [threshold]")
        return
    
    jobs_csv_file = sys.argv[1]
    resumes_dir = sys.argv[2]
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 70.0
    
    # Setup database
    print("Setting up database...")
    setup_database()
    
    # Initialize agents
    jd_agent = JDAnalyzer()
    cv_agent = CVParser()
    matching_agent = MatchingEngine(threshold=threshold)
    scheduler_agent = InterviewScheduler()
    
    # Process resumes first (to avoid reprocessing for each job)
    print("\nProcessing resumes...")
    cv_files = [f for f in os.listdir(resumes_dir) if f.lower().endswith(('.pdf', '.docx', '.doc'))]
    
    if not cv_files:
        print(f"Error: No CV files found in '{resumes_dir}'")
        return
    
    print(f"Found {len(cv_files)} resume files")
    
    # Store candidate profiles
    candidate_ids = []
    candidate_names = {}
    
    for i, cv_filename in enumerate(cv_files):
        cv_path = os.path.join(resumes_dir, cv_filename)
        candidate_id = f"cand_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
        candidate_ids.append(candidate_id)
        
        print(f"Processing resume {i+1}/{len(cv_files)}: {cv_filename}")
        cv_text = extract_text_from_file(cv_path)
        profile = cv_agent.process_cv(candidate_id, cv_text)
        candidate_names[candidate_id] = profile['name']
        print(f"  → Processed {profile['name']}'s resume")
    
    # Process jobs from CSV
    print("\nProcessing jobs from CSV...")
    
    try:
        with open(jobs_csv_file, 'r', encoding='latin-1') as csv_file:
            csv_reader = csv.reader(csv_file)
            header = next(csv_reader)  # Skip header row
            
            for row_num, row in enumerate(csv_reader):
                if len(row) < 2:
                    print(f"Warning: Row {row_num+2} does not have enough columns, skipping")
                    continue
                
                job_title = row[0]
                job_description = row[1]
                company_name = "Example Company"
                
                print(f"\nProcessing job {row_num+1}: {job_title}")
                
                # Generate job ID and store job
                job_id = f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}_{row_num}"
                store_job(job_id, job_title, company_name, job_description)
                
                # Process job requirements
                print("Extracting job requirements...")
                job_requirements = jd_agent.process_job(job_id, job_description)
                print(f"Extracted requirements: {len(job_requirements['skills'])} skills, {job_requirements['experience']} experience, education: {job_requirements['education']}")
                
                # Match candidates to job
                print(f"Matching {len(candidate_ids)} candidates to job requirements...")
                match_results = matching_agent.match_candidates(job_id, candidate_ids)
                
                # Print match results
                print("\nMatch Results:")
                for i, result in enumerate(match_results):
                    status = "SHORTLISTED" if result["shortlisted"] else "Not shortlisted"
                    print(f"{i+1}. Candidate {result['candidate_name']}: {result['overall_score']:.1f}% match - {status}")
                    print(f"   Skills: {result['skills_score']:.1f}%, Experience: {result['experience_score']:.1f}%, Education: {result['education_score']:.1f}%")
                
                # Count shortlisted candidates
                shortlisted_count = sum(1 for result in match_results if result["shortlisted"])
                
                if shortlisted_count == 0:
                    print("\nNo candidates were shortlisted for this job. Consider lowering the threshold.")
                    continue
                
                # Schedule interviews for shortlisted candidates
                print(f"\nScheduling interviews for {shortlisted_count} shortlisted candidates...")
                interviews = scheduler_agent.schedule_interviews(job_id, job_title, company_name)
                
                print(f"{len(interviews)} interview invitations prepared.")
                
                print(f"\nJob screening completed for '{job_title}'")
                print(f"Processed {len(candidate_ids)} resumes, shortlisted {shortlisted_count} candidates ({shortlisted_count/len(candidate_ids)*100:.1f}%)")
    
    except Exception as e:
        print(f"Error processing CSV file: {e}")
    
    print("\nAll jobs processed successfully!")

if __name__ == "__main__":
    main()
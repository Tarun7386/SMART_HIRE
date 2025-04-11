import os
import argparse
from datetime import datetime
from agents.jd_analyzer import JDAnalyzer
from agents.cv_parser1 import CVParser
from agents.matcher import MatchingEngine
from agents.scheduler import InterviewScheduler
from utils.document_processor import extract_text_from_file
from db.database import setup_database, store_job

def main():
    parser = argparse.ArgumentParser(description='Job Screening Multi-Agent System')
    parser.add_argument('--jd', type=str, help='Path to job description file')
    parser.add_argument('--cv_dir', type=str, help='Directory containing CV files')
    parser.add_argument('--job_title', type=str, default='', help='Job title')
    parser.add_argument('--company', type=str, default='', help='Company name')
    parser.add_argument('--threshold', type=float, default=70.0, help='Match threshold (0-100)')
    
    args = parser.parse_args()
    
    # Setup database
    print("Setting up database...")
    setup_database()
    
    # Initialize agents
    jd_agent = JDAnalyzer()
    cv_agent = CVParser()
    matching_agent = MatchingEngine(threshold=args.threshold)
    scheduler_agent = InterviewScheduler()
    
    # Process job description
    if not args.jd:
        print("Error: Job description file is required")
        return
    
    if not os.path.exists(args.jd):
        print(f"Error: Job description file '{args.jd}' not found")
        return
    
    job_id = f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    job_title = args.job_title or os.path.basename(args.jd).split('.')[0]
    company_name = args.company or "Your Company"
    
    print(f"Processing job description: {args.jd}")
    jd_text = extract_text_from_file(args.jd)
    
    # Store job in database
    store_job(job_id, job_title, company_name, jd_text)
    
    # Process job requirements
    print("Extracting job requirements...")
    job_requirements = jd_agent.process_job(job_id, jd_text)
    print(f"Extracted requirements: {len(job_requirements['skills'])} skills, {job_requirements['experience']} experience, education: {job_requirements['education']}")
    
    # Process candidate CVs
    if not args.cv_dir:
        print("Error: CV directory is required")
        return
    
    if not os.path.exists(args.cv_dir):
        print(f"Error: CV directory '{args.cv_dir}' not found")
        return
    
    cv_files = [f for f in os.listdir(args.cv_dir) if f.endswith(('.pdf', '.docx', '.doc','.txt'))]
    if not cv_files:
        print(f"Error: No CV files found in '{args.cv_dir}'")
        return
    
    print(f"\nProcessing {len(cv_files)} candidate resumes...")
    candidate_ids = []
    
    for i, cv_filename in enumerate(cv_files):
        cv_path = os.path.join(args.cv_dir, cv_filename)
        candidate_id = f"cand_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
        candidate_ids.append(candidate_id)
        
        print(f"Processing: {cv_filename}")
        cv_text = extract_text_from_file(cv_path)
        profile = cv_agent.process_cv(candidate_id, cv_text)
        print(f"  → Processed {profile['name']}'s resume with {len(profile['skills'])} skills and {len(profile['experience'])} work experiences")
    
    # Match candidates to job
    print("\nMatching candidates to job requirements...")
    match_results = matching_agent.match_candidates(job_id, candidate_ids)
    
    print("\nMatch Results:")
    for i, result in enumerate(match_results):
        status = "SHORTLISTED" if result["shortlisted"] else "Not shortlisted"
        print(f"{i+1}. Candidate {result['candidate_name']}: {result['overall_score']:.1f}% match - {status}")
        print(f"   Skills: {result['skills_score']:.1f}%, Experience: {result['experience_score']:.1f}%, Education: {result['education_score']:.1f}%")
    
    # Count shortlisted candidates
    shortlisted_count = sum(1 for result in match_results if result["shortlisted"])
    
    if shortlisted_count == 0:
        print("\nNo candidates were shortlisted. Consider lowering the threshold.")
        return
    
    # Schedule interviews for shortlisted candidates
    print(f"\nScheduling interviews for {shortlisted_count} shortlisted candidates...")
    interviews = scheduler_agent.schedule_interviews(job_id, job_title, company_name)
    
    print(f"\n{len(interviews)} interview invitations prepared.")
    
    for i, interview in enumerate(interviews):
        print(f"\nEmail {i+1}: Invitation for {interview['candidate']['name']}")
        print(f"Proposed slots: {', '.join(interview['proposed_slots'][:2])}...")
    
    print("\nJob screening process completed successfully!")
    print(f"Processed {len(cv_files)} resumes, shortlisted {shortlisted_count} candidates ({shortlisted_count/len(cv_files)*100:.1f}%)")

if __name__ == "__main__":
    main()
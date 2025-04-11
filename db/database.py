import os
import sqlite3
import json
from datetime import datetime

# Database file
DB_FILE = "recruitment_system.db"

def get_connection():
    """Get SQLite connection"""
    conn = sqlite3.connect(DB_FILE)
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def setup_database():
    """Create database tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create jobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            description TEXT,
            date_posted DATE
        )
    ''')
    
    # Create job requirements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_requirements (
            requirement_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            skills TEXT,
            experience TEXT,
            education TEXT,
            responsibilities TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs (job_id)
        )
    ''')
    
    # Create candidates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            candidate_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            skills TEXT,
            experience TEXT,
            education TEXT,
            resume_text TEXT
        )
    ''')
    
    # Create match results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_results (
            match_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            candidate_id TEXT,
            skills_score REAL,
            experience_score REAL,
            education_score REAL,
            overall_score REAL,
            shortlisted BOOLEAN,
            match_date DATE,
            FOREIGN KEY (job_id) REFERENCES jobs (job_id),
            FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id)
        )
    ''')
    
    # Create interview schedule table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interviews (
            interview_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            candidate_id TEXT,
            proposed_dates TEXT,
            status TEXT,
            notes TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs (job_id),
            FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def store_job(job_id, title, company, description):
    """Store job in database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO jobs (job_id, title, company, description, date_posted)
        VALUES (?, ?, ?, ?, ?)
    ''', (job_id, title, company, description, datetime.now().date()))
    
    conn.commit()
    conn.close()

def store_job_requirements(job_id, requirements):
    """Store job requirements in database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Convert lists to JSON strings for storage
    skills_json = json.dumps(requirements.get("skills", []))
    responsibilities_json = json.dumps(requirements.get("responsibilities", []))
    
    cursor.execute('''
        INSERT INTO job_requirements (job_id, skills, experience, education, responsibilities)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        job_id,
        skills_json,
        requirements.get("experience", ""),
        requirements.get("education", ""),
        responsibilities_json
    ))
    
    conn.commit()
    conn.close()
    
    return requirements

def store_candidate_profile(candidate_id, profile):
    """Store candidate profile in database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Convert complex structures to JSON strings for storage
    skills_json = json.dumps(profile.get("skills", []))
    experience_json = json.dumps(profile.get("experience", []))
    education_json = json.dumps(profile.get("education", []))
    
    cursor.execute('''
        INSERT INTO candidates (candidate_id, name, email, phone, skills, experience, education)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        candidate_id,
        profile.get("name", "Unknown"),
        profile.get("contact", {}).get("email", ""),
        profile.get("contact", {}).get("phone", ""),
        skills_json,
        experience_json,
        education_json
    ))
    
    conn.commit()
    conn.close()
    
    return profile

def get_job_requirements(job_id):
    """Get job requirements from database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT skills, experience, education, responsibilities
        FROM job_requirements
        WHERE job_id = ?
    ''', (job_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {
            "skills": [],
            "experience": "",
            "education": "",
            "responsibilities": []
        }
    
    # Parse JSON strings back to Python objects
    skills = json.loads(row[0]) if row[0] else []
    responsibilities = json.loads(row[3]) if row[3] else []
    
    return {
        "skills": skills,
        "experience": row[1] if row[1] else "",
        "education": row[2] if row[2] else "",
        "responsibilities": responsibilities
    }

def get_candidate_profiles(candidate_ids=None):
    """Get candidate profiles from database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if candidate_ids:
        # Convert list to tuple for SQL IN clause
        if isinstance(candidate_ids, list):
            placeholders = ','.join(['?'] * len(candidate_ids))
            cursor.execute(f'''
                SELECT candidate_id, name, email, phone, skills, experience, education
                FROM candidates
                WHERE candidate_id IN ({placeholders})
            ''', candidate_ids)
        else:
            # Single candidate ID
            cursor.execute('''
                SELECT candidate_id, name, email, phone, skills, experience, education
                FROM candidates
                WHERE candidate_id = ?
            ''', (candidate_ids,))
    else:
        # Get all candidates
        cursor.execute('''
            SELECT candidate_id, name, email, phone, skills, experience, education
            FROM candidates
        ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    candidates = {}
    for row in rows:
        candidate_id = row[0]
        
        # Parse JSON strings back to Python objects
        skills = json.loads(row[4]) if row[4] else []
        experience = json.loads(row[5]) if row[5] else []
        education = json.loads(row[6]) if row[6] else []
        
        candidates[candidate_id] = {
            "name": row[1],
            "contact": {
                "email": row[2],
                "phone": row[3]
            },
            "skills": skills,
            "experience": experience,
            "education": education
        }
    
    return candidates

def store_match_results(match_result):
    """Store match results in database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO match_results (
            job_id, candidate_id, skills_score, experience_score, 
            education_score, overall_score, shortlisted, match_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        match_result["job_id"],
        match_result["candidate_id"],
        match_result["skills_score"],
        match_result["experience_score"],
        match_result["education_score"],
        match_result["overall_score"],
        1 if match_result["shortlisted"] else 0,
        datetime.now().date()
    ))
    
    conn.commit()
    match_id = cursor.lastrowid
    conn.close()
    
    return match_id

def get_shortlisted_candidates(job_id):
    """Get shortlisted candidates for a job"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.candidate_id, c.name, c.email, c.phone, m.overall_score
        FROM match_results m
        JOIN candidates c ON m.candidate_id = c.candidate_id
        WHERE m.job_id = ? AND m.shortlisted = 1
        ORDER BY m.overall_score DESC
    ''', (job_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    shortlisted = []
    for row in rows:
        shortlisted.append({
            "candidate_id": row[0],
            "name": row[1],
            "email": row[2],
            "phone": row[3],
            "match_score": row[4]
        })
    
    return shortlisted

def update_interview_status(job_id, candidate_id, proposed_dates, status):
    """Update interview status in database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Convert date list to JSON string
    dates_json = json.dumps(proposed_dates)
    
    cursor.execute('''
        INSERT INTO interviews (job_id, candidate_id, proposed_dates, status)
        VALUES (?, ?, ?, ?)
    ''', (job_id, candidate_id, dates_json, status))
    
    conn.commit()
    interview_id = cursor.lastrowid
    conn.close()
    
    return interview_id
# File: db/models.py
# Database models for the Job Screening Multi-Agent System

class Job:
    """Model representing a job posting"""
    
    def __init__(self, job_id, title, company, description, date_posted=None):
        self.job_id = job_id
        self.title = title
        self.company = company
        self.description = description
        self.date_posted = date_posted
        self.requirements = None

class JobRequirements:
    """Model representing job requirements"""
    
    def __init__(self, job_id, skills=None, experience=None, education=None, responsibilities=None):
        self.job_id = job_id
        self.skills = skills or []
        self.experience = experience or ""
        self.education = education or ""
        self.responsibilities = responsibilities or []

class Candidate:
    """Model representing a job candidate"""
    
    def __init__(self, candidate_id, name=None, email=None, phone=None):
        self.candidate_id = candidate_id
        self.name = name or "Unknown"
        self.email = email or ""
        self.phone = phone or ""
        self.skills = []
        self.experience = []
        self.education = []
        self.resume_text = ""

class Experience:
    """Model representing work experience"""
    
    def __init__(self, company, title, start_date=None, end_date=None, description=None):
        self.company = company
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        self.description = description or ""

class Education:
    """Model representing educational background"""
    
    def __init__(self, degree, institution, year=None):
        self.degree = degree
        self.institution = institution
        self.year = year

class MatchResult:
    """Model representing a job-candidate match result"""
    
    def __init__(self, job_id, candidate_id):
        self.job_id = job_id
        self.candidate_id = candidate_id
        self.skills_score = 0.0
        self.experience_score = 0.0
        self.education_score = 0.0
        self.overall_score = 0.0
        self.shortlisted = False
        self.match_date = None

class Interview:
    """Model representing an interview schedule"""
    
    def __init__(self, job_id, candidate_id):
        self.job_id = job_id
        self.candidate_id = candidate_id
        self.proposed_dates = []
        self.status = "Pending"
        self.notes = ""
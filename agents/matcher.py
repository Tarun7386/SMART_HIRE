from db.database import get_job_requirements, get_candidate_profiles, store_match_results
import datetime
import re

class MatchingEngine:
    def __init__(self, threshold=70.0):
        self.threshold = threshold
        
    def calculate_skills_match(self, required_skills, candidate_skills):
        """Calculate match score for skills"""
        if not required_skills:
            return 100.0
            
        matches = 0
        partial_matches = 0
        
        for req_skill in required_skills:
            req_skill_lower = req_skill.lower()
            # Check for exact matches
            if any(req_skill_lower == cand_skill.lower() for cand_skill in candidate_skills):
                matches += 1
            # Check for partial matches (e.g., "Python" matches "Python programming")
            elif any(req_skill_lower in cand_skill.lower() or cand_skill.lower() in req_skill_lower 
                    for cand_skill in candidate_skills):
                partial_matches += 0.5
                
        total_matches = matches + partial_matches
        return min(100.0, (total_matches / len(required_skills)) * 100.0)
    
    def calculate_experience_match(self, required_experience, candidate_experience):
        """Calculate match score for experience"""
        # Extract required years from text like "3+ years" or "2-4 years"
        required_years = self._parse_years_experience(required_experience)
        
        if required_years <= 0:
            return 100.0  # If no clear requirement or couldn't parse, give full score
            
        # Calculate total years from candidate experience
        candidate_years = sum(self._calculate_experience_duration(exp) for exp in candidate_experience)
        
        if candidate_years >= required_years:
            return 100.0
        elif candidate_years >= (required_years * 0.7):
            return 70.0 + (30.0 * (candidate_years / required_years))
        elif candidate_years >= (required_years * 0.5):
            return 50.0 + (20.0 * (candidate_years / required_years))
        elif candidate_years > 0:
            return 30.0 + (20.0 * (candidate_years / required_years))
        else:
            return 0.0
    
    def calculate_education_match(self, required_education, candidate_education):
        """Calculate match score for education"""
        if not required_education or not candidate_education:
            return 50.0  # Neutral score if either is missing
            
        education_levels = {
            "high school": 1,
            "associate": 2, 
            "bachelor": 3,
            "master": 4,
            "phd": 5,
            "doctorate": 5
        }
        
        # Determine required education level
        required_level = 0
        for level, value in education_levels.items():
            if level in required_education.lower():
                required_level = value
                break
                
        # If no specific level found but education is required, assume bachelor's
        if required_level == 0 and required_education:
            required_level = 3
                
        # Find highest education level of candidate
        candidate_level = 0
        for education in candidate_education:
            degree_lower = education["degree"].lower() if "degree" in education else ""
            
            # Check each education level
            for level, value in education_levels.items():
                if level in degree_lower and value > candidate_level:
                    candidate_level = value
        
        # Score based on comparison of education levels
        if candidate_level >= required_level:
            return 100.0
        elif candidate_level == required_level - 1:
            return 75.0
        elif candidate_level == required_level - 2:
            return 50.0
        elif candidate_level > 0:
            return 25.0
        else:
            return 0.0
    
    def calculate_overall_match(self, job_requirements, candidate_profile, candidate_id):
        """Calculate overall match score"""
        skills_score = self.calculate_skills_match(
            job_requirements["skills"], 
            candidate_profile["skills"]
        )
        
        experience_score = self.calculate_experience_match(
            job_requirements["experience"], 
            candidate_profile["experience"]
        )
        
        education_score = self.calculate_education_match(
            job_requirements["education"], 
            candidate_profile["education"]
        )
        
        # Weighted average - adjust weights based on job requirements
        # Skills are typically most important, followed by experience and education
        weights = {"skills": 0.5, "experience": 0.3, "education": 0.2}
        
        overall_score = (
            (skills_score * weights["skills"]) + 
            (experience_score * weights["experience"]) + 
            (education_score * weights["education"])
        )
        
        return {
            "candidate_id": candidate_id,
            "candidate_name": candidate_profile["name"],
            "skills_score": skills_score,
            "experience_score": experience_score,
            "education_score": education_score,
            "overall_score": overall_score,
            "shortlisted": overall_score >= self.threshold
        }
    
    def _parse_years_experience(self, experience_text):
        """Parse years of experience from text like '3+ years' or '2-4 years'"""
        if not experience_text:
            return 0
            
        # Try to find patterns like "X+ years", "X-Y years", "at least X years", etc.
        plus_pattern = re.search(r'(\d+)\+\s*years?', experience_text, re.IGNORECASE)
        if plus_pattern:
            return float(plus_pattern.group(1))
            
        range_pattern = re.search(r'(\d+)\s*-\s*(\d+)\s*years?', experience_text, re.IGNORECASE)
        if range_pattern:
            # For a range, use the lower value
            return float(range_pattern.group(1))
            
        min_pattern = re.search(r'(?:at least|minimum|min\.?)\s*(\d+)\s*years?', experience_text, re.IGNORECASE)
        if min_pattern:
            return float(min_pattern.group(1))
            
        # Simple number followed by "years"
        simple_pattern = re.search(r'(\d+)\s*years?', experience_text, re.IGNORECASE)
        if simple_pattern:
            return float(simple_pattern.group(1))
            
        # If no pattern matches, default to 0
        return 0
    
    def _calculate_experience_duration(self, experience):
        """Calculate duration of a work experience in years"""
        if not experience:
            return 0
            
        if not isinstance(experience, dict):
            return 0
            
        if "start_date" not in experience or "end_date" not in experience:
            return 0
            
        start_date = experience["start_date"]
        end_date = experience["end_date"]
        
        # Handle cases where dates might be empty
        if not start_date:
            return 0
            
        # Parse start year
        start_year_match = re.search(r'(\d{4})', str(start_date))
        if not start_year_match:
            return 0
            
        start_year = int(start_year_match.group(1))
        
        # Parse end year (could be "present" or a year)
        if not end_date or end_date.lower() == "present":
            # Use current year for "present"
            end_year = datetime.datetime.now().year
        else:
            end_year_match = re.search(r'(\d{4})', str(end_date))
            if not end_year_match:
                return 0
            end_year = int(end_year_match.group(1))
                
        # Calculate years of experience
        years = end_year - start_year
        
        # Add partial year if month information is available
        start_month_match = re.search(r'(\d{4})-(\d{2})', str(start_date))
        end_month_match = re.search(r'(\d{4})-(\d{2})', str(end_date))
        
        if start_month_match and end_month_match and end_date.lower() != "present":
            start_month = int(start_month_match.group(2))
            end_month = int(end_month_match.group(2))
            
            months = (end_year - start_year) * 12 + (end_month - start_month)
            years = months / 12
        
        return max(0, years)  # Ensure non-negative
    
    def match_candidates(self, job_id, candidate_ids=None):
        """Match all candidates to a specific job"""
        job_requirements = get_job_requirements(job_id)
        
        # If candidate_ids not provided, match all candidates in the database
        candidates = get_candidate_profiles(candidate_ids)
        
        if not candidates:
            return []
        
        match_results = []
        for candidate_id, profile in candidates.items():
            match_result = self.calculate_overall_match(job_requirements, profile, candidate_id)
            match_result["job_id"] = job_id
            
            # Store match result in database
            store_match_results(match_result)
            match_results.append(match_result)
            
        # Sort by overall score, descending
        match_results.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return match_results

# Change this line:
import re
import ollama
from db.database import store_candidate_profile

class CVParser:
    def __init__(self, model_name="mistral"):
        self.model_name = model_name
        
    def extract_profile(self, cv_text):
        """Extract candidate profile from CV text"""
        prompt = f"""
        Extract the following information from this resume:
        1. Candidate name
        2. Contact information (email, phone)
        3. Skills (list all technical and soft skills)
        4. Work experience (for each position: company, title, dates, description)
        5. Education (for each entry: degree, institution, year)
        
        Format the output as JSON with the following structure:
        {{
            "name": "candidate name",
            "contact": {{
                "email": "email address",
                "phone": "phone number"
            }},
            "skills": ["skill1", "skill2", ...],
            "experience": [
                {{
                    "company": "company name",
                    "title": "job title",
                    "start_date": "start date (YYYY-MM or 'present')",
                    "end_date": "end date (YYYY-MM or 'present')",
                    "description": "job description"
                }},
                ...
            ],
            "education": [
                {{
                    "degree": "degree name",
                    "institution": "institution name",
                    "year": year completed (YYYY)
                }},
                ...
            ]
        }}
        
        Here is the resume:
        {cv_text}
        """
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            
            output = response["message"]["content"]
            
            # Parse the response to extract structured data
            structured_profile = self._parse_profile(output)
            return structured_profile
            
        except Exception as e:
            print(f"Error extracting profile from CV: {e}")
            # Fallback to basic extraction if LLM fails
            return self._basic_profile_extraction(cv_text)
    
    def _parse_profile(self, llm_response):
        """Parse LLM response into structured format"""
        # Extract JSON block from response if present
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', llm_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON without code blocks
            json_str = llm_response
        
        try:
            import json
            data = json.loads(json_str)
            
            # Ensure all expected keys are present
            if "name" not in data:
                data["name"] = "Unknown"
                
            if "contact" not in data:
                data["contact"] = {}
            if "email" not in data["contact"]:
                data["contact"]["email"] = ""
            if "phone" not in data["contact"]:
                data["contact"]["phone"] = ""
                
            if "skills" not in data:
                data["skills"] = []
                
            if "experience" not in data:
                data["experience"] = []
                
            if "education" not in data:
                data["education"] = []
                
            return data
            
        except Exception as e:
            print(f"Error parsing LLM response as JSON: {e}")
            # If JSON parsing fails, create a minimal profile with available data
            return {
                "name": self._extract_name(llm_response) or "Unknown",
                "contact": {
                    "email": self._extract_email(llm_response) or "",
                    "phone": self._extract_phone(llm_response) or ""
                },
                "skills": self._extract_skills(llm_response),
                "experience": [],
                "education": []
            }
    
    def _basic_profile_extraction(self, cv_text):
        """Basic extraction of profile information without using LLM"""
        # Extract name (usually at the beginning of a resume)
        name_match = re.search(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})', cv_text)
        name = name_match.group(1) if name_match else "Unknown"
        
        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', cv_text)
        email = email_match.group(0) if email_match else ""
        
        # Extract phone
        phone_match = re.search(r'(?:\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', cv_text)
        phone = phone_match.group(0) if phone_match else ""
        
        # Extract skills (look for "Skills" section and extract words)
        skills_section = re.search(r'(?:Skills|Proficiencies|Abilities)(?::|\.)(.*?)(?:Education|Experience|Reference|$)', 
                                  cv_text, re.IGNORECASE | re.DOTALL)
        
        skills = []
        if skills_section:
            skills_text = skills_section.group(1)
            # Extract skills from bullet points, comma-separated lists, etc.
            skills = re.findall(r'(?:•|\*|\-|\,|\n)\s*([A-Za-z0-9+#]+(?:\s+[A-Za-z0-9+#]+){0,3})', skills_text)
            skills = [s.strip() for s in skills if len(s.strip()) > 2]
        
        # Extract experience (basic - just company names and titles)
        experience = []
        exp_section = re.search(r'(?:Experience|Work Experience|Employment)(?::|\.)(.*?)(?:Education|Skills|References|$)', 
                               cv_text, re.IGNORECASE | re.DOTALL)
        
        if exp_section:
            exp_text = exp_section.group(1)
            # Look for company names (often in ALL CAPS or bold)
            companies = re.findall(r'(?:^|\n)([A-Z][A-Za-z\s,\.]+?(?:Inc|LLC|Ltd|Corp|Corporation|Company)?)\s*(?:,|\n|$)', exp_text)
            
            for i, company in enumerate(companies[:3]):  # Limit to 3 most recent
                experience.append({
                    "company": company.strip(),
                    "title": "Position " + str(i+1),
                    "start_date": "",
                    "end_date": "",
                    "description": ""
                })
        
        # Extract education (basic - just degree and institution)
        education = []
        edu_section = re.search(r'(?:Education|Academic Background|Qualifications)(?::|\.)(.*?)(?:Experience|Skills|References|$)', 
                               cv_text, re.IGNORECASE | re.DOTALL)
        
        if edu_section:
            edu_text = edu_section.group(1)
            # Look for degree names and institutions
            degrees = re.findall(r'(?:Bachelor|Master|PhD|MBA|BS|MS|BA|MD|JD)[^\n,]+(?: of | in )[^\n,]+', edu_text)
            institutions = re.findall(r'(?:University|College|Institute|School) of [A-Za-z\s]+', edu_text)
            
            if degrees:
                education.append({
                    "degree": degrees[0].strip() if degrees else "Degree",
                    "institution": institutions[0].strip() if institutions else "Institution",
                    "year": 0
                })
        
        return {
            "name": name,
            "contact": {
                "email": email,
                "phone": phone
            },
            "skills": skills,
            "experience": experience,
            "education": education
        }
    
    def _extract_name(self, text):
        """Extract candidate name from text"""
        name_match = re.search(r'"name":\s*"([^"]+)"', text)
        return name_match.group(1) if name_match else None
    
    def _extract_email(self, text):
        """Extract email from text"""
        email_match = re.search(r'"email":\s*"([^"]+)"', text)
        return email_match.group(1) if email_match else None
    
    def _extract_phone(self, text):
        """Extract phone from text"""
        phone_match = re.search(r'"phone":\s*"([^"]+)"', text)
        return phone_match.group(1) if phone_match else None
    
    def _extract_skills(self, text):
        """Extract skills from text"""
        skills_match = re.search(r'"skills":\s*\[(.*?)\]', text, re.DOTALL)
        if skills_match:
            skills_text = skills_match.group(1)
            return re.findall(r'"([^"]+)"', skills_text)
        return []
    
    def process_cv(self, candidate_id, cv_text):
        """Process a CV and store profile in the database"""
        profile = self.extract_profile(cv_text)
        store_candidate_profile(candidate_id, profile)
        return profile
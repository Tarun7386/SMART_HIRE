import re
import ollama
from db.database import store_job_requirements

class JDAnalyzer:
    def __init__(self, model_name="mistral"):
        self.model_name = model_name
        
    def extract_requirements(self, job_description):
        """Extract key requirements from job description text"""
        prompt = f"""
        Extract the following information from this job description:
        1. Required skills (list all technical and soft skills)
        2. Years of experience required
        3. Education requirements
        4. Key responsibilities
        
        Format the output as JSON with the following keys:
        "skills": [list of skills],
        "experience": "experience requirement as text",
        "education": "education requirement as text",
        "responsibilities": [list of key responsibilities]
        
        Here is the job description:
        {job_description}
        """
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            
            output = response["message"]["content"]
            
            # Parse the response to extract structured data
            structured_requirements = self._parse_requirements(output)
            return structured_requirements
            
        except Exception as e:
            print(f"Error extracting requirements from job description: {e}")
            # Fallback to basic extraction if LLM fails
            return self._basic_requirements_extraction(job_description)
    
    def _parse_requirements(self, llm_response):
        """Parse LLM response into structured format"""
        # Extract JSON block from response if present
        json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON without code blocks
            json_str = llm_response
        
        try:
            import json
            data = json.loads(json_str)
            # Ensure all expected keys are present
            required_keys = ["skills", "experience", "education", "responsibilities"]
            for key in required_keys:
                if key not in data:
                    data[key] = [] if key in ["skills", "responsibilities"] else ""
            return data
        except:
            # If JSON parsing fails, try to extract requirements manually
            skills = re.findall(r'"skills":\s*\[(.*?)\]', json_str, re.DOTALL)
            skills_list = re.findall(r'"([^"]+)"', skills[0]) if skills else []
            
            experience = re.search(r'"experience":\s*"([^"]+)"', json_str)
            experience_text = experience.group(1) if experience else ""
            
            education = re.search(r'"education":\s*"([^"]+)"', json_str)
            education_text = education.group(1) if education else ""
            
            responsibilities = re.findall(r'"responsibilities":\s*\[(.*?)\]', json_str, re.DOTALL)
            responsibilities_list = re.findall(r'"([^"]+)"', responsibilities[0]) if responsibilities else []
            
            return {
                "skills": skills_list,
                "experience": experience_text,
                "education": education_text,
                "responsibilities": responsibilities_list
            }
    
    def _basic_requirements_extraction(self, job_description):
        """Basic extraction of requirements without using LLM"""
        # Simple regex-based extraction as backup
        skills_section = re.search(r'(?:Requirements|Skills|Qualifications):(.*?)(?:Responsibilities|About Us|Benefits|$)', 
                                  job_description, re.IGNORECASE | re.DOTALL)
        
        skills_text = skills_section.group(1) if skills_section else job_description
        
        # Extract skills using bullet points or common formats
        skills = re.findall(r'(?:•|\*|\-|\d+\.)\s*([A-Za-z0-9+#\s]+)(?:\s*\([^)]+\))?', skills_text)
        skills = [s.strip() for s in skills if len(s.strip()) > 2]
        
        # Try to extract years of experience
        experience = re.search(r'(\d+\+?)\s*(?:-\s*\d+)?\s*years?(?:\s+of)?\s+experience', 
                              job_description, re.IGNORECASE)
        experience_text = f"{experience.group(1)} years" if experience else ""
        
        # Try to extract education
        education = re.search(r'(?:Bachelor|Master|PhD|Degree|BS|MS|BA|MBA)[\'\s]+(?:degree\s+)?(?:in|of|with)?[\s\']+([^,.]+)', 
                             job_description, re.IGNORECASE)
        education_text = education.group(0) if education else ""
        
        # Try to extract responsibilities
        resp_section = re.search(r'(?:Responsibilities|Duties|You will):(.*?)(?:Requirements|Qualifications|Skills|About Us|Benefits|$)', 
                                job_description, re.IGNORECASE | re.DOTALL)
        
        resp_text = resp_section.group(1) if resp_section else ""
        responsibilities = re.findall(r'(?:•|\*|\-|\d+\.)\s*([A-Za-z][^•\*\-\d\.]+)', resp_text)
        responsibilities = [r.strip() for r in responsibilities if len(r.strip()) > 10]
        
        return {
            "skills": skills[:10],  # Limit to top 10 skills for relevance
            "experience": experience_text,
            "education": education_text,
            "responsibilities": responsibilities[:5]  # Limit to top 5 responsibilities
        }
    
    def process_job(self, job_id, job_description):
        """Process a job and store requirements in the database"""
        requirements = self.extract_requirements(job_description)
        store_job_requirements(job_id, requirements)
        return requirements
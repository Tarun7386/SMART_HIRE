class Config:
    """Configuration settings for the Job Screening System"""
    
    # Database settings
    DB_FILE = "recruitment_system.db"
    
    # Ollama settings
    DEFAULT_MODEL = "mistral"
    ALTERNATIVE_MODELS = ["llama2", "gemma", "phi2"]
    
    # Matching settings
    DEFAULT_THRESHOLD = 70.0  # Default match threshold (0-100)
    WEIGHTS = {
        "skills": 0.5,  # Weight of skills score in overall match
        "experience": 0.3,  # Weight of experience score in overall match
        "education": 0.2,  # Weight of education score in overall match
    }
    
    # File handling settings
    SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.txt', '.rtf']
    
    # Interview scheduling settings
    MIN_DAYS_AHEAD = 3  # Minimum days ahead to schedule interviews
    DEFAULT_SLOTS = 3  # Default number of time slots to offer

# File: agents/scheduler.py
# Interview Scheduler Agent

import ollama
import datetime
import re
from db.database import get_shortlisted_candidates, update_interview_status

class InterviewScheduler:
    def __init__(self, model_name="mistral"):
        self.model_name = model_name
        
    def generate_interview_email(self, candidate_name, job_title, company_name):
        """Generate personalized interview invitation email"""
        prompt = f"""
        Write a professional email inviting {candidate_name} for an interview for the {job_title} position at {company_name}. 
        Include the following:
        1. A congratulatory message for being shortlisted
        2. Brief mention of the impressive qualifications
        3. Propose three different time slots next week for the interview
        4. Ask about their preferred interview format (video call, phone, in-person)
        5. Request confirmation
        6. Professional closing
        
        Keep the tone professional but friendly.
        """
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response["message"]["content"]
        except Exception as e:
            print(f"Error generating interview email: {e}")
            # Fallback template
            return f"""
            Subject: Interview Invitation - {job_title} Position at {company_name}
            
            Dear {candidate_name},
            
            Congratulations! We are pleased to inform you that you have been shortlisted for the {job_title} position at {company_name}. Your qualifications and experience impressed our hiring team, and we would like to invite you for an interview.
            
            We would like to schedule the interview for next week. Please let us know which of the following time slots works best for you:
            
            - Monday, 10:00 AM - 11:00 AM
            - Wednesday, 2:00 PM - 3:00 PM
            - Friday, 11:00 AM - 12:00 PM
            
            Additionally, please indicate your preferred interview format (video call, phone call, or in-person).
            
            We look forward to your confirmation and to learning more about your skills and experience.
            
            Best regards,
            Hiring Team
            {company_name}
            """
    
    def generate_interview_slots(self, num_slots=3, start_days_from_now=3):
        """Generate future interview time slots"""
        slots = []
        today = datetime.datetime.now()
        
        for i in range(num_slots):
            # Generate weekday dates (skip weekends)
            days_ahead = start_days_from_now + i
            interview_date = today + datetime.timedelta(days=days_ahead)
            
            # Skip weekends
            while interview_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                interview_date = interview_date + datetime.timedelta(days=1)
            
            # Generate two time slots per day
            morning_slot = datetime.time(10, 0)  # 10:00 AM
            afternoon_slot = datetime.time(14, 0)  # 2:00 PM
            
            slots.append(datetime.datetime.combine(interview_date.date(), morning_slot))
            slots.append(datetime.datetime.combine(interview_date.date(), afternoon_slot))
            
        return slots[:num_slots]  # Return only the requested number of slots
    
    def schedule_interviews(self, job_id, job_title, company_name):
        """Schedule interviews for all shortlisted candidates"""
        shortlisted = get_shortlisted_candidates(job_id)
        
        if not shortlisted:
            print("No candidates were shortlisted for interviews.")
            return []
        
        scheduled_interviews = []
        for candidate in shortlisted:
            # Generate email
            email_content = self.generate_interview_email(
                candidate["name"],
                job_title,
                company_name
            )
            
            # Generate interview slots
            interview_slots = self.generate_interview_slots()
            
            # Format slots as strings
            slot_strings = [slot.strftime("%A, %B %d at %I:%M %p") for slot in interview_slots]
            
            # Update database with proposed slots
            interview_id = update_interview_status(
                job_id=job_id,
                candidate_id=candidate["candidate_id"],
                proposed_dates=slot_strings,
                status="Invitation Sent"
            )
            
            scheduled_interviews.append({
                "interview_id": interview_id,
                "candidate": candidate,
                "email": email_content,
                "proposed_slots": slot_strings
            })
            
        return scheduled_interviews
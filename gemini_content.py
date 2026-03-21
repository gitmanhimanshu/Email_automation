"""Gemini API Content Generation Module"""
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiContentGenerator:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def generate_email_content(self, name, company, resume_link, your_name, job_position=None):
        """Generate personalized email content using Gemini"""
        
        # Build prompt based on available data
        if job_position:
            prompt = f"""
            Write a professional job application email with these details:
            - Recipient name: {name}
            - Company: {company}
            - Job Position: {job_position}
            - Resume link: {resume_link}
            - Sender name: {your_name}
            
            Requirements:
            - Keep it concise (under 150 words)
            - Professional but friendly tone
            - Mention the specific job position
            - Highlight relevant skills for this role
            - Include the resume link naturally
            - End with proper signature
            
            Return ONLY the email body, no subject line.
            """
        else:
            prompt = f"""
            Write a professional job application email with these details:
            - Recipient name: {name}
            - Company: {company}
            - Resume link: {resume_link}
            - Sender name: {your_name}
            
            Requirements:
            - Keep it concise (under 150 words)
            - Professional but friendly tone
            - Express general interest in opportunities
            - Include the resume link naturally
            - End with proper signature
            
            Return ONLY the email body, no subject line.
            """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            # Fallback to simple template if Gemini fails
            print(f"⚠️ Gemini API error: {e}. Using fallback template.")
            return self._fallback_template(name, company, resume_link, your_name, job_position)
    
    def _fallback_template(self, name, company, resume_link, your_name, job_position=None):
        """Simple fallback template if Gemini fails - uses same data"""
        if job_position:
            return f"""Hi {name},

I hope this email finds you well.

I am writing to express my interest in the {job_position} position at {company}. I believe my skills and experience align well with this role.

Please find my resume here: {resume_link}

I would love to discuss how I can contribute to {company}'s success in this position.

Thank you for your time and consideration.

Best regards,
{your_name}"""
        else:
            return f"""Hi {name},

I hope this email finds you well.

I am writing to express my interest in opportunities at {company}. I believe my skills and experience would be a great fit for your team.

Please find my resume here: {resume_link}

I would love to discuss how I can contribute to {company}'s success.

Thank you for your time and consideration.

Best regards,
{your_name}"""

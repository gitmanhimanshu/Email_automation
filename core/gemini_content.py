"""Gemini-written email bodies, for the CLI and Flask app.

The MCP server never imports this. There, Claude writes the email itself and
already knows the user's background from the conversation, so a second model
behind a fixed prompt would only make the result worse.
"""
from . import config


class GeminiContentGenerator:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or config.gemini_api_key()
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not set. Add it to .env — get one at "
                "https://aistudio.google.com/app/apikey"
            )

        # Imported lazily so the MCP server, which has no use for Gemini, does
        # not need google-generativeai installed at all.
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        self.model_name = model or config.gemini_model()
        self.model = genai.GenerativeModel(self.model_name)

    def generate_email_content(self, name, company, resume_link, your_name, job_position=None):
        role_line = f"- Job position: {job_position}\n" if job_position else ""
        intent = (
            f"Express interest in the {job_position} role specifically."
            if job_position
            else "Express general interest in opportunities at the company."
        )

        prompt = (
            "Write the body of a professional job application email.\n"
            f"- Recipient name: {name}\n"
            f"- Company: {company}\n"
            f"{role_line}"
            f"- Resume link: {resume_link}\n"
            f"- Sender name: {your_name}\n\n"
            "Requirements:\n"
            "- Under 150 words\n"
            "- Professional but warm; no buzzwords or filler\n"
            f"- {intent}\n"
            "- Work the resume link in naturally\n"
            f"- Sign off as {your_name}\n\n"
            "Return only the email body. No subject line, no markdown."
        )

        try:
            response = self.model.generate_content(prompt)
            text = (response.text or "").strip()
            if not text:
                raise ValueError("Gemini returned an empty response")
            return text
        except Exception as exc:
            # Never let a flaky API stop a campaign — fall back to the template.
            print(f"Gemini unavailable ({exc}); using the fallback template.")
            return self._fallback_template(name, company, resume_link, your_name, job_position)

    def _fallback_template(self, name, company, resume_link, your_name, job_position=None):
        if job_position:
            opening = (
                f"I am writing to express my interest in the {job_position} position "
                f"at {company}. I believe my skills and experience align well with this role."
            )
            closing = f"I would love to discuss how I can contribute to {company} in this position."
        else:
            opening = (
                f"I am writing to express my interest in opportunities at {company}. "
                "I believe my skills and experience would be a good fit for your team."
            )
            closing = f"I would love to discuss how I can contribute to {company}."

        return (
            f"Hi {name},\n\n"
            "I hope this email finds you well.\n\n"
            f"{opening}\n\n"
            f"Please find my resume here: {resume_link}\n\n"
            f"{closing}\n\n"
            "Thank you for your time and consideration.\n\n"
            "Best regards,\n"
            f"{your_name}"
        )


def subject_for(company, job_position=None):
    """The one place subject lines are built, so every entry point matches."""
    if job_position:
        return f"Application for {job_position} at {company}"
    return f"Application for Opportunities at {company}"

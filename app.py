"""Flask web interface — the standalone mode, with Gemini writing the emails.

This is the no-MCP path: there is no model in the loop, so Gemini generates the
content. If you drive the tool from Claude instead, use the MCP server, which
skips Gemini entirely.
"""
import time

from dotenv import load_dotenv, set_key
from flask import Flask, jsonify, render_template, request

from core import config, gmail_auth, sent_log
from core.email_sender import EmailSender
from core.gemini_content import GeminiContentGenerator, subject_for
from core.sheets_reader import SheetsReader

app = Flask(__name__)

ENV_PATH = config.PROJECT_ROOT / ".env"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify(
        {
            "resume_link": config.resume_link(),
            "your_name": config.your_name(),
            "your_email": config.your_email(),
            "email_delay": config.email_delay(),
            "gemini_configured": bool(config.gemini_api_key()),
            "gmail_authorized": gmail_auth.has_token(),
        }
    )


@app.route("/api/config", methods=["POST"])
def update_config():
    data = request.json or {}
    fields = {
        "resume_link": "RESUME_LINK",
        "your_name": "YOUR_NAME",
        "your_email": "YOUR_EMAIL",
        "email_delay": "EMAIL_DELAY",
        "gemini_api_key": "GEMINI_API_KEY",
    }

    try:
        ENV_PATH.touch(exist_ok=True)
        for key, env_var in fields.items():
            if key in data and data[key] not in (None, ""):
                set_key(str(ENV_PATH), env_var, str(data[key]))
        load_dotenv(ENV_PATH, override=True)
        return jsonify({"success": True, "message": "Configuration updated"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/preview", methods=["POST"])
def preview_email():
    data = request.json or {}
    try:
        gemini = GeminiContentGenerator()
        job_position = data.get("job_position")
        body = gemini.generate_email_content(
            data["name"],
            data["company"],
            data.get("resume_link") or config.resume_link(),
            config.your_name(),
            job_position,
        )
        return jsonify(
            {
                "success": True,
                "content": body,
                "subject": subject_for(data["company"], job_position),
            }
        )
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/sheet/preview", methods=["POST"])
def preview_sheet():
    sheet_url = (request.json or {}).get("sheet_url")
    if not sheet_url:
        return jsonify({"success": False, "error": "Sheet URL not provided"}), 400

    try:
        reader = SheetsReader(sheet_url)
        recipients = reader.validate_records(reader.read_public_sheet())
        return jsonify({"success": True, "count": len(recipients), "recipients": recipients})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/send", methods=["POST"])
def send_emails():
    recipients = (request.json or {}).get("recipients", [])
    if not recipients:
        return jsonify({"success": False, "error": "No recipients provided"}), 400

    missing = config.missing_profile_fields()
    if missing:
        return jsonify({"success": False, "error": f"Missing in .env: {', '.join(missing)}"}), 400

    try:
        sender = EmailSender(gmail_auth.get_service(allow_browser=True), config.your_email())
        gemini = GeminiContentGenerator()
        delay = config.email_delay()

        results = []
        for index, recipient in enumerate(recipients):
            job_position = recipient.get("job_position")
            body = gemini.generate_email_content(
                recipient["name"],
                recipient["company"],
                recipient.get("resume_link") or config.resume_link(),
                config.your_name(),
                job_position,
            )
            result = sender.send(
                recipient["email"],
                subject_for(recipient["company"], job_position),
                body,
            )
            results.append({**result, "name": recipient["name"], "company": recipient["company"]})

            if index < len(recipients) - 1 and delay:
                time.sleep(delay)

        sent_log.record(results)
        succeeded = sum(1 for r in results if r["success"])

        return jsonify(
            {
                "success": True,
                "total": len(results),
                "successful": succeeded,
                "failed": len(results) - succeeded,
                "results": results,
            }
        )
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/test", methods=["POST"])
def test_email():
    your_email = config.your_email()
    if not your_email:
        return jsonify({"success": False, "error": "YOUR_EMAIL is not set in .env"}), 400

    try:
        sender = EmailSender(gmail_auth.get_service(allow_browser=True), your_email)
        gemini = GeminiContentGenerator()
        body = gemini.generate_email_content(
            "Test User",
            "Test Company",
            config.resume_link(),
            config.your_name(),
            "Software Engineer",
        )
        result = sender.send(your_email, "Test: Email Automation System", body)

        if not result["success"]:
            return jsonify({"success": False, "error": result["error"]}), 500

        return jsonify(
            {"success": True, "message": f"Test email sent to {your_email}", "content": body}
        )
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)

"""Google Sheets Reader Module - Public Sheet Support"""
import re
import requests
import csv
from io import StringIO

class SheetsReader:
    def __init__(self, sheet_url=None):
        self.sheet_url = sheet_url
    
    def extract_sheet_id(self, url):
        """Extract sheet ID from Google Sheets URL"""
        patterns = [
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'key=([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError("Invalid Google Sheets URL")
    
    def read_public_sheet(self, sheet_url=None):
        """Read data from public Google Sheet (no authentication needed)"""
        url = sheet_url or self.sheet_url
        
        if not url:
            raise ValueError("Sheet URL not provided")
        
        try:
            # Extract sheet ID
            sheet_id = self.extract_sheet_id(url)
            
            # Convert to CSV export URL
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            
            # Fetch CSV data
            response = requests.get(csv_url)
            response.raise_for_status()
            
            # Parse CSV
            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)
            records = list(reader)
            
            # Clean up records (remove empty rows)
            records = [r for r in records if any(r.values())]
            
            return records
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching sheet: {str(e)}. Make sure sheet is public!")
        except Exception as e:
            raise Exception(f"Error reading sheet: {str(e)}")
    
    def validate_records(self, records):
        """Validate and normalize records with flexible column matching"""
        if not records:
            raise ValueError("Sheet is empty or no data found")
        
        first_record = records[0]
        
        # Find email column
        email_col = None
        for col in first_record.keys():
            if 'email' in col.lower() or 'mail' in col.lower():
                email_col = col
                break
        
        if not email_col:
            raise ValueError("No email column found. Sheet must have an 'email' column")
        
        # Normalize records to standard format
        normalized = []
        for record in records:
            # Find name column (flexible)
            name = None
            for key in record.keys():
                if 'name' in key.lower():
                    name = record[key]
                    break
            
            # Find company column (flexible)
            company = None
            for key in record.keys():
                if 'company' in key.lower() or 'organization' in key.lower():
                    company = record[key]
                    break
            
            # Find job position column (flexible)
            job_position = None
            for key in record.keys():
                if 'position' in key.lower() or 'role' in key.lower() or 'job' in key.lower():
                    job_position = record[key]
                    break
            
            # Find resume link column (flexible)
            resume_link = None
            for key in record.keys():
                if 'resume' in key.lower() or 'cv' in key.lower() or 'link' in key.lower():
                    resume_link = record[key]
                    break
            
            email = record.get(email_col, '').strip()
            
            if email:  # Only include rows with email
                normalized.append({
                    'name': name or 'There',
                    'email': email,
                    'company': company or 'your organization',
                    'job_position': job_position or None,
                    'resume_link': resume_link or None
                })
        
        if not normalized:
            raise ValueError("No valid email addresses found in sheet")
        
        return normalized

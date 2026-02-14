import requests
import openai
from typing import List
import json

def extract_skills_with_llm(text: str, api_key: str) -> List[str]:
    """Use LLM to extract skills from resume text."""
    if not text.strip():
        return []
    openai.api_key = api_key
    prompt = f"""
    From the following resume text, extract a list of technical and professional skills.
    Return only a JSON list of strings, e.g. ["Python", "Machine Learning", "Project Management"].
    Do not include any other text.
    Text: {text[:2000]}  # Limit to avoid token overflow
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300
        )
        content = response.choices[0].message.content.strip()
        # Attempt to parse JSON list
        if content.startswith('[') and content.endswith(']'):
            return json.loads(content)
        else:
            # Fallback: try to find list in text
            import re
            matches = re.findall(r'"(.*?)"', content)
            if matches:
                return matches
            return []
    except:
        return []

def fetch_github_skills(username: str) -> List[str]:
    """Fetch languages and topics from user's public repos."""
    skills = set()
    # Get repos
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
    try:
        resp = requests.get(repos_url)
        if resp.status_code != 200:
            return []
        repos = resp.json()
        for repo in repos:
            # languages
            lang = repo.get("language")
            if lang:
                skills.add(lang)
            # topics (requires special Accept header)
            topics_url = f"https://api.github.com/repos/{username}/{repo['name']}/topics"
            headers = {"Accept": "application/vnd.github.mercy-preview+json"}
            topics_resp = requests.get(topics_url, headers=headers)
            if topics_resp.status_code == 200:
                topics = topics_resp.json().get("names", [])
                skills.update(topics)
    except:
        pass
    return list(skills)

def get_job_requirements(role: str) -> dict:
    """Mock function – in production you'd query a dataset or an API."""
    mock_db = {
        "Data Scientist": {
            "description": "Analyze data, build models, deploy solutions.",
            "skills": ["Python", "SQL", "Machine Learning", "Statistics", "Pandas", "Scikit-learn", "TensorFlow", "Data Visualization", "Big Data", "Communication"]
        },
        "Frontend Developer": {
            "description": "Build responsive web interfaces.",
            "skills": ["HTML", "CSS", "JavaScript", "React", "Responsive Design", "Version Control", "Web Performance", "Testing", "Browser DevTools", "APIs"]
        },
        "Backend Developer": {
            "description": "Develop server-side logic, APIs, and databases.",
            "skills": ["Python", "Java", "Node.js", "SQL", "NoSQL", "REST APIs", "Docker", "Cloud Services", "Authentication", "Testing"]
        },
        "DevOps Engineer": {
            "description": "Manage infrastructure, CI/CD, and automation.",
            "skills": ["Linux", "Docker", "Kubernetes", "CI/CD", "Cloud (AWS/Azure/GCP)", "Infrastructure as Code", "Monitoring", "Scripting", "Networking", "Security"]
        },
        "Machine Learning Engineer": {
            "description": "Build and deploy ML models.",
            "skills": ["Python", "Machine Learning", "Deep Learning", "TensorFlow/PyTorch", "SQL", "Data Processing", "Model Deployment", "MLOps", "Statistics", "Cloud ML"]
        }
    }
    return mock_db.get(role, {"description": "", "skills": []})
import os
import json
from typing import List, Dict, Any
import openai
from utils import extract_skills_with_llm, fetch_github_skills, get_job_requirements

class CareerNavigatorAgent:
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        openai.api_key = self.openai_api_key

    def run(self, resume_text: str, github_username: str, dream_role: str) -> Dict[str, Any]:
        try:
            # Step 1: Extract skills from resume and GitHub
            profile_skills = self._extract_profile_skills(resume_text, github_username)

            # Step 2: Get job requirements for dream role
            job_req = self._get_role_requirements(dream_role)
            required_skills = job_req.get("skills", [])

            # Step 3: Identify gaps
            gaps = self._identify_gaps(profile_skills, required_skills)

            # Step 4: Generate 30-day roadmap
            roadmap = self._generate_roadmap(gaps, profile_skills, required_skills, dream_role)

            return {
                "profile_skills": profile_skills,
                "job_requirements": job_req,
                "gaps": gaps,
                "roadmap": roadmap
            }
        except Exception as e:
            return {"error": str(e)}

    def _extract_profile_skills(self, resume_text: str, github_username: str) -> List[str]:
        skills = set()
        # from resume
        if resume_text and resume_text.strip():
            resume_skills = extract_skills_with_llm(resume_text, self.openai_api_key)
            if resume_skills:
                skills.update(resume_skills)
        # from GitHub
        if github_username and github_username.strip():
            github_skills = fetch_github_skills(github_username)
            if github_skills:
                skills.update(github_skills)
        return list(skills)

    def _get_role_requirements(self, dream_role: str) -> Dict[str, Any]:
        # First try to get from mock database
        mock_req = get_job_requirements(dream_role)
        if mock_req.get("skills"):
            return mock_req

        # If not found, use LLM to generate requirements
        prompt = f"""
        Provide a concise job description for a '{dream_role}' position.
        List the top 10 technical skills required, in a JSON format like:
        {{"description": "...", "skills": ["skill1", "skill2", ...]}}
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except:
            return {"description": "", "skills": []}

    def _identify_gaps(self, profile_skills: List[str], required_skills: List[str]) -> Dict[str, List[str]]:
        if not required_skills:
            return {"missing": [], "partial": []}
        prompt = f"""
        Profile skills: {profile_skills}
        Required skills for dream role: {required_skills}

        Identify:
        1. Missing skills (required but not in profile)
        2. Partial matches (profile has related but not exact skills)
        Return JSON: {{"missing": [...], "partial": [...]}}
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except:
            return {"missing": [], "partial": []}

    def _generate_roadmap(self, gaps: Dict, profile_skills: List, required: List, role: str) -> Dict:
        prompt = f"""
        You are a career coach. Create a 30-day "vibe check" learning roadmap for a student aiming to become a {role}.
        Their current skills: {profile_skills}
        They need to acquire: {gaps.get('missing', [])} and strengthen: {gaps.get('partial', [])}

        The roadmap should be a JSON with keys "day_1" through "day_30", each day having:
        - "task": a short description (1 sentence)
        - "resource": a link or reference (use real URLs like YouTube, freeCodeCamp, MDN, etc.)
        - "project": a mini project idea (or "none")
        - "checkpoint": a self-evaluation question

        Also include a weekly summary after day 7, 14, 21, 28 as "week_1_summary", etc. with reflection questions.
        The plan should be realistic, project-based, and help the student build a portfolio.
        Return valid JSON only. Do not include any additional text.
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=2500
            )
            content = response.choices[0].message.content
            # Sometimes the model returns extra text; try to extract JSON
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                content = content[start:end]
            return json.loads(content)
        except Exception as e:
            return {"error": f"Could not generate roadmap: {str(e)}"}
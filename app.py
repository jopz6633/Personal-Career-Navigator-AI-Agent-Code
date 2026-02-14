import streamlit as st
from agent import CareerNavigatorAgent
import os
from dotenv import load_dotenv
import PyPDF2
import io

load_dotenv()

st.set_page_config(page_title="Personal Career Navigator", layout="wide")
st.title("🧭 The Personal Career Navigator")
st.markdown("Upload your resume, connect your GitHub, and choose your dream role to get a personalized 30-day learning roadmap.")

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    if not api_key:
        st.warning("Please enter your OpenAI API key to proceed.")
        st.stop()

    st.markdown("---")
    st.header("Your Profile")
    resume_file = st.file_uploader("Upload Resume (TXT or PDF)", type=["txt", "pdf"])
    resume_text = ""
    if resume_file is not None:
        if resume_file.type == "text/plain":
            resume_text = resume_file.read().decode("utf-8")
        elif resume_file.type == "application/pdf":
            resume_text = extract_text_from_pdf(resume_file)
        else:
            st.info("Unsupported file type. Please upload a TXT or PDF.")
            resume_text = st.text_area("Or paste resume text", height=200)
    else:
        resume_text = st.text_area("Paste your resume text here", height=200)

    github_user = st.text_input("GitHub Username (optional)")

    dream_role = st.selectbox("Select your dream role", 
                              ["Data Scientist", "Frontend Developer", "Backend Developer", "DevOps Engineer", "Machine Learning Engineer", "Other (specify below)"])
    if dream_role == "Other (specify below)":
        dream_role = st.text_input("Enter your dream role")

    if st.button("Generate My Roadmap"):
        st.session_state.run_agent = True

if "run_agent" in st.session_state and st.session_state.run_agent:
    if not resume_text.strip() and not github_user:
        st.error("Please provide either a resume or GitHub username.")
        st.stop()

    with st.spinner("Analyzing your profile and building your personalized roadmap..."):
        agent = CareerNavigatorAgent(openai_api_key=api_key)
        result = agent.run(resume_text, github_user, dream_role)

    if "error" in result:
        st.error(f"An error occurred: {result['error']}")
        st.stop()

    st.success("Roadmap generated!")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Your Identified Skills")
        st.write(result["profile_skills"])

        st.subheader("🎯 Required Skills for " + dream_role)
        st.write(result["job_requirements"].get("skills", []))

    with col2:
        st.subheader("🔍 Skill Gaps")
        missing = result["gaps"].get("missing", [])
        partial = result["gaps"].get("partial", [])
        st.markdown(f"**Missing:** {', '.join(missing) if missing else 'None'}")
        st.markdown(f"**Partial matches:** {', '.join(partial) if partial else 'None'}")

    st.subheader("🗓️ Your 30‑Day Learning Roadmap")
    roadmap = result.get("roadmap", {})
    if "error" in roadmap:
        st.error(roadmap["error"])
    else:
        # Display as expandable days
        for day in range(1, 31):
            day_key = f"day_{day}"
            if day_key in roadmap:
                day_data = roadmap[day_key]
                with st.expander(f"Day {day}: {day_data.get('task', '')}"):
                    st.markdown(f"**Task:** {day_data.get('task', '')}")
                    st.markdown(f"**Resource:** {day_data.get('resource', '')}")
                    st.markdown(f"**Project:** {day_data.get('project', 'none')}")
                    st.markdown(f"**Checkpoint:** {day_data.get('checkpoint', '')}")
            else:
                st.write(f"Day {day}: No data")

    st.subheader("🔄 How This Agent Adapts Over Time")
    st.markdown("""
    - **Initial Personalization:** The roadmap is tailored using your resume and GitHub skills.
    - **Progress Tracking:** You can mark days as completed (feature to be implemented). The agent would then adjust future days based on your pace.
    - **Mid‑point Reassessment:** After 15 days, you can re‑upload your latest projects. The agent re‑extracts skills from them and updates the remaining roadmap.
    - **Market Alignment:** Job requirements are refreshed weekly (simulated) to reflect current trends.
    """)

    st.balloons()
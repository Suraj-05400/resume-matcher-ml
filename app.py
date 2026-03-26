import streamlit as st
from utils import extract_resume, clean_text, detect_skills, extract_experience, extract_education
from model import match_resumes
import matplotlib.pyplot as plt
import pandas as pd
from streamlit_lottie import st_lottie
import requests

#---Page setting---
st.set_page_config(page_title="AI Resume Matcher", layout="wide")

#---Load lottie---
@st.cache_data
def load_lottie(url):
    try:
        r = requests.get(url)
        return r.json()
    except:
        return None

lottie_ai = load_lottie("https://assets10.lottiefiles.com/packages/lf20_qp1q7mct.json")

#---Custom UI---
st.markdown("""
<style>
.main {
    background-color: #0E1117;
    color: white;
}
.header {
    font-size: 42px;
    font-weight: bold;
    background: linear-gradient(-45deg, #00ADB5, #3A86FF, #8338EC, #FF006E);
    background-size: 400% 400%;
    animation: gradient 10s ease infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
}
@keyframes gradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
.stButton>button {
    background: linear-gradient(45deg,#00ADB5,#3A86FF);
    color: white;
    font-size: 16px;
    border-radius: 10px;
    height: 3em;
    width: 100%;
}
.rank-card {
    background-color: #1F2937;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

#---Header---
st.markdown('<div class="header">🤖 AI Resume Matcher Dashboard</div>', unsafe_allow_html=True)
st.caption("🚀 Automated Resume Screening & Ranking System")

if lottie_ai:
    st_lottie(lottie_ai, height=220)

#---Side Bar---
st.sidebar.title("📂 Control Panel")

uploaded_files = st.sidebar.file_uploader(
    "📄 Upload Multiple Resumes",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

st.sidebar.markdown("📌 Instructions")
st.sidebar.write("1️. Upload resumes")
st.sidebar.write("2️. Paste job description")
st.sidebar.write("3️.Click Match Resumes")

#---Job Description---
job_description = st.text_area("💼 Paste Job Description Here")

#---Resume---
@st.cache_data
def process_resume(file):
    text = extract_resume(file)
    cleaned = clean_text(text)
    skills = detect_skills(cleaned)
    exp_years = extract_experience(cleaned)
    edu_score = extract_education(cleaned)
    return cleaned, skills, exp_years, edu_score

#---Match Button---
if st.button("🚀 Match Resumes"):

    if uploaded_files and job_description:

        with st.spinner("🤖 AI is analyzing resumes..."):

            cleaned_resumes = []
            resume_names = []
            resume_skills = []
            resume_experience = []
            resume_education = []

            progress = st.progress(0)

            for i, file in enumerate(uploaded_files):

                cleaned, skills, exp, edu = process_resume(file)

                cleaned_resumes.append(cleaned)
                resume_names.append(file.name)
                resume_skills.append(skills)
                resume_experience.append(exp)
                resume_education.append(edu)

                progress.progress((i + 1) / len(uploaded_files))

            cleaned_job = clean_text(job_description)
            job_skills = detect_skills(cleaned_job)
            job_required_exp = extract_experience(cleaned_job)
            job_required_edu = extract_education(cleaned_job)

            similarity_scores = match_resumes(cleaned_resumes, cleaned_job)

        #---ATS Score---
        final_scores = []
        missing_skills_list = []
        skill_match_percent = []

        for i, sim_score in enumerate(similarity_scores):

            candidate_skills = resume_skills[i]
            semantic_score = sim_score

            if job_skills:
                matched = set(candidate_skills) & set(job_skills)
                skill_match = len(matched) / len(job_skills)
                skill_percent = round(skill_match * 100, 2)
                missing = list(set(job_skills) - set(candidate_skills))
            else:
                skill_match = 0
                skill_percent = 0
                missing = []

            skill_match_percent.append(skill_percent)

            if missing:
                missing_skills_list.append(", ".join(missing))
            else:
                missing_skills_list.append("None")

            if job_required_exp > 0:
                experience_score = min(resume_experience[i] / job_required_exp, 1)
            else:
                experience_score = 1

            if job_required_edu > 0:
                education_score = min(resume_education[i] / job_required_edu, 1)
            else:
                education_score = 1

            final_score = (
                0.4 * semantic_score +
                0.3* skill_match +
                0.2 * experience_score +
                0.2 * education_score
            )

            final_scores.append(final_score)

        #---Dashboard---
        st.subheader("📊 Hiring Insights Dashboard")

        col1, col2, col3 = st.columns(3)

        col1.metric("📄 Total Resumes", len(resume_names))
        col2.metric("🏆 Top Match Score", f"{round(max(final_scores)*100,2)}%")
        col3.metric("📈 Average Match", f"{round(sum(final_scores)/len(final_scores)*100,2)}%")

        #---Showing Best Candidate---
        best_index = final_scores.index(max(final_scores))

        st.success(
            f"🏆 Best Candidate: {resume_names[best_index]} "
            f"with ATS Score {round(final_scores[best_index]*100,2)}%"
        )

        st.markdown("---")

        #---Show Ranking---
        st.subheader("🎖️ Candidate Ranking")

        ranking = sorted(zip(resume_names, final_scores), key=lambda x: x[1], reverse=True)

        recommendations = []

        for rank, (name, score) in enumerate(ranking, start=1):

            if score >= 0.75:
                decision = "✅ Hire Candidate"
            elif score >= 0.45:
                decision = "💡 Shortlist"
            else:
                decision = "❌ Reject"

            recommendations.append(decision)

            st.markdown(f"""
            <div class="rank-card">
                <h4>🏅 Rank {rank}: {name}</h4>
                <p>📊 ATS Score: <b>{round(score*100,2)}%</b></p>
                <p>🧾 Recommendation: <b>{decision}</b></p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        #---Show Skills---
        st.subheader("🔎 Detected Skills")

        for name, skills in zip(resume_names, resume_skills):
            st.write(f"👤 {name}: {', '.join(skills) if skills else '⚠️ No major skills found'}")

        st.markdown("---")

        #---Show Pie Chart---
        st.subheader("📊 Resume Match Distribution")

        labels = resume_names
        values = [float(score) for score in final_scores]

        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
        ax.axis('equal')
        st.pyplot(fig)

        st.markdown("---")

        #---Dashboard Board---
        st.subheader("⬇ Download Hiring Report")

        df = pd.DataFrame({
            "Resume": resume_names,
            "ATS Score (%)": [round(s*100,2) for s in final_scores],
            "Skill Match (%)": skill_match_percent,
            "Skills": [", ".join(sk) for sk in resume_skills],
            "Missing Skills": missing_skills_list,
            "Recommendation": recommendations
        })
        
        st.dataframe(df)

        st.download_button(
            label="📥 Download CSV Report",
            data=df.to_csv(index=False),
            file_name="resume_matching_report.csv",
            mime="text/csv"
        )

    else:
        st.warning("⚠️ Please upload resumes and enter job description.")

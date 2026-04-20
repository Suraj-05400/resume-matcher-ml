import streamlit as st
#from streamlit.runtime.uploaded_file_manager import UploadedFile
from utils import extract_resume, clean_text, detect_skills, extract_experience, extract_education
from model import match_resumes
import matplotlib.pyplot as plt
import pandas as pd
from streamlit_lottie import st_lottie
import requests
import json
import hashlib

# Set page config
st.set_page_config(page_title="AI Resume Matcher", layout="wide")

# -------------------- USER DB --------------------
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------- SESSION --------------------
if "logged_in" not in st.session_state:
    if "show_landing" not in st.session_state:
        st.session_state.show_landing = True
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user = None

# -------------------- LOTTIE --------------------
@st.cache_data
def load_lottie(url):
    try:
        return requests.get(url).json()
    except:
        return None

lottie_ai = load_lottie("https://assets10.lottiefiles.com/packages/lf20_kyu7xb1v.json")

#---------------------Custom UI---------------------
st.markdown("""
<style>
.stApp {
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

col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.divider()
    


#-------------------------AUTH UI--------------------------
st.markdown("""
<style>
.auth-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 80vh;
}
.auth-box {
    background: rgba(255, 255, 255, 0.05);
    padding: 40px;
    border-radius: 20px;
    backdrop-filter: blur(15px);
    width: 400px;
    box-shadow: 0 0 40px rgba(0,0,0,0.3);
}
.toggle-btn {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LANDING PAGE ----------------
if not st.session_state.logged_in and st.session_state.show_landing:

    st.markdown("""
    <style>
    .hero {
        text-align: center;
        padding: 80px 20px;
    }
    .hero h1 {
        font-size: 55px;
        background: linear-gradient(90deg,#00ADB5,#3A86FF,#8338EC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero p {
        font-size: 20px;
        color: #aaa;
    }
    .feature {
        background: #1F2937;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # Title
    st.markdown("""
    <div class="hero">
        <h1>🤖 AI Resume Matcher</h1>
        <p>Smart Hiring with AI for HR Professionals</p>
        <p>Automate Resume Screening & Job Recommendation Systems</p>
    </div>
    """, unsafe_allow_html=True)

    # Button
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if st.button("🚀 Get Started"):
            st.session_state.show_landing = False
            st.rerun()

    st.markdown("---")

    # Features
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="feature">📊 ATS Scoring</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="feature">🤖 AI Matching</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="feature">⚡ Fast Hiring</div>', unsafe_allow_html=True)

    st.stop()
    
#----------------------------------------- AUTHENTICATION ------------------------------------------------------
if not st.session_state.logged_in:

    st.markdown('<div class="header">🔐 Welcome to AI Resume Matcher</div>', unsafe_allow_html=True)

    #tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    default_tab = 0 if st.session_state.get("switch_to_login") else 1
    col1, col2 = st.columns(2)

    if "switch_to_login" in st.session_state:
        st.session_state.pop("switch_to_login")

    users = load_users()
    #if st.session_state.get("registered_success"):
    #  st.success("🎉 Registration successful! Please login.")
    #  del st.session_state["registered_success"]

    # ---------------- LOGIN ----------------
    with col1:
        if st.session_state.get("registered_success"):
            st.success("🎉 Registration successful! Please login.")
            del st.session_state["registered_success"]

        st.subheader("Login to your account")

        email = st.text_input("Email/Username", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login",key="login_btn", use_container_width=True):

            if email in users and users[email]["password"] == hash_password(password):

                st.session_state.logged_in = True
                st.session_state.role = users[email]["role"]
                st.session_state.user = email

                st.success("Login successful ✅")
                st.rerun()

            else:
                st.error("Invalid email or password ❌ Please Register first")

    # ---------------- REGISTER ----------------
    with col2:
        st.subheader("Create a new account")

        email = st.text_input("Email/Username", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_pass")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_pass")

        role = st.selectbox("Select Role", ["HR", "Job Seeker"], key="reg_role")

        if st.button("Register", key="register_btn", use_container_width=True):

            if email in users:
                st.warning("User already exists ⚠️")

            elif password != confirm_password:
                st.error("Passwords do not match ❌")

            elif len(password) < 6:
                st.warning("Password must be at least 6 characters")
            
            elif email.strip() == "":
                st.error("Email cannot be empty")

            else:
                users[email] = {
                    "password": hash_password(password),
                    "role": role
                }

                save_users(users)

                #st.success("Registered successfully 🎉 Please login")
                st.session_state["registered_success"] = True
                
                # Auto switch to login tab
                st.session_state["auth_mode"] = True
                st.rerun()

# ----------------------------------------- MAIN APP ------------------------------------------------------
else:

    st.sidebar.write(f"👤 {st.session_state.user}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False #Important Fix
        st.session_state.role = None
        st.session_state.user = None
        st.rerun()

    role = st.session_state.role
    #role = st.sidebar.selectbox("Select Role", ["HR", "Job Seeker"])

    #---Header---
    st.markdown('<div class="header">🤖 AI Resume Matcher Dashboard</div>', unsafe_allow_html=True)
    st.caption("🚀 Automated Resume Screening & Ranking System")

    if lottie_ai:
        st_lottie(lottie_ai, height=220)

    #------------------------this is the Job seeker dashboard----------------------------------
    if role == "Job Seeker":

        st.sidebar.subheader("📂 Job Seeker Dashboard")
        st.sidebar.markdown("📌 Instructions")
        st.sidebar.write("1️. Upload your resume")
        st.sidebar.write("2️. Paste job description")
        st.sidebar.write("3️. Click Analyze Resume")

        resume = st.file_uploader("Upload Resume", type=["pdf", "docx"])
        jd = st.text_area("Paste Job Description")

        if st.button("Analyze Resume", key="jobseeker_btn"):

            if resume and jd:

                text = extract_resume(resume)
                cleaned = clean_text(text)

                skills = detect_skills(cleaned)

                cleaned_jd = clean_text(jd)
                jd_skills = detect_skills(cleaned_jd)

                skills_set = set([s.lower() for s in skills])
                jd_set = set([s.lower() for s in jd_skills])

                matched = list(skills_set & jd_set)
                missing = list(jd_set - skills_set)

                if jd_skills:
                    ats = int((len(matched) / len(jd_skills)) * 100)
                else:
                    ats = 0

                st.metric("📊 ATS Score", f"{ats}%")

                st.write("✅ Matched Skills:", matched)
                st.write("❌ Missing Skills:", missing)

                st.subheader("💡 Suggestions")
                st.write("- Add missing skills")
                st.write("- Add projects")
                st.write("- Add certifications")
                st.write("- Tailor resume for each job")

                # Job Recommendation
                if ats < 60:
                    st.subheader("🔍 Recommended Jobs")

                    jobs = {
                        "Data Analyst": ["python", "sql", "excel", "tableau", "power bi"],
                        "Frontend Developer": ["react", "html","css", "javascript", "vue","angular"],
                        "Backend Developer": ["python", "django","flask","java", "spring", "nodejs","express", "sql", "mongodb","aws"],
                        "Data Scientist": ["python", "r", "machine learning", "deep learning", "nlp", "statistics", "sql"],
                        "Project Manager": ["project management", "agile", "scrum", "communication", "leadership"],
                    }

                    for job, req in jobs.items():
                        if len(set(req) & skills_set) > 0:
                            st.write("👉", job)

            else:
                st.warning("Upload resume and enter job description")
            
    #---Side Bar------------------this is the HR dashboard-------------------------------------
    elif role == "HR":
        st.sidebar.subheader("📂 HR Control")

        uploaded_files = st.sidebar.file_uploader(   #Important Fix: add at.sidebar if you want upload button to be palced at sidebar
            "📄 Upload Multiple Resumes",
            type=["pdf", "docx"],
            accept_multiple_files=True
        )

        st.sidebar.markdown("📌 Instructions")
        st.sidebar.write("1️. Upload Multiple Resumes")
        st.sidebar.write("2️. Paste job description")
        st.sidebar.write("3️. Click Match Resumes")

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
        if st.button("🚀 Match Resumes", key="hr_btn"):

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

                    # 🔥 FIX (case-insensitive comparison)
                    candidate_skills_set = set([s.lower() for s in candidate_skills])
                    job_skills_set = set([s.lower() for s in job_skills])

                    if job_skills:
                        matched = candidate_skills_set & job_skills_set
                        skill_match = len(matched) / len(job_skills)
                        skill_percent = round(skill_match * 100, 2)
                        missing = list(job_skills_set - candidate_skills_set)
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
                        0.3 * skill_match +
                        0.2 * experience_score +
                        0.2 * education_score
                    )

                    final_scores.append(final_score)

                #---Dashboard---
                st.subheader("📊 Hiring Insights Dashboard")
                if not final_scores:                              #Important fix
                    st.error("No resumes processed")
                    st.stop()
                col1, col2, col3 = st.columns(3)

                col1.metric("📄 Total Resumes", len(resume_names))
                col2.metric("🏆 Top Match Score", f"{round(max(final_scores)*100,2)}%")
                col3.metric("📈 Average Match", f"{round(sum(final_scores)/len(final_scores)*100,2)}%")

                best_index = final_scores.index(max(final_scores))

                st.success(
                f"🏆 Best Candidate: {resume_names[best_index]} "
                f"with ATS Score {round(final_scores[best_index]*100,2)}%"
                )

                st.markdown("---")

                #---Ranking---
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

                #---Skills---
                st.subheader("🔎 Detected Skills")

                for name, skills in zip(resume_names, resume_skills):
                    st.write(f"👤 {name}: {', '.join(skills) if skills else '⚠️ No major skills found'}")

                st.markdown("---")

                #---Pie Chart---
                st.subheader("📊 Resume Match Distribution")

                labels = resume_names
                values = [float(score) for score in final_scores]

                fig, ax = plt.subplots()
                ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
                ax.axis('equal')
                st.pyplot(fig)

                st.markdown("---")

                #---Download---
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

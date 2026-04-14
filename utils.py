import docx2txt
from pdfminer.high_level import extract_text
import re

# ---------- SKILLS LIST ----------
skills = [

    # Programming Languages
    "python","java","c","c++","c#","javascript","typescript","go","ruby","php","r","matlab",

    # Data Science & ML
    "machine learning","ml","deep learning","dl","data science","data analysis",
    "statistics","predictive modeling","regression","classification","clustering",

    # AI & NLP
    "artificial intelligence","ai","nlp","natural language processing",
    "computer vision","image processing","text mining",

    # Libraries & Frameworks
    "tensorflow","pytorch","keras","scikit-learn","sklearn","pandas","numpy","matplotlib","seaborn",

    # Databases
    "sql","mysql","postgresql","mongodb","oracle","sqlite","nosql",

    # Data Visualization
    "power bi","tableau","excel","data visualization","dashboard",

    # Web Development
    "html","css","javascript","react","angular","vue","nodejs","express",
    "flask","django","spring boot",

    # Cloud & DevOps
    "aws","amazon web services","azure","gcp","google cloud",
    "docker","kubernetes","ci/cd","jenkins","git","github",

    # Big Data
    "hadoop","spark","big data","kafka","hive",

    # Tools
    "linux","unix","shell scripting","jira","postman",

    # Soft Skills
    "communication","teamwork","problem solving","leadership"
]

# ---------- EXTRACT RESUME ----------
def extract_resume(file):

    text = ""

    if file.name.endswith(".pdf"):
        text = extract_text(file)

    elif file.name.endswith(".docx"):
        text = docx2txt.process(file)

    return text


# ---------- CLEAN TEXT ----------
def clean_text(text):

    text = re.sub(r'[^a-zA-Z ]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.lower()

    return text


# ---------- DETECT SKILLS ----------
def detect_skills(text):

    text = text.lower()
    found_skills = []

    for skill in skills:
        if skill.lower() in text:
            found_skills.append(skill)

    return list(set(found_skills))

# ---------- EXPERIENCE ----------
def extract_experience(text):

    matches = re.findall(r'(\d+)\+?\s*years?', text.lower())
    years = [int(m) for m in matches]

    return max(years) if years else 0


# ---------- EDUCATION ----------
def extract_education(text):

    degrees = {
        "phd": 4,
        "mtech": 3,
        "msc": 3,
        "mca": 3,
        "mba": 3,
        "btech": 2,
        "be": 2,
        "bsc": 2,
        "bca": 2,
        "diploma": 1
    }

    highest = 0

    for degree, score in degrees.items():
        if degree in text.lower():
            highest = max(highest, score)

    return highest

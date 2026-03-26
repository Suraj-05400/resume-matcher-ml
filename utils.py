import docx2txt
from pdfminer.high_level import extract_text
import re

#---Show Skills list---
skills = [
    "python","machine learning","deep learning","nlp","sql","power bi",
    "tableau","excel","data science","statistics","tensorflow","pytorch",
    "java","c++","aws","azure","gcp","docker","kubernetes","flask","django"
]

#---extract resume Text---
def extract_resume(file):

    text = ""

    if file.name.endswith(".pdf"):
        text = extract_text(file)

    elif file.name.endswith(".docx"):
        text = docx2txt.process(file)

    return text

#---Text Cleaning---
def clean_text(text):

    text = re.sub(r'[^a-zA-Z ]', '', text)

    text = text.lower()

    return text

#---Detecting Skills---
def detect_skills(text):

    found_skills = []

    for skill in skills:

        if skill in text:
            found_skills.append(skill)

    return found_skills

#---Extract Experience---
def extract_experience(text):

    matches = re.findall(r'(\d+)\+?\s*years?', text.lower())

    years = [int(m) for m in matches]

    return max(years) if years else 0

#---Extract Education---
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

    text = text.lower()

    highest = 0

    for degree, score in degrees.items():

        if degree in text:
            highest = max(highest, score)

    return highest

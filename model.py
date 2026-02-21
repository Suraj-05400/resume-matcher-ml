from sentence_transformers import SentenceTransformer, util
import streamlit as st

# Cache the model so it loads only once
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

def match_resumes(resume_texts, job_description):

    job_embedding = model.encode(job_description, convert_to_tensor=True)

    scores = []

    for resume in resume_texts:
        resume_embedding = model.encode(resume, convert_to_tensor=True)
        similarity = util.cos_sim(resume_embedding, job_embedding)
        scores.append(float(similarity[0][0]))

    return scores
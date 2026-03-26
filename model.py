from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def match_resumes(resumes, job_description):

    documents = [job_description] + resumes

    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform(documents)

    similarity = cosine_similarity(tfidf[1:], tfidf[0])

    scores = [float(score[0]) for score in similarity]

    return scores

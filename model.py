from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.linear_model import LogisticRegression


# ---------- TEXT SIMILARITY ----------
def match_resumes(resumes, job_description):

    documents = [job_description] + resumes

    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform(documents)

    similarity = cosine_similarity(tfidf[1:], tfidf[0])

    scores = [float(score[0]) for score in similarity]

    return scores


# ---------- LOGISTIC REGRESSION ----------
def train_logistic_model(features, labels):

    model = LogisticRegression()
    model.fit(features, labels)

    return model


def predict_logistic(model, features):

    return model.predict(features)

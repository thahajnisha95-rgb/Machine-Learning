"""
recommendation.py
ML logic for the AI-Based Student Self-Learning and Skill Recommendation System.

How it works (content-based recommendation):
1. Every skill in dataset.csv becomes a short text (career goals + interests + name).
2. TF-IDF turns that text into numbers.
3. The student's interests + career goal become text too.
4. Cosine similarity scores how well each skill matches the student.
5. Rules remove skills the student already knows, skills that are too advanced,
   and skills whose prerequisite is missing.
"""

import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

LEVELS = {"beginner": 1, "intermediate": 2, "advanced": 3}
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset.csv")

# ---------- Load data and train the vectorizer once ----------
df = pd.read_csv(DATA_FILE, keep_default_na=False)
df["text"] = df["career_goal"] + " " + df["interests"] + " " + df["next_skill"]

vectorizer = TfidfVectorizer(stop_words="english")
skill_matrix = vectorizer.fit_transform(df["text"])

# All names a skill can be known by (e.g. "Python Basics" -> {"python basics", "python"})
SKILL_NAMES = {}
for _, row in df.iterrows():
    names = {row["next_skill"].lower()}
    for alias in row["aliases"].split("|"):
        if alias.strip():
            names.add(alias.strip().lower())
    SKILL_NAMES[row["next_skill"].lower()] = names


def _clean_list(items):
    """Accept a list or a comma-separated string and return clean lowercase items."""
    if items is None:
        return []
    if isinstance(items, str):
        items = items.split(",")
    return [str(i).strip().lower() for i in items if str(i).strip()]


def _eligible_skills(known, level_num):
    """Return indexes of skills that pass the rules (not known, right level, prerequisite met)."""
    eligible = []
    for i, row in df.iterrows():
        skill_key = row["next_skill"].lower()

        if known & SKILL_NAMES[skill_key]:          # already known
            continue
        if LEVELS[row["level"].lower()] > level_num + 1:   # too advanced
            continue
        prereq = row["prerequisite"]
        if prereq and not (known & SKILL_NAMES[prereq.lower()]):  # prerequisite missing
            continue
        eligible.append(i)
    return eligible


def recommend(current_skills, interests, level, career_goal, top_n=5):
    """
    Recommend what a student should learn next.

    current_skills : list of skills, e.g. ["Python"]
    interests      : list or comma-separated string, e.g. ["AI", "data"]
    level          : "Beginner", "Intermediate" or "Advanced"
    career_goal    : e.g. "AI Engineer"
    top_n          : how many recommendations to return

    Returns a dictionary (easy to turn into JSON for the website).
    """
    known = set(_clean_list(current_skills))
    interest_words = _clean_list(interests)
    goal = str(career_goal or "").strip().lower()
    level_num = LEVELS.get(str(level).strip().lower(), 1)

    eligible = _eligible_skills(known, level_num)

    # Score each skill against the student's interests and goal
    query = " ".join(interest_words) + " " + (goal + " ") * 2
    scores = [0.0] * len(df)
    if query.strip():
        similarity = cosine_similarity(vectorizer.transform([query]), skill_matrix)[0]
        scores = list(similarity)

    matched = [i for i in eligible if scores[i] > 0]
    message = "Recommendations based on your interests and career goal."

    if matched:
        matched.sort(key=lambda i: (-scores[i], LEVELS[df.loc[i, "level"].lower()]))
        chosen = matched[:top_n]
    else:
        # Missing or unfamiliar interests -> safe fallback: easiest eligible skills
        eligible.sort(key=lambda i: LEVELS[df.loc[i, "level"].lower()])
        chosen = eligible[:top_n]
        message = ("We couldn't match your interests or goal, so here are "
                   "beginner-friendly skills to start with.")

    recommendations = []
    for i in chosen:
        row = df.loc[i]
        if row["prerequisite"]:
            reason = f"You are ready for this because you know {row['prerequisite']}."
        else:
            reason = "A good starting point with no prerequisites."
        recommendations.append({
            "skill": row["next_skill"],
            "level": row["level"],
            "score": round(float(scores[i]), 3),
            "reason": reason,
            "resource_name": row["resource_name"],
            "resource_link": row["resource_link"],
        })

    if not recommendations:
        message = "You have covered everything in our current dataset. Great work!"

    return {"status": "ok", "message": message, "recommendations": recommendations}


if __name__ == "__main__":
    demo = recommend(["Python"], ["AI"], "Beginner", "AI Engineer")
    print(demo["message"])
    for rec in demo["recommendations"]:
        print("-", rec["skill"], "|", rec["reason"])

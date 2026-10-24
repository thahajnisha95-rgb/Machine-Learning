"""
student_learning_system.py
--------------------------
Core Skill Recommendation Engine & Learning Resource Matcher.
Features:
- NLP tokenization with domain synonym expansion
- Mathematical TF-IDF Vectorization & Cosine Similarity
- Course alignment & year-of-study difficulty adaptation
- Transparent feature attribution (explainable recommendations)
- Model training, serialization, and persistence
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import json
import math
import os
import re


# Domain synonyms & acronym mappings to normalize student inputs
SYNONYM_MAP = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "ds": "data science",
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "web dev": "web development",
    "frontend": "front-end web development",
    "backend": "back-end web development",
    "db": "database sql",
    "dbms": "database management system sql",
    "cloud": "cloud computing devops",
    "nn": "neural networks deep learning",
    "rl": "reinforcement learning",
    "algo": "algorithms data structures",
    "dsa": "data structures and algorithms",
    "cyber": "cybersecurity information security",
    "sec": "security cybersecurity",
}

STOPWORDS = {
    "a", "about", "above", "after", "again", "all", "am", "an", "and", "any",
    "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "for", "from", "further", "had", "has",
    "have", "having", "he", "her", "here", "hers", "herself", "him", "himself",
    "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "me",
    "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on",
    "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "would", "you", "your", "yours",
    "want", "study", "studying", "like", "interested"
}


def clean_and_tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase keywords and expanded domain synonyms."""
    if not text:
        return []

    cleaned = re.sub(r'[^a-zA-Z0-9+#]', ' ', text.lower())
    raw_tokens = [t.strip() for t in cleaned.split() if t.strip()]

    tokens = []
    for token in raw_tokens:
        expanded = SYNONYM_MAP.get(token, token)
        for sub_token in expanded.split():
            if sub_token not in STOPWORDS and len(sub_token) > 1:
                tokens.append(sub_token)

    return tokens


def extract_ngrams(tokens: List[str], n: int = 2) -> List[str]:
    """Generate n-grams (e.g. bigrams like 'machine learning') from tokens."""
    if len(tokens) < n:
        return []
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def compute_text_similarity(student_tokens: List[str], skill_tokens: List[str]) -> float:
    """
    Compute Jaccard + Overlap similarity between student interest tokens and skill attributes.
    Returns float score between 0.0 and 1.0.
    """
    if not student_tokens or not skill_tokens:
        return 0.0

    set_student = set(student_tokens)
    set_skill = set(skill_tokens)

    intersection = set_student.intersection(set_skill)
    if not intersection:
        partial_hits = 0.0
        for s in set_student:
            for k in set_skill:
                if len(s) > 2 and (s in k or k in s):
                    partial_hits += 0.5
        if partial_hits > 0:
            return min(partial_hits / max(len(set_student), 1), 0.6)
        return 0.0

    overlap_score = len(intersection) / len(set_student)
    union = set_student.union(set_skill)
    jaccard_score = len(intersection) / len(union)

    return round((overlap_score * 0.7) + (jaccard_score * 0.3), 3)


class TFIDFVectorizer:
    """
    Pure-Python mathematical TF-IDF Vectorizer with L2 normalization.
    Calculates TF-IDF weights and cosine similarities without external dependencies.
    """

    def __init__(self):
        self.vocabulary: Dict[str, int] = {}
        self.idf_: Dict[str, float] = {}
        self.doc_count: int = 0

    def fit(self, documents: List[str]):
        """Build vocabulary and compute IDF for each term across all documents."""
        self.doc_count = len(documents)
        if self.doc_count == 0:
            return

        doc_term_sets = []
        all_terms = set()

        for doc in documents:
            tokens = clean_and_tokenize(doc)
            bigrams = extract_ngrams(tokens, 2)
            terms = set(tokens + bigrams)
            doc_term_sets.append(terms)
            all_terms.update(terms)

        self.vocabulary = {term: idx for idx, term in enumerate(sorted(all_terms))}

        # Standard smoothed IDF formula: ln((1 + N) / (1 + DF)) + 1.0
        self.idf_ = {}
        for term in self.vocabulary:
            df = sum(1 for d in doc_term_sets if term in d)
            self.idf_[term] = math.log((1.0 + self.doc_count) / (1.0 + df)) + 1.0

    def transform(self, text: str) -> Dict[str, float]:
        """Convert a document into an L2-normalized sparse TF-IDF vector."""
        if not self.vocabulary:
            return {}

        tokens = clean_and_tokenize(text)
        bigrams = extract_ngrams(tokens, 2)
        terms = tokens + bigrams

        if not terms:
            return {}

        # Term Frequency
        term_counts: Dict[str, int] = {}
        for t in terms:
            if t in self.vocabulary:
                term_counts[t] = term_counts.get(t, 0) + 1

        total_terms = len(terms)
        tfidf_vec: Dict[str, float] = {}

        for term, count in term_counts.items():
            tf = count / total_terms
            idf = self.idf_.get(term, 1.0)
            tfidf_vec[term] = tf * idf

        # L2 Normalization: v / sqrt(sum(v_i^2))
        norm = math.sqrt(sum(val ** 2 for val in tfidf_vec.values()))
        if norm > 0:
            tfidf_vec = {t: val / norm for t, val in tfidf_vec.items()}

        return tfidf_vec

    @staticmethod
    def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """Compute cosine similarity (dot product of L2-normalized vectors)."""
        if not vec_a or not vec_b:
            return 0.0

        dot_product = sum(vec_a[t] * vec_b[t] for t in vec_a if t in vec_b)
        return max(0.0, min(round(dot_product, 4), 1.0))

    @staticmethod
    def get_top_contributing_terms(
        vec_a: Dict[str, float], vec_b: Dict[str, float], top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """Return the terms contributing most to the cosine similarity score."""
        contributions = [
            (t, round(vec_a[t] * vec_b[t], 4))
            for t in vec_a if t in vec_b
        ]
        contributions.sort(key=lambda x: x[1], reverse=True)
        return contributions[:top_k]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize vectorizer state."""
        return {
            "vocabulary": self.vocabulary,
            "idf": self.idf_,
            "doc_count": self.doc_count,
        }

    def from_dict(self, data: Dict[str, Any]):
        """Load vectorizer state."""
        self.vocabulary = data.get("vocabulary", {})
        self.idf_ = data.get("idf", {})
        self.doc_count = data.get("doc_count", 0)


@dataclass
class RecommendationResult:
    skill_id: int
    skill_name: str
    category: str
    description: str
    match_score: float  # 0.0 - 1.0
    match_percentage: int  # 0 - 100
    match_reasons: List[str] = field(default_factory=list)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    top_contributing_terms: List[str] = field(default_factory=list)


class MLSkillRecommender:
    """
    Production-ready Machine Learning Recommender Engine.
    Combines:
    1. TF-IDF Cosine Similarity for interest & skill matching
    2. Academic curriculum alignment weighting
    3. Academic year-of-study difficulty adaptation
    """

    def __init__(self, model_path: Optional[str] = None):
        self.vectorizer = TFIDFVectorizer()
        self.skill_vectors: Dict[int, Dict[str, float]] = {}
        self.model_path = model_path or os.path.join(
            os.path.dirname(__file__), "recommender_model.json"
        )
        self.is_trained = False

        if os.path.exists(self.model_path):
            self.load_model(self.model_path)

    def train_from_database(self):
        """Train TF-IDF vector space model on all skills and resources currently in the database."""
        from accounts.models import Skill

        skills = list(Skill.objects.all().prefetch_related('resources'))
        if not skills:
            return

        documents = []
        skill_ids = []

        for skill in skills:
            resource_titles = " ".join(r.title for r in skill.resources.all())
            doc_text = f"{skill.name} {skill.category} {skill.keywords} {skill.description} {resource_titles}"
            documents.append(doc_text)
            skill_ids.append(skill.id)

        self.vectorizer.fit(documents)

        # Build skill vectors
        self.skill_vectors = {}
        for skill_id, doc_text in zip(skill_ids, documents):
            self.skill_vectors[skill_id] = self.vectorizer.transform(doc_text)

        self.is_trained = True
        self.save_model(self.model_path)

    def save_model(self, filepath: str):
        """Persist model state and vectors to JSON."""
        data = {
            "vectorizer": self.vectorizer.to_dict(),
            "skill_vectors": {str(k): v for k, v in self.skill_vectors.items()},
            "is_trained": self.is_trained,
        }
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def load_model(self, filepath: str):
        """Load model state and vectors from JSON."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.vectorizer.from_dict(data.get("vectorizer", {}))
            self.skill_vectors = {
                int(k): v for k, v in data.get("skill_vectors", {}).items()
            }
            self.is_trained = data.get("is_trained", False)
        except Exception:
            self.is_trained = False

    def get_preferred_difficulties(self, year_of_study: Optional[int]) -> List[str]:
        year = year_of_study or 1
        if year <= 1:
            return ['beginner', 'intermediate']
        elif year == 2:
            return ['beginner', 'intermediate', 'advanced']
        else:
            return ['intermediate', 'advanced', 'beginner']

    def recommend(self, student_profile: Any, top_n: int = 5) -> List[RecommendationResult]:
        from accounts.models import Skill

        if not student_profile:
            return []

        if not self.is_trained or not self.skill_vectors:
            self.train_from_database()

        interests_text = getattr(student_profile, 'interests', '') or ''
        course_text = getattr(student_profile, 'course', '') or ''
        year_of_study = getattr(student_profile, 'year_of_study', 1) or 1

        interest_tokens = clean_and_tokenize(interests_text)
        course_tokens = clean_and_tokenize(course_text)

        # Student interest query vector
        query_text = f"{interests_text} {' '.join(interest_tokens)}"
        student_vector = self.vectorizer.transform(query_text)

        skills = Skill.objects.all().prefetch_related('resources')
        preferred_difficulties = self.get_preferred_difficulties(year_of_study)

        scored_skills: List[RecommendationResult] = []

        for skill in skills:
            skill_vec = self.skill_vectors.get(skill.id)
            if not skill_vec:
                doc_text = f"{skill.name} {skill.category} {skill.keywords} {skill.description}"
                skill_vec = self.vectorizer.transform(doc_text)
                self.skill_vectors[skill.id] = skill_vec

            # 1. Cosine similarity via TF-IDF vectors
            cosine_score = self.vectorizer.cosine_similarity(student_vector, skill_vec)

            # 2. Direct lexical fallback / booster
            direct_sim = compute_text_similarity(
                interest_tokens,
                clean_and_tokenize(f"{skill.name} {skill.keywords}")
            )

            # 3. Course curriculum alignment
            course_sim = compute_text_similarity(
                course_tokens,
                clean_and_tokenize(f"{skill.name} {skill.category} {skill.description}")
            )

            # Feature Attribution
            top_terms = self.vectorizer.get_top_contributing_terms(student_vector, skill_vec, top_k=3)
            contributing_term_names = [t[0] for t in top_terms]

            match_reasons = []

            # Hybrid score blending ML vector similarity (60%) and token matching (40%)
            hybrid_score = (cosine_score * 0.60) + (direct_sim * 0.40)

            if contributing_term_names:
                match_reasons.append(f"Matches keywords: '{', '.join(contributing_term_names)}'")
            elif direct_sim > 0:
                match_reasons.append(f"Direct match with {skill.name}")

            if course_sim > 0:
                course_bonus = course_sim * 0.25
                hybrid_score += course_bonus
                match_reasons.append(f"Aligned with {course_text or 'degree'} curriculum")

            final_score = min(round(hybrid_score, 3), 1.0)

            # Sort resources by academic difficulty
            active_resources = [r for r in skill.resources.all() if r.is_active]

            def difficulty_rank(res):
                try:
                    return preferred_difficulties.index(res.difficulty)
                except ValueError:
                    return 99

            sorted_resources = sorted(active_resources, key=difficulty_rank)

            resource_dicts = [
                {
                    "id": r.id,
                    "title": r.title,
                    "description": r.description,
                    "resource_type": r.get_resource_type_display(),
                    "url": r.url,
                    "platform": r.platform or "Online",
                    "difficulty": r.get_difficulty_display(),
                }
                for r in sorted_resources
            ]

            if final_score > 0.05 or not interest_tokens:
                if not match_reasons:
                    match_reasons.append("Recommended foundational skill for your studies")

                scored_skills.append(
                    RecommendationResult(
                        skill_id=skill.id,
                        skill_name=skill.name,
                        category=skill.category,
                        description=skill.description,
                        match_score=final_score,
                        match_percentage=int(round(final_score * 100)),
                        match_reasons=match_reasons,
                        resources=resource_dicts,
                        top_contributing_terms=contributing_term_names,
                    )
                )

        scored_skills.sort(key=lambda x: (x.match_score, len(x.resources)), reverse=True)
        return scored_skills[:top_n]


# Global recommender engine instance
recommender_engine = MLSkillRecommender()


def train_recommender_system() -> Dict[str, Any]:
    """Train/update the recommendation model weights from the database."""
    recommender_engine.train_from_database()
    return {
        "status": "success",
        "doc_count": recommender_engine.vectorizer.doc_count,
        "vocabulary_size": len(recommender_engine.vectorizer.vocabulary),
        "skills_indexed": len(recommender_engine.skill_vectors),
    }


def get_recommendations_for_student(student_profile: Any, top_n: int = 5) -> Dict[str, Any]:
    """
    High-level API for views and controllers.
    Returns recommended skills, matched resources, and model meta information.
    """
    recommendations = recommender_engine.recommend(student_profile, top_n=top_n)

    all_matched_resources = []
    seen_urls = set()
    for rec in recommendations:
        for res in rec.resources:
            if res["url"] not in seen_urls:
                seen_urls.add(res["url"])
                res_copy = dict(res)
                res_copy["skill_name"] = rec.skill_name
                all_matched_resources.append(res_copy)

    return {
        "recommended_skills": recommendations,
        "recommended_resources": all_matched_resources[:12],
        "total_recommendations": len(recommendations),
        "engine_version": "ML TF-IDF & Cosine Similarity Engine v2.0",
        "vocabulary_size": len(recommender_engine.vectorizer.vocabulary),
    }

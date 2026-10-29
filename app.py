"""
app.py
Streamlit Web Application for AI-Based Student Self-Learning and Skill Recommendation System.
"""

import streamlit as st
import pandas as pd
from recommendation import recommend, df

# Set page configuration
st.set_page_config(
    page_title="AI Student Skill Recommender",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .rec-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        border-left: 5px solid #3B82F6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .level-badge-beginner {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .level-badge-intermediate {
        background-color: #FEF08A;
        color: #713F12;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .level-badge-advanced {
        background-color: #FCE7F3;
        color: #831843;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.markdown('<div class="main-header">🎓 AI-Based Student Skill Recommendation System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Content-Based ML Recommendation Engine using TF-IDF Vectorization, Cosine Similarity & Prerequisite Validation</div>', unsafe_allow_html=True)

# Extract available options from dataset
available_skills = sorted(list(df["next_skill"].unique()))
unique_goals = sorted(list(set(
    goal.strip()
    for goals in df["career_goal"]
    for goal in goals.split()
    if goal.strip()
)))
# Pre-defined popular career goals
popular_goals = [
    "AI Engineer",
    "Data Scientist",
    "Data Analyst",
    "Backend Developer",
    "Frontend Developer",
    "Web Developer"
]

tab_rec, tab_catalog, tab_test = st.tabs(["🚀 Get Recommendations", "📚 Skill Catalog & Prerequisites", "🧪 Quick Test Profiles"])

with tab_rec:
    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        st.subheader("📋 Student Profile")
        
        # 1. Career Goal
        goal_option = st.selectbox(
            "Target Career Goal",
            popular_goals + ["Custom / Other..."],
            index=0
        )
        if goal_option == "Custom / Other...":
            career_goal = st.text_input("Enter your career goal", placeholder="e.g. Machine Learning Specialist")
        else:
            career_goal = goal_option

        # 2. Level
        level = st.selectbox(
            "Current Experience Level",
            ["Beginner", "Intermediate", "Advanced"],
            index=0
        )

        # 3. Known Skills
        selected_skills = st.multiselect(
            "Skills You Already Know",
            options=available_skills,
            default=["Python Basics"] if "Python Basics" in available_skills else []
        )
        extra_skills = st.text_input(
            "Other known skills (comma separated)",
            placeholder="e.g. Git, C++"
        )
        current_skills = selected_skills.copy()
        if extra_skills.strip():
            current_skills.extend([s.strip() for s in extra_skills.split(",") if s.strip()])

        # 4. Interests
        interest_input = st.text_input(
            "Interests / Focus Areas (comma or space separated)",
            value="AI, machine learning",
            placeholder="e.g. AI, deep learning, web, database"
        )

        # 5. Top N
        top_n = st.slider("Max recommendations to show", min_value=1, max_value=10, value=5)

        get_rec_button = st.button("🔍 Get Recommendations", type="primary", use_container_width=True)

    with col2:
        st.subheader("💡 Recommended Learning Path")

        if get_rec_button or True:
            # Process interests into a clean list
            interests_list = [i.strip() for i in interest_input.replace(",", " ").split() if i.strip()]
            
            result = recommend(
                current_skills=current_skills,
                interests=interests_list,
                level=level,
                career_goal=career_goal,
                top_n=top_n
            )

            st.info(f"📌 **Status:** {result['message']}")

            recommendations = result.get("recommendations", [])
            if recommendations:
                for idx, rec in enumerate(recommendations, 1):
                    lvl = rec['level'].lower()
                    badge_class = f"level-badge-{lvl}"

                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.markdown(f"### {idx}. {rec['skill']}")
                        st.markdown(f"**Level:** <span class='{badge_class}'>{rec['level']}</span> &nbsp;&nbsp;|&nbsp;&nbsp; **Match Score:** `{rec['score']}`", unsafe_allow_html=True)
                        st.write(f"ℹ️ **Why learn this:** {rec['reason']}")
                        st.markdown(f"📖 **Recommended Resource:** [{rec['resource_name']}]({rec['resource_link']})")
                    with col_b:
                        progress_val = min(max(rec['score'], 0.05), 1.0)
                        st.metric(label="Match", value=f"{int(rec['score']*100)}%")
                        st.progress(progress_val)
                    st.divider()
            else:
                st.warning("No new recommendations available for this profile. Try adjusting your current skills or interests!")

with tab_catalog:
    st.subheader("📖 Full Skill Database")
    st.write(f"Total skills available in dataset: **{len(df)}**")
    
    # Filter by level
    selected_level_filter = st.multiselect(
        "Filter by Level",
        options=["Beginner", "Intermediate", "Advanced"],
        default=["Beginner", "Intermediate", "Advanced"]
    )
    
    filtered_df = df[df["level"].isin(selected_level_filter)] if selected_level_filter else df
    
    display_df = filtered_df[["next_skill", "level", "prerequisite", "career_goal", "resource_name", "resource_link"]].copy()
    display_df.columns = ["Skill", "Level", "Prerequisite", "Relevant Careers", "Resource Name", "Resource URL"]
    st.dataframe(display_df, use_container_width=True)

with tab_test:
    st.subheader("🧪 Evaluate Standard Student Profiles")
    st.write("Click any sample profile to see how the recommendation engine responds:")

    sample_profiles = {
        "AI Beginner": (["Python Basics"], ["AI", "deep learning"], "Beginner", "AI Engineer"),
        "Data Analyst Aspirant": (["SQL Basics"], ["data analysis", "dashboards"], "Beginner", "Data Analyst"),
        "Intermediate Programmer -> ML": (["Python Basics", "NumPy and Pandas", "SQL Basics"], ["machine learning"], "Intermediate", "Data Scientist"),
        "Web Developer Path": (["HTML and CSS"], ["interactive", "frontend"], "Beginner", "Frontend Developer"),
        "Unfamiliar Interests (Fallback Test)": ([], ["cooking", "music"], "Beginner", "")
    }

    selected_sample = st.selectbox("Select a test profile", list(sample_profiles.keys()))
    if st.button("Run Profile Test"):
        s_skills, s_interests, s_level, s_goal = sample_profiles[selected_sample]
        st.write(f"**Known Skills:** {s_skills}")
        st.write(f"**Interests:** {s_interests}")
        st.write(f"**Level:** {s_level}")
        st.write(f"**Goal:** {s_goal or '(None)'}")
        
        sample_result = recommend(s_skills, s_interests, s_level, s_goal, top_n=5)
        st.success(sample_result["message"])
        for r in sample_result["recommendations"]:
            st.write(f"- **{r['skill']}** ({r['level']}) — Match Score: `{r['score']}` | Reason: _{r['reason']}_ | [{r['resource_name']}]({r['resource_link']})")


"""evaluate_model.py - tests the recommender with different student profiles."""
from recommendation import recommend, df

def show(title, result):
    print("\n==", title, "==")
    print(result["message"])
    for r in result["recommendations"]:
        print(f"  - {r['skill']} ({r['level']}, score {r['score']})")

profiles = {
    "1. Beginner interested in AI": (["Python"], ["AI"], "Beginner", "AI Engineer"),
    "2. Student interested in data analysis": (["SQL"], ["data analysis"], "Beginner", "Data Analyst"),
    "3. Intermediate programmer aiming for ML": (["Python", "NumPy", "Pandas"], ["machine learning"], "Intermediate", "Data Scientist"),
    "4. Unfamiliar interest (edge case)": ([], ["cooking"], "Beginner", ""),
    "5. Missing everything (edge case)": ([], [], "Beginner", ""),
}

passed = True
for title, args in profiles.items():
    result = recommend(*args)
    show(title, result)

    known = {s.lower() for s in args[0]}
    for rec in result["recommendations"]:
        row = df[df["next_skill"] == rec["skill"]].iloc[0]
        if rec["skill"].lower() in known:
            print("  FAIL: recommended a skill the student already knows:", rec["skill"])
            passed = False
        # prerequisite check: prerequisite must be known (by name or alias)
        prereq = row["prerequisite"]
        if prereq:
            prereq_row = df[df["next_skill"] == prereq].iloc[0]
            names = {prereq.lower()} | {a for a in prereq_row["aliases"].split("|") if a}
            if not (known & names):
                print("  FAIL: prerequisite missing for", rec["skill"])
                passed = False

print("\nAll checks passed!" if passed else "\nSome checks failed.")

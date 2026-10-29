"""prepare_data.py - checks that dataset.csv is clean before using it."""
import pandas as pd

df = pd.read_csv("dataset.csv", keep_default_na=False)
names = set(df["next_skill"])
problems = 0

for _, row in df.iterrows():
    for col in ["next_skill", "level", "career_goal", "interests", "resource_link"]:
        if not row[col]:
            print("Empty", col, "in row:", row["next_skill"])
            problems += 1
    if row["level"] not in ("Beginner", "Intermediate", "Advanced"):
        print("Bad level for:", row["next_skill"])
        problems += 1
    if row["prerequisite"] and row["prerequisite"] not in names:
        print("Unknown prerequisite for:", row["next_skill"])
        problems += 1

print("Rows:", len(df))
print("Dataset OK!" if problems == 0 else f"Found {problems} problem(s).")

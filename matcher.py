def analyze_skill_gap(required_skills, user_skills):
    required = [s.strip().lower() for s in required_skills.split(",") if s.strip()]
    mine = {s.strip().lower() for s in user_skills.split(",") if s.strip()}

    matched = [s for s in required if s in mine]
    missing = [s for s in required if s not in mine]
    match_score = round(len(matched) / len(required) * 100) if required else 0

    roadmap = [f"Learn {s}" for s in missing]
    return {"match_score": match_score, "matched": matched,
            "missing": missing, "roadmap": roadmap}

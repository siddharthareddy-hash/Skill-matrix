from app import app
from models import db, Company, Role

DATA = {
    "Google": [
        {"title": "Backend Engineer",
         "skills": ["Python", "Go", "SQL", "Docker"],
         "subjects": ["DBMS", "OS", "CN", "DSA"]},
        {"title": "Frontend Developer",
         "skills": ["JavaScript", "React", "CSS"],
         "subjects": ["OS", "DSA"]},
    ],
    "Zoho": [
        {"title": "Data Analyst",
         "skills": ["Python", "SQL", "Excel", "Tableau"],
         "subjects": ["DBMS", "Statistics"]},
    ],
}

with app.app_context():
    db.create_all()
    for name, roles in DATA.items():
        c = Company(name=name)
        for r in roles:
            c.roles.append(Role(
                title=r["title"],
                skills=", ".join(r["skills"]),
                subjects=", ".join(r["subjects"]),
            ))
        db.session.add(c)
    db.session.commit()
    print("✅ Seeded successfully!")

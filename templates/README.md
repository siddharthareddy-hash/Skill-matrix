# ⚡ SkillMatrix

A Flask web app that compares your skills against real job roles
and shows your match score, skill gaps, and a learning roadmap.

## Features
- 🔐 User registration & login (Flask-Login)
- 🏢 Browse/search companies and their roles
- 🎯 Skill gap analyzer with match score (0–100%)
- 📋 Personal profile with saved skills
- 🗂️ Analysis history (view & delete)
- 📊 Dashboard with Chart.js charts
- 🛠️ Full REST API (CRUD for companies, roles, analyses)

## Tech Stack
- Python / Flask / SQLAlchemy
- SQLite database
- Jinja2 templates + vanilla JS
- Chart.js

## Run It

```bash
pip install flask flask_sqlalchemy flask_login
python app.py

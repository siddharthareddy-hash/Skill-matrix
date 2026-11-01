import os, re
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Company, Role, Analysis, Resume
from resume_parser import extract_text
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///skillmatrix.db"
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

ALLOWED_EXT = {"pdf", "docx", "txt"}

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ---------- helpers ----------
def get_own_role(role_id):
    role = db.session.get(Role, role_id)
    if not role or role.company.user_id != current_user.id:
        abort(404)
    return role

def match_skills(required_list, text):
    words = set(re.findall(r"[a-zA-Z+#.]+", text.lower()))
    matched = [s for s in required_list if s.lower() in words]
    missing = [s for s in required_list if s.lower() not in words]
    score = int(len(matched) / len(required_list) * 100) if required_list else 0
    return matched, missing, score

# ---------- auth ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        if db.session.query(User).filter_by(username=username).first():
            flash("Username taken.")
            return redirect(url_for("register"))
        u = User(username=username)
        u.set_password(request.form["password"])
        db.session.add(u)
        db.session.commit()
        flash("Registered! Please log in.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = db.session.query(User).filter_by(username=request.form["username"]).first()
        if u and u.check_password(request.form["password"]):
            login_user(u)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials.")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------- dashboard ----------
@app.route("/")
@login_required
def dashboard():
    companies = Company.query.filter_by(user_id=current_user.id).all()
    recent = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).limit(5).all()
    return render_template("dashboard.html", companies=companies, recent=recent)

@app.route("/company/add", methods=["POST"])
@login_required
def add_company():
    name = request.form["name"].strip()
    if name:
        db.session.add(Company(name=name, user_id=current_user.id))
        db.session.commit()
        flash("Company added ✅")
    return redirect(url_for("dashboard"))

@app.route("/company/<int:company_id>")
@login_required
def company(company_id):
    c = db.session.get(Company, company_id)
    if not c or c.user_id != current_user.id:
        abort(404)
    return render_template("company.html", company=c)

@app.route("/company/<int:company_id>/role/add", methods=["POST"])
@login_required
def add_role(company_id):
    c = db.session.get(Company, company_id)
    if not c or c.user_id != current_user.id:
        abort(404)
    title = request.form["title"].strip()
    skills = request.form["skills"].strip()
    if title and skills:
        db.session.add(Role(title=title, skills=skills, company_id=company_id))
        db.session.commit()
        flash("Role added ✅")
    return redirect(url_for("company", company_id=company_id))

@app.route("/role/<int:role_id>/delete", methods=["POST"])
@login_required
def delete_role(role_id):
    role = get_own_role(role_id)
    cid = role.company_id
    db.session.delete(role)
    db.session.commit()
    flash("Role deleted.")
    return redirect(url_for("company", company_id=cid))

# ---------- analyzer ----------
@app.route("/analyzer")
@login_required
def analyzer():
    companies = Company.query.filter_by(user_id=current_user.id).order_by(Company.name).all()
    preselect = request.args.get("role_id", type=int)
    pre_company = None
    if preselect:
        r = db.session.get(Role, preselect)
        pre_company = r.company_id if r else None
    return render_template("analyzer.html", companies=companies,
                           pre_company=pre_company, pre_role=preselect)

@app.route("/api/company/<int:company_id>/roles")
@login_required
def api_roles(company_id):
    c = db.session.get(Company, company_id)
    if not c or c.user_id != current_user.id:
        return jsonify([]), 404
    return jsonify([{"id": r.id, "title": r.title} for r in c.roles])

@app.route("/api/analyze", methods=["POST"])
@login_required
def api_analyze():
    data = request.get_json()
    role = get_own_role(data.get("role_id", 0))
    user_skills = [s.strip() for s in (data.get("skills") or "").split(",") if s.strip()]
    required = [s.strip() for s in role.skills.split(",") if s.strip()]
    user_lower = {s.lower() for s in user_skills}
    matched = [s for s in required if s.lower() in user_lower]
    missing = [s for s in required if s.lower() not in user_lower]
    score = int(len(matched) / len(required) * 100) if required else 0
    a = Analysis(role_id=role.id, user_id=current_user.id, match_score=score,
                 matched=", ".join(matched), missing=", ".join(missing))
    db.session.add(a)
    db.session.commit()
    return jsonify({"role": role.title, "match_score": score,
                    "matched": matched, "missing": missing})

@app.route("/history")
@login_required
def history():
    items = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).all()
    return render_template("history.html", items=items)

# ---------- resume ----------
@app.route("/upload/<int:role_id>", methods=["GET", "POST"])
@login_required
def upload_resume(role_id):
    role = get_own_role(role_id)
    if request.method == "POST":
        file = request.files.get("resume")
        if not file or file.filename == "" or \
           file.filename.rsplit(".", 1)[-1].lower() not in ALLOWED_EXT:
            flash("Please upload a PDF, DOCX, or TXT file.")
            return redirect(request.url)
        text = extract_text(file)
        if not text or not text.strip():
            flash("Could not extract text from that file.")
            return redirect(request.url)
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        required = [s.strip() for s in role.skills.split(",") if s.strip()]
        _, _, score = match_skills(required, text)
        resume = Resume(filename=filename, text=text, role_id=role.id,
                        user_id=current_user.id, match_score=score)
        db.session.add(resume)
        db.session.commit()
        flash(f"Resume analyzed! Match score: {score}%")
        return redirect(url_for("resume_result", resume_id=resume.id))
    return render_template("upload.html", role=role)

@app.route("/resume/<int:resume_id>")
@login_required
def resume_result(resume_id):
    r = db.session.get(Resume, resume_id)
    if not r or r.user_id != current_user.id:
        abort(404)
    required = [s.strip() for s in r.role.skills.split(",") if s.strip()]
    matched, missing, _ = match_skills(required, r.text)
    return render_template("resume_result.html", resume=r, matched=matched, missing=missing)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

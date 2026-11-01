// ===== Skill Gap Analyzer =====

// Hide result card until we have data
document.addEventListener("DOMContentLoaded", () => {
    const resultCard = document.getElementById("result-card");
    if (resultCard) resultCard.style.display = "none";
});

async function loadRoles() {
    const companyId = document.getElementById("company").value;
    const roleSelect = document.getElementById("role");
    roleSelect.innerHTML = '<option value="">--</option>';
    roleSelect.disabled = !companyId;
    if (!companyId) return;

    const res = await fetch(`/api/company/${companyId}`);
    const company = await res.json();
    company.roles.forEach(r => {
        const opt = document.createElement("option");
        opt.value = r.id;
        opt.textContent = r.title;
        roleSelect.appendChild(opt);
    });
}

async function analyze() {
    const companyId = document.getElementById("company").value;
    const roleId = document.getElementById("role").value;
    const skills = document.getElementById("skills").value.trim();

    if (!companyId || !roleId) return alert("Select a company and role first!");
    if (!skills) return alert("Enter at least one skill!");

    const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            company_id: parseInt(companyId),
            role_id: parseInt(roleId),
            skills: skills
        })
    });
    const data = await res.json();

    if (data.error) return alert(data.error);

    // Show the result card
    document.getElementById("result-card").style.display = "block";

    const score = data.match_score;
    document.getElementById("result-title").innerText =
        data.role + " at " + data.company;
    document.getElementById("result-score").innerText = score + "% match";

    const bar = document.getElementById("result-bar");
    bar.style.width = score + "%";
    bar.style.background = score >= 80 ? "var(--green)"
                         : score >= 50 ? "var(--orange)" : "var(--red)";

    document.getElementById("result-matched").innerHTML =
        data.matched.map(s => `<span class="badge ok">${s}</span>`).join(" ") || "—";
    document.getElementById("result-missing").innerHTML =
        data.missing.map(s => `<span class="badge gap">${s}</span>`).join(" ") || "None! 🎉";
    document.getElementById("result-roadmap").innerHTML =
        data.roadmap.map(r => `<li>${r}</li>`).join("");
}

import json
import os
from datetime import datetime


def score_color(score):
    if score >= 80:
        return "#1D5C2E"
    if score >= 60:
        return "#C5A028"
    if score >= 40:
        return "#1A3C5E"
    return "#8B1A1A"


def score_label(score):
    if score >= 80:
        return "Top Match"
    if score >= 60:
        return "Bon Match"
    if score >= 40:
        return "A evaluer"
    return "Faible"


def contract_badge(contract):
    c = contract.lower()
    if any(x in c for x in ["mission", "freelance", "interim"]):
        return "Freelance", "#2C2C6E"
    if "cdi" in c:
        return "CDI", "#1D5C2E"
    if "cdd" in c:
        return "CDD", "#C5A028"
    return contract, "#1A3C5E"


def generate_card(job, idx):
    score = job.get("score", 0)
    color = score_color(score)
    label = score_label(score)
    contract_text, contract_color = contract_badge(job.get("contract", ""))
    cv = job.get("cv_recommended", "CDI")
    cv_color = "#2C2C6E" if cv == "Freelance" else "#1A3C5E"
    job_id = job.get("id", str(idx))
    title = job.get("title", "")
    company = job.get("company", "Non precise")
    location = job.get("location", "")
    salary = job.get("salary", "Non precise")
    date = job.get("date", "")[:10]
    source = job.get("source", "")
    summary = job.get("ai_summary", "")
    title_rw = job.get("title_rewrite", "")
    url = job.get("url", "#")

    card = '<div class="card" style="border-left-color:' + color + '">'
    card += '<div class="score-badge" style="background:' + color + '">'
    card += label + " " + str(score) + "/100</div>"
    card += '<div class="card-header">'
    card += '<div class="card-icon">briefcase</div>'
    card += "<div>"
    card += '<div class="card-title">' + title + "</div>"
    card += '<div class="card-company">' + company + " · " + location + "</div>"
    card += "</div></div>"
    card += '<div class="card-meta">'
    card += '<span class="tag" style="background:' + contract_color + ';color:white">' + contract_text + "</span>"
    card += '<span class="tag">' + salary + "</span>"
    card += '<span class="tag">' + date + "</span>"
    card += '<span class="tag">' + source + "</span>"
    card += "</div>"
    card += '<div class="card-body">' + summary + "</div>"
    card += '<div class="card-cv" style="border-left:3px solid ' + cv_color + '">'
    card += "CV recommande : " + cv + " · " + title_rw + "</div>"
    card += '<div class="card-actions">'
    card += '<a class="btn btn-primary" href="' + url + '" target="_blank">Voir offre</a>'
    card += '<select class="status-select" onchange="updateStatus(\'' + job_id + '\', this.value)">'
    card += '<option value="new">Nouvelle</option>'
    card += '<option value="active">A postuler</option>'
    card += '<option value="applied">Envoyee</option>'
    card += '<option value="network">Reseau</option>'
    card += '<option value="rejected">Refusee</option>'
    card += "</select>"
    card += '<button class="btn btn-outline" onclick="toggleNote(\'' + job_id + '\')">Note</button>'
    card += "</div>"
    card += '<textarea class="notes-area" id="notes' + job_id + '" '
    card += 'onchange="saveNote(\'' + job_id + '\', this.value)" '
    card += 'placeholder="Vos notes..."></textarea>'
    card += "</div>"
    return card


def generate_linkedin_links():
    searches = [
        ("Head of ITSM Paris", "head+of+ITSM+paris"),
        ("ServiceNow Consultant Senior", "servicenow+consultant+senior+paris"),
        ("IT Governance Manager", "IT+governance+manager+paris"),
        ("DSI Transformation Freelance", "DSI+transformation+freelance+paris"),
        ("ITIL Expert Paris", "ITIL+expert+paris"),
    ]
    html = ""
    for label, query in searches:
        url = "https://www.linkedin.com/jobs/search/?keywords=" + query + "&location=Paris&f_TPR=r86400"
        html += '<a class="linkedin-link" href="' + url + '" target="_blank">' + label + "</a>"
    return html


def main():
    with open("data/jobs.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    jobs = data["jobs"]
    updated = data.get("updated_at", "")[:16].replace("T", " a ")
    total = len(jobs)
    top_count = len([j for j in jobs if j["score"] >= 70])
    medium_count = len([j for j in jobs if 40 <= j["score"] < 70])
    today = datetime.now().strftime("%d/%m/%Y")

    cards_top = ""
    cards_medium = ""
    cards_low = ""

    for i, job in enumerate(jobs):
        card = generate_card(job, i)
        if job["score"] >= 70:
            cards_top += card
        elif job["score"] >= 40:
            cards_medium += card
        else:
            cards_low += card

    if not cards_top:
        cards_top = '<div class="empty">Aucune offre top match aujourd\'hui</div>'
    if not cards_medium:
        cards_medium = '<div class="empty">Aucune offre dans cette categorie</div>'
    if not cards_low:
        cards_low = '<div class="empty">Aucune offre dans cette categorie</div>'

    linkedin_links = generate_linkedin_links()

    css = """
  :root { --navy: #1A3C5E; --gold: #C5A028; --green: #1D5C2E; --bordeaux: #8B1A1A; --indigo: #2C2C6E; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: #f0f4f8; color: #1a1a2e; }
  .header { background: linear-gradient(135deg, #1A3C5E 0%, #0d2438 100%); color: white; padding: 2rem 2.5rem 1.5rem; border-bottom: 4px solid #C5A028; }
  .header h1 { font-size: 2rem; font-weight: 800; }
  .header h1 span { color: #C5A028; }
  .header-sub { font-size: 0.9rem; opacity: 0.8; margin-top: 0.3rem; }
  .header-top { display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem; }
  .date-badge { background: rgba(197,160,40,0.2); border: 1px solid #C5A028; border-radius: 6px; padding: 0.4rem 0.9rem; font-size: 0.8rem; color: #C5A028; }
  .stats { display: flex; gap: 1.5rem; padding: 1rem 2.5rem; background: white; border-bottom: 1px solid #dde; flex-wrap: wrap; }
  .stat { font-size: 0.85rem; }
  .stat strong { font-size: 1.1rem; }
  main { max-width: 1300px; margin: 0 auto; padding: 1.5rem; }
  .section-label { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: #888; margin: 1.8rem 0 0.8rem; border-left: 3px solid #C5A028; padding-left: 0.6rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 1.2rem; }
  .card { background: white; border-radius: 12px; padding: 1.4rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-left: 5px solid #1A3C5E; position: relative; transition: transform 0.15s; }
  .card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
  .score-badge { position: absolute; top: 1rem; right: 1rem; padding: 0.25rem 0.7rem; border-radius: 20px; font-size: 0.7rem; font-weight: 700; color: white; }
  .card-header { display: flex; gap: 0.8rem; margin-bottom: 0.8rem; padding-right: 8rem; }
  .card-icon { font-size: 1.5rem; }
  .card-title { font-size: 1rem; font-weight: 700; line-height: 1.3; }
  .card-company { font-size: 0.85rem; color: #555; margin-top: 0.2rem; }
  .card-meta { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.8rem 0; }
  .tag { background: #F5F7FA; border-radius: 4px; padding: 0.2rem 0.5rem; font-size: 0.72rem; color: #444; }
  .card-body { font-size: 0.83rem; color: #555; line-height: 1.5; margin-bottom: 0.9rem; border-top: 1px solid #eee; padding-top: 0.7rem; }
  .card-cv { font-size: 0.78rem; background: #f0f4f8; border-radius: 6px; padding: 0.4rem 0.7rem; margin-bottom: 0.8rem; color: #1A3C5E; font-weight: 600; }
  .card-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
  .btn { display: inline-flex; align-items: center; padding: 0.45rem 0.9rem; border-radius: 6px; font-size: 0.8rem; font-weight: 600; text-decoration: none; cursor: pointer; border: none; }
  .btn-primary { background: #1A3C5E; color: white; }
  .btn-outline { background: transparent; border: 1.5px solid #ccc; color: #444; }
  .status-select { font-size: 0.75rem; padding: 0.3rem 0.5rem; border-radius: 5px; border: 1.5px solid #ddd; cursor: pointer; background: white; }
  .notes-area { width: 100%; margin-top: 0.6rem; padding: 0.5rem; border-radius: 6px; border: 1.5px solid #ddd; font-size: 0.8rem; resize: vertical; min-height: 50px; display: none; font-family: inherit; }
  .notes-area.visible { display: block; }
  .linkedin-section { background: white; border-radius: 12px; padding: 1.2rem 1.5rem; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-top: 4px solid #0077B5; }
  .linkedin-section h3 { color: #0077B5; font-size: 0.9rem; margin-bottom: 0.8rem; font-weight: 700; }
  .linkedin-links { display: flex; flex-wrap: wrap; gap: 0.6rem; }
  .linkedin-link { background: #0077B5; color: white; padding: 0.4rem 0.9rem; border-radius: 6px; font-size: 0.8rem; font-weight: 600; text-decoration: none; }
  .linkedin-link:hover { background: #005582; }
  .empty { text-align:center; color:#aaa; padding:2rem; font-size:0.9rem; }
"""

    js = """
function updateStatus(id, value) {
  try { localStorage.setItem('status_' + id, value); } catch(e) {}
}
function toggleNote(id) {
  var area = document.getElementById('notes' + id);
  if(area) area.classList.toggle('visible');
}
function saveNote(id, value) {
  try { localStorage.setItem('note_' + id, value); } catch(e) {}
}
(function() {
  try {
    document.querySelectorAll('.status-select').forEach(function(sel) {
      var match = sel.getAttribute('onchange').match(/'([^']+)'/);
      if(match) {
        var saved = localStorage.getItem('status_' + match[1]);
        if(saved) sel.value = saved;
      }
    });
    document.querySelectorAll('.notes-area').forEach(function(area) {
      var id = area.id.replace('notes','');
      var saved = localStorage.getItem('note_' + id);
      if(saved) area.value = saved;
    });
  } catch(e) {}
})();
"""

    html = "<!DOCTYPE html>\n"
    html += '<html lang="fr">\n<head>\n'
    html += '<meta charset="UTF-8">\n'
    html += '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    html += "<title>Dashboard Candidatures — Eric Georges</title>\n"
    html += "<style>" + css + "</style>\n"
    html += "</head>\n<body>\n"

    html += '<div class="header">'
    html += '<div class="header-top">'
    html += "<div>"
    html += "<h1>Dashboard <span>Candidatures</span></h1>"
    html += '<div class="header-sub">Eric Georges · Consultant ITSM Senior · Systeme Cyborg</div>'
    html += "</div>"
    html += '<div class="date-badge">Mis a jour le ' + updated + "</div>"
    html += "</div></div>\n"

    html += '<div class="stats">'
    html += '<div class="stat">Total <strong>' + str(total) + "</strong> offres</div>"
    html += '<div class="stat">Top Match <strong style="color:#1D5C2E">' + str(top_count) + "</strong></div>"
    html += '<div class="stat">Bon Match <strong style="color:#C5A028">' + str(medium_count) + "</strong></div>"
    html += '<div class="stat">Aujourd\'hui <strong>' + today + "</strong></div>"
    html += "</div>\n"

    html += "<main>\n"

    html += '<div class="linkedin-section">'
    html += "<h3>Recherches LinkedIn du jour — offres des 24 dernieres heures</h3>"
    html += '<div class="linkedin-links">' + linkedin_links + "</div>"
    html += "</div>\n"

    html += '<div class="section-label">Top Match — Score 70/100 et plus (' + str(top_count) + " offres)</div>"
    html += '<div class="grid">' + cards_top + "</div>\n"

    html += '<div class="section-label">Bon Match — Score 40 a 69/100 (' + str(medium_count) + " offres)</div>"
    html += '<div class="grid">' + cards_medium + "</div>\n"

    html += '<div class="section-label">Faible pertinence — Score inferieur a 40/100</div>'
    html += '<div class="grid">' + cards_low + "</div>\n"

    html += "</main>\n"
    html += "<script>" + js + "</script>\n"
    html += "</body>\n</html>"

    os.makedirs("output", exist_ok=True)
    with open("output/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("Dashboard genere — " + str(total) + " offres dont " + str(top_count) + " top match")


if __name__ == "__main__":
    main()

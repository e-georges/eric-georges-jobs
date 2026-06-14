import json
import os
from datetime import datetime

def score_color(score):
    if score >= 80: return "#1D5C2E"
    if score >= 60: return "#C5A028"
    if score >= 40: return "#1A3C5E"
    return "#8B1A1A"

def score_label(score):
    if score >= 80: return "🔥 Top Match"
    if score >= 60: return "⚡ Bon Match"
    if score >= 40: return "👀 À évaluer"
    return "❄️ Faible"

def contract_badge(contract):
    c = contract.lower()
    if any(x in c for x in ["mission", "freelance", "interim", "indépendant"]):
        return "Freelance", "#2C2C6E"
    if "cdi" in c: return "CDI", "#1D5C2E"
    if "cdd" in c: return "CDD", "#C5A028"
    return contract, "#1A3C5E"

def generate_card(job, idx):
    score = job.get("score", 0)
    color = score_color(score)
    label = score_label(score)
    contract_text, contract_color = contract_badge(job.get("contract", ""))
    cv = job.get("cv_recommended", "CDI")
    cv_color = "#2C2C6E" if cv == "Freelance" else "#1A3C5E"
    
    return f"""
    <div class="card" style="border-left-color:{color}">
      <div class="score-badge" style="background:{color}">
        {label} — {score}/100
      </div>
      
      <div class="card-header">
        <div class="card-icon">💼</div>
        <div>
          <div class="card-title">{job.get('title','')}</div>
          <div class="card-company">🏢 {job.get('company','Non précisé')} &nbsp;·&nbsp; 📍 {job.get('location','')}</div>
        </div>
      </div>

      <div class="card-meta">
        <span class="tag" style="background:{contract_color};color:white">{contract_text}</span>
        <span class="tag">💰 {job.get('salary','Non précisé')}</span>
        <span class="tag">📅 {job.get('date','')[:10]}</span>
        <span class="tag">🔗 {job.get('source','')}</span>
      </div>

      <div class="card-body">{job.get('ai_summary','')}</div>

      <div class="card-cv" style="border-left:3px solid {cv_color}">
        📄 CV recommandé : <span style="color:{cv_color};font-weight:700">{cv}</span>
        &nbsp;·&nbsp; <span style="font-weight:400;color:#555">{job.get('title_rewrite','')}</span>
      </div>

      <div class="card-actions">
        <a class="btn btn-primary" href="{job.get('url','#')}" target="_blank">🔗 Voir l'offre</a>
        <select class="status-select" onchange="updateStatus('{job.get('id',idx)}', this.value)">
          <option value="new">● Nouvelle</option>
          <option value="active">✅ À postuler</option>
          <option value="applied">✉ Envoyée</option>
          <option value="network">◎ Réseau</option>
          <option value="rejected">✗ Refusée</option>
        </select>
        <button class="btn btn-outline" onclick="toggleNote('{job.get('id',idx)}')">📝 Note</button>
      </div>
      <textarea class="notes-area" id="notes{job.get('id',idx)}" 
        onchange="saveNote('{job.get('id',idx)}', this.value)" 
        placeholder="Vos notes sur cette offre..."></textarea>
    </div>"""

def generate_linkedin_links():
    searches = [
        ("Head of ITSM Paris", "head+of+ITSM+paris"),
        ("ServiceNow Consultant Senior", "servicenow+consultant+senior+paris"),
        ("IT Governance Manager", "IT+governance+manager+paris"),
        ("DSI Transformation Freelance", "DSI+transformation+freelance+paris"),
        ("ITIL Expert Paris", "ITIL+expert+paris"),
    ]
    cards = ""
    for label, query in searches:
        cards += f"""
        <a class="linkedin-link" 
           href="https://www.linkedin.com/jobs/search/?keywords={query}&location=Paris&f_TPR=r86400" 
           target="_blank">
          🔍 {label}
        </a>"""
    return cards

def main():
    with open("data/jobs.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    jobs = data["jobs"]
    updated = data.get("updated_at", "")[:16].replace("T", " à ")
    total = len(jobs)
    top = len([j for j in jobs if j["score"] >= 70])
    medium = len([j for j in jobs if 40 <= j["score"] < 70])

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

    linkedin_links = generate_linkedin_links()

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Candidatures — Eric Georges</title>
<style>
  :root {{
    --navy: #1A3C5E; --gold: #C5A028; --green: #1D5C2E;
    --bordeaux: #8B1A1A; --indigo: #2C2C6E; --grey: #F5F7FA; --text: #1a1a2e;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f0f4f8; color: var(--text); }}
  
  .header {{
    background: linear-gradient(135deg, var(--navy) 0%, #0d2438 100%);
    color: white; padding: 2rem 2.5rem 1.5rem;
    border-bottom: 4px solid var(--gold);
  }}
  .header h1 {{ font-size: 2rem; font-weight: 800; }}
  .header h1 span {{ color: var(--gold); }}
  .header-sub {{ font-size: 0.9rem; opacity: 0.8; margin-top: 0.3rem; }}
  .date-badge {{
    background: rgba(197,160,40,0.2); border: 1px solid var(--gold);
    border-radius: 6px; padding: 0.4rem 0.9rem; font-size: 0.8rem; color: var(--gold);
  }}
  .header-top {{ display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem; }}

  .stats {{
    display: flex; gap: 1.5rem; padding: 1rem 2.5rem;
    background: white; border-bottom: 1px solid #dde; flex-wrap: wrap;
  }}
  .stat {{ font-size: 0.85rem; }}
  .stat strong {{ font-size: 1.1rem; }}

  main {{ max-width: 1300px; margin: 0 auto; padding: 1.5rem; }}

  .section-label {{
    font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 2px; color: #888; margin: 1.8rem 0 0.8rem;
    border-left: 3px solid var(--gold); padding-left: 0.6rem;
  }}

  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 1.2rem; }}

  .card {{
    background: white; border-radius: 12px; padding: 1.4rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-left: 5px solid var(--navy);
    position: relative; transition: transform 0.15s, box-shadow 0.15s;
  }}
  .card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }}

  .score-badge {{
    position: absolute; top: 1rem; right: 1rem;
    padding: 0.25rem 0.7rem; border-radius: 20px;
    font-size: 0.7rem; font-weight: 700; color: white;
  }}

  .card-header {{ display: flex; gap: 0.8rem; margin-bottom: 0.8rem; padding-right: 8rem; }}
  .card-icon {{ font-size: 1.5rem; }}
  .card-title {{ font-size: 1rem; font-weight: 700; line-height: 1.3; }}
  .card-company {{ font-size: 0.85rem; color: #555; margin-top: 0.2rem; }}

  .card-meta {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.8rem 0; }}
  .tag {{
    background: var(--grey); border-radius: 4px;
    padding: 0.2rem 0.5rem; font-size: 0.72rem; color: #444;
  }}

  .card-body {{
    font-size: 0.83rem; color: #555; line-height: 1.5;
    margin-bottom: 0.9rem; border-top: 1px solid #eee; padding-top: 0.7rem;
  }}

  .card-cv {{
    font-size: 0.78rem; background: #f0f4f8; border-radius: 6px;
    padding: 0.4rem 0.7rem; margin-bottom: 0.8rem; color: var(--navy);
    font-weight: 600;
  }}

  .card-actions {{ display: flex; gap: 0.5rem; flex-wrap: wrap; }}
  .btn {{
    display: inline-flex; align-items: center; gap: 0.3rem;
    padding: 0.45rem 0.9rem; border-radius: 6px; font-size: 0.8rem;
    font-weight: 600; text-decoration: none; cursor: pointer; border: none;
    transition: all 0.15s;
  }}
  .btn-primary {{ background: var(--navy); color: white; }}
  .btn-outline {{ background: transparent; border: 1.5px solid #ccc; color: #444; }}
  .btn-outline:hover {{ border-color: var(--navy); color: var(--navy); }}

  .status-select {{
    font-size: 0.75rem; padding: 0.3rem 0.5rem; border-radius: 5px;
    border: 1.5px solid #ddd; cursor: pointer; background: white;
  }}

  .notes-area {{
    width: 100%; margin-top: 0.6rem; padding: 0.5rem; border-radius: 6px;
    border: 1.5px solid #ddd; font-size: 0.8rem; resize: vertical;
    min-height: 50px; display: none; font-family: inherit;
  }}
  .notes-area.visible {{ display: block; }}

  .linkedin-section {{
    background: white; border-radius: 12px; padding: 1.2rem 1.5rem;
    margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border-top: 4px solid #0077B5;
  }}
  .linkedin-section h3 {{ color: #0077B5; font-size: 0.9rem; margin-bottom: 0.8rem; font-weight: 700; }}
  .linkedin-links {{ display: flex; flex-wrap: wrap; gap: 0.6rem; }}
  .linkedin-link {{
    background: #0077B5; color: white; padding: 0.4rem 0.9rem;
    border-radius: 6px; font-size: 0.8rem; font-weight: 600;
    text-decoration: none; transition: background 0.15s;
  }}
  .linkedin-link:hover {{ background: #005582; }}

  .empty {{ text-align:center; color:#aaa; padding:2rem; font-size:0.9rem; }}
</style>
</head>
<body>

<div class="header">
  <div class="header-top">
    <div>
      <h1>Dashboard <span>Candidatures</span></h1>
      <div class="header-sub">Eric Georges · Consultant ITSM Senior · Système Cyborg</div>
    </div>
    <div class="date-badge">🕐 Mis à jour le {updated}</div>
  </div>
</div>

<div class="stats">
  <div class="stat">📋 Total <strong>{total}</strong> offres</div>
  <div class="stat">🔥 Top Match <strong style="color:#1D5C2E">{top}</strong></div>
  <div class="stat">⚡ Bon Match <strong style="color:#C5A028">{medium}</strong></div>
  <div class="stat">📅 Aujourd'hui <strong>{datetime.now().strftime('%d/%m/%Y')}</strong></div>
</div>

<main>

  <!-- LINKEDIN -->
  <div class="linkedin-section">
    <h3>🔍 Recherches LinkedIn du jour — cliquez pour ouvrir (offres des dernières 24h)</h3>
    <div class="linkedin-links">
      {linkedin_links}
    </div>
  </div>

  <!-- TOP OFFRES -->
  <div class="section-label">🔥 Top Match — Score ≥ 70/100 ({top} offres)</div>
  <div class="grid">
    {cards_top if cards_top else '<div class="empty">Aucune offre top match aujourd\'hui</div>'}
  </div>

  <!-- BON MATCH -->
  <div class="section-label">⚡ Bon Match — Score 40–69/100 ({medium} offres)</div>
  <div class="grid">
    {cards_medium if cards_medium else '<div class="empty">Aucune offre dans cette catégorie</div>'}
  </div>

  <!-- FAIBLE -->
  <div class="section-label">❄️ Faible pertinence — Score < 40/100</div>
  <div class="grid">
    {cards_low if cards_low else '<div class="empty">Aucune offre dans cette catégorie</div>'}
  </div>

</main>

<script>
function updateStatus(id, value) {{
  try {{ localStorage.setItem('status_' + id, value); }} catch(e) {{}}
}}
function toggleNote(id) {{
  const area = document.getElementById('notes' + id);
  if(area) area.classList.toggle('visible');
}}
function saveNote(id, value) {{
  try {{ localStorage.setItem('note_' + id, value); }} catch(e) {{}}
}}
(function() {{
  try {{
    document.querySelectorAll('.status-select').forEach(sel => {{
      const id = sel.getAttribute('onchange').match(/'([^']+)'/)[1];
      const saved = localStorage.getItem('status_' + id);
      if(saved) sel.value = saved;
    }});
    document.querySelectorAll('.notes-area').forEach(area => {{
      const saved = localStorage.getItem('note_' + area.id.replace('notes',''));
      if(saved) area.value = saved;
    }});
  }} catch(e) {{}}
}})();
</script>
</body>
</html>"""

    os.makedirs("output", exist_ok=True)
    with open("output/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Dashboard généré — {total} offres dont {top} top match")

if __name__ == "__main__":
    main()

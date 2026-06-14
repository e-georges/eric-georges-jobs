import json
import os
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

SCORING_PROMPT = """Tu es un expert en recrutement IT senior en France.
Analyse cette offre d'emploi pour Eric Georges, consultant ITSM Senior (20 ans d'exp, ITIL Expert, ServiceNow CSA, ex-LVMH, DGAC).

OFFRE :
Titre : {title}
Entreprise : {company}
Contrat : {contract}
Salaire : {salary}
Description : {description}

Réponds UNIQUEMENT en JSON valide, sans texte avant ou après :
{{
  "score": <nombre entre 0 et 100>,
  "cv_recommended": "<CDI ou Freelance>",
  "reasons": "<2 phrases max expliquant le score>",
  "title_rewrite": "<nouveau titre CV adapté à cette offre, max 10 mots>",
  "tagline_rewrite": "<nouvelle tagline CV, max 15 mots>",
  "profile_rewrite": "<nouvelle accroche profil CV, 3 phrases max, en français>"
}}

Critères de scoring :
- +30 pts : mots-clés ITSM, ServiceNow, ITIL, Gouvernance IT présents
- +20 pts : séniorité Head of / Lead / Senior / Manager / Directeur
- +20 pts : localisation Paris / Île-de-France / Remote
- +15 pts : salaire >= 100K€ ou TJM >= 700€/j
- +15 pts : secteur luxe, banque, assurance, aéro, santé, énergie
- -50 pts : hors Île-de-France sans remote, ou TJM < 700€/j
- CV Freelance si contrat mission/freelance/interim, sinon CV CDI"""

def score_job(job):
    prompt = SCORING_PROMPT.format(
        title=job["title"],
        company=job["company"],
        contract=job["contract"],
        salary=job["salary"],
        description=job["description"]
    )
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500
    )
    
    raw = response.choices[0].message.content.strip()
    
    # Nettoyer si besoin
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    
    return json.loads(raw)

def main():
    with open("data/jobs.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    jobs = data["jobs"]
    print(f"🤖 Scoring {len(jobs)} offres via Groq...")
    
    scored = []
    for i, job in enumerate(jobs):
        try:
            result = score_job(job)
            job["score"] = result.get("score", 0)
            job["cv_recommended"] =

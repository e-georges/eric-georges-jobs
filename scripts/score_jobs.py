import json
import os
import re
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

SCORING_PROMPT = """Tu es un expert en recrutement IT senior en France.
Analyse cette offre d'emploi pour Eric Georges, consultant ITSM Senior (20 ans exp, ITIL Expert, ServiceNow CSA, ex-LVMH, DGAC).

OFFRE :
Titre : {title}
Entreprise : {company}
Contrat : {contract}
Salaire : {salary}
Description : {description}

Reponds UNIQUEMENT en JSON valide, sans texte avant ou apres :
{{
  "score": 75,
  "cv_recommended": "CDI",
  "reasons": "Explication courte du score en 2 phrases.",
  "title_rewrite": "Nouveau titre adapte max 10 mots",
  "tagline_rewrite": "Nouvelle tagline max 15 mots",
  "profile_rewrite": "Nouvelle accroche profil en 3 phrases max."
}}

Criteres de scoring :
- +30 pts : mots-cles ITSM, ServiceNow, ITIL, Gouvernance IT presents
- +20 pts : seniorite Head of / Lead / Senior / Manager / Directeur
- +20 pts : localisation Paris / Ile-de-France / Remote
- +15 pts : salaire >= 100K euros ou TJM >= 700 euros par jour
- +15 pts : secteur luxe, banque, assurance, aero, sante, energie
- -50 pts : hors Ile-de-France sans remote, ou TJM < 700 euros par jour
- Mettre cv_recommended a Freelance si contrat mission/freelance/interim, sinon CDI"""


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
        max_tokens=600
    )

    raw = response.choices[0].message.content.strip()

    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    return json.loads(raw)


def main():
    with open("data/jobs.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    jobs = data["jobs"]
    print(f"Scoring {len(jobs)} offres via Groq...")

    scored = []
    for i, job in enumerate(jobs):
        try:
            result = score_job(job)
            job["score"] = int(result.get("score", 0))
            job["cv_recommended"] = str(result.get("cv_recommended", "CDI"))
            job["ai_summary"] = str(result.get("reasons", ""))
            job["title_rewrite"] = str(result.get("title_rewrite", ""))
            job["tagline_rewrite"] = str(result.get("tagline_rewrite", ""))
            job["profile_rewrite"] = str(result.get("profile_rewrite", ""))
            print(f"[{i+1}/{len(jobs)}] {job['title']} — Score: {job['score']}/100")
        except Exception as e:
            print(f"Erreur sur {job['title']} : {e}")
            job["score"] = 0
            job["cv_recommended"] = "CDI"
            job["ai_summary"] = ""
            job["title_rewrite"] = ""
            job["tagline_rewrite"] = ""
            job["profile_rewrite"] = ""
        scored.append(job)

    scored.sort(key=lambda x: x["score"], reverse=True)
    data["jobs"] = scored

    with open("data/jobs.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    top = [j for j in scored if j["score"] >= 70]
    print(f"{len(top)} offres a fort potentiel (score >= 70)")
    print("data/jobs.json mis a jour")


if __name__ == "__main__":
    main()

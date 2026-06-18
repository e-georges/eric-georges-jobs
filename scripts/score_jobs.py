import json
import os
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

SCORING_PROMPT = """Tu es un expert en recrutement IT senior en France.
Analyse cette offre pour Eric Georges, consultant ITSM Senior (20 ans exp, ITIL Expert, ServiceNow CSA, ex-LVMH, DGAC).

REGLES DE REJET STRICTES (mettre rejected a true) :
1. CDI/CDD avec salaire annuel clairement INFERIEUR a 80 000 EUR (package inclus) -> REJETER
2. Mission freelance avec TJM clairement INFERIEUR a 750 EUR/jour -> REJETER
3. Si le salaire/TJM n'est PAS precise :
   - GARDER (rejected=false) UNIQUEMENT si le poste est de niveau senior strategique :
     Head of IT, Directeur IT, DSI, CTO, CIO, COO, IT Director, Head of ITSM,
     Practice Director, ou tout poste dont l'IA estime de facon credible que la
     remuneration atteindra >= 80K EUR (CDI) ou >= 750 EUR/jour (freelance)
   - REJETER (rejected=true) si c'est un poste junior, intermediaire, technicien,
     analyste, support, ou administrateur sans dimension strategique/management

OFFRE :
Titre : {title}
Entreprise : {company}
Contrat : {contract}
Salaire : {salary}
Description : {description}

Reponds UNIQUEMENT en JSON valide, sans texte avant ou apres :
{{
  "rejected": false,
  "score": 75,
  "cv_recommended": "CDI",
  "reasons": "Explication courte en 2 phrases incluant l'estimation salariale.",
  "title_rewrite": "Nouveau titre adapte max 10 mots",
  "tagline_rewrite": "Nouvelle tagline max 15 mots",
  "profile_rewrite": "Nouvelle accroche profil en 3 phrases max."
}}

Criteres de scoring (si non rejete) :
- +30 pts : mots-cles ITSM, ServiceNow, ITIL, Gouvernance IT presents
- +20 pts : seniorite Head of / Lead / Senior / Manager / Directeur / CxO
- +20 pts : localisation Paris / Ile-de-France / Remote
- +15 pts : salaire >= 100K euros ou TJM >= 750 euros par jour
- +15 pts : secteur luxe, banque, assurance, aero, sante, energie
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

    kept = []
    rejected_count = 0

    for i, job in enumerate(jobs):
        try:
            result = score_job(job)

            if result.get("rejected", False):
                rejected_count += 1
                print(f"[{i+1}/{len(jobs)}] REJETE : {job['title']}")
                continue

            job["score"] = int(result.get("score", 0))
            job["cv_recommended"] = str(result.get("cv_recommended", "CDI"))
            job["ai_summary"] = str(result.get("reasons", ""))
            job["title_rewrite"] = str(result.get("title_rewrite", ""))
            job["tagline_rewrite"] = str(result.get("tagline_rewrite", ""))
            job["profile_rewrite"] = str(result.get("profile_rewrite", ""))
            print(f"[{i+1}/{len(jobs)}] {job['title']} — Score: {job['score']}/100")
            kept.append(job)
        except Exception as e:
            print(f"Erreur sur {job['title']} : {e}")
            job["score"] = 0
            job["cv_recommended"] = "CDI"
            job["ai_summary"] = ""
            job["title_rewrite"] = ""
            job["tagline_rewrite"] = ""
            job["profile_rewrite"] = ""
            kept.append(job)

    kept.sort(key=lambda x: x["score"], reverse=True)
    data["jobs"] = kept
    data["total"] = len(kept)

    with open("data/jobs.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    top = [j for j in kept if j["score"] >= 70]
    print(f"\n{rejected_count} offres rejetees (salaire insuffisant ou poste non strategique)")
    print(f"{len(kept)} offres conservees dont {len(top)} a fort potentiel")
    print("data/jobs.json mis a jour")


if __name__ == "__main__":
    main()

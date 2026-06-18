import json
import os
import time
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

# Pre-filtre par mots-cles AVANT d'appeler l'IA (economise les tokens)
EXCLUDE_KEYWORDS = [
    "stage", "stagiaire", "alternance", "apprenti", "junior",
    "technicien", "helpdesk", "support utilisateur", "hotline",
    "juriste", "comptable", "back-office", "middle office",
    "ingenieur reseau", "telecom engineer"
]

INCLUDE_KEYWORDS = [
    "itsm", "servicenow", "itil", "gouvernance", "service management",
    "head of", "directeur", "director", "dsi", "cto", "cio", "coo",
    "manager", "consultant senior", "transformation", "service delivery",
    "incident manager", "process owner", "practice"
]


def prefilter(job):
    text = (job["title"] + " " + job["description"]).lower()
    if any(k in text for k in EXCLUDE_KEYWORDS):
        if not any(k in job["title"].lower() for k in ["head", "directeur", "director", "manager", "senior"]):
            return False
    if any(k in text for k in INCLUDE_KEYWORDS):
        return True
    return False


SCORING_PROMPT = """Expert recrutement IT senior France. Profil : Eric Georges, consultant ITSM Senior (20 ans, ITIL Expert, ServiceNow CSA, ex-LVMH, DGAC).

REJET (rejected=true) si :
- CDI/CDD salaire < 80000 EUR/an clairement indique
- Freelance TJM < 750 EUR/jour clairement indique
- Salaire non precise ET poste junior/technicien/analyste sans dimension strategique
GARDER si salaire non precise ET poste senior strategique (Head of IT, DSI, CTO, CIO, COO, Director, Practice Director) ou remuneration credible >= seuils.

OFFRE :
Titre : {title}
Contrat : {contract}
Salaire : {salary}
Description : {description}

JSON uniquement :
{{
  "rejected": false,
  "score": 75,
  "cv_recommended": "CDI",
  "reasons": "2 phrases max.",
  "title_rewrite": "titre adapte max 10 mots",
  "tagline_rewrite": "tagline max 15 mots",
  "profile_rewrite": "accroche 3 phrases max."
}}

Score : +30 ITSM/ServiceNow/ITIL/Gouvernance · +20 seniorite · +20 Paris/IDF/remote · +15 salaire>=100K ou TJM>=750 · +15 secteur luxe/banque/assurance/aero/sante/energie. cv_recommended=Freelance si mission/freelance/interim, sinon CDI."""


def score_job(job):
    prompt = SCORING_PROMPT.format(
        title=job["title"],
        contract=job["contract"],
        salary=job["salary"],
        description=job["description"][:400]
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=400
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
    print(f"Total recu : {len(jobs)} offres")

    # Pre-filtre local (gratuit, pas d'IA)
    candidates = [j for j in jobs if prefilter(j)]
    print(f"Apres pre-filtre : {len(candidates)} offres a scorer par IA")

    kept = []
    rejected_count = 0

    for i, job in enumerate(candidates):
        try:
            result = score_job(job)

            if result.get("rejected", False):
                rejected_count += 1
                print(f"[{i+1}/{len(candidates)}] REJETE : {job['title']}")
                continue

            job["score"] = int(result.get("score", 0))
            job["cv_recommended"] = str(result.get("cv_recommended", "CDI"))
            job["ai_summary"] = str(result.get("reasons", ""))
            job["title_rewrite"] = str(result.get("title_rewrite", ""))
            job["tagline_rewrite"] = str(result.get("tagline_rewrite", ""))
            job["profile_rewrite"] = str(result.get("profile_rewrite", ""))
            print(f"[{i+1}/{len(candidates)}] {job['title']} — Score: {job['score']}/100")
            kept.append(job)
        except Exception as e:
            print(f"Erreur sur {job['title']} : {str(e)[:100]}")
            job["score"] = 50
            job["cv_recommended"] = "CDI"
            job["ai_summary"] = "Score IA indisponible — a evaluer manuellement"
            job["title_rewrite"] = ""
            job["tagline_rewrite"] = ""
            job["profile_rewrite"] = ""
            kept.append(job)
        time.sleep(1)

    kept.sort(key=lambda x: x["score"], reverse=True)
    data["jobs"] = kept
    data["total"] = len(kept)

    with open("data/jobs.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    top = [j for j in kept if j["score"] >= 70]
    print(f"\n{rejected_count} rejetees · {len(kept)} conservees dont {len(top)} top match")
    print("data/jobs.json mis a jour")


if __name__ == "__main__":
    main()

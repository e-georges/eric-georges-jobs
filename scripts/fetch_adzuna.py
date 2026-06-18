import requests
import json
import os
from datetime import datetime


def fetch_adzuna_jobs():
    app_id = os.environ["ADZUNA_APP_ID"]
    app_key = os.environ["ADZUNA_APP_KEY"]

    searches = [
        "ITSM ServiceNow",
        "ITIL gouvernance",
        "IT Service Management",
        "ServiceNow consultant",
        "DSI transformation",
        "responsable informatique",
    ]

    all_jobs = []
    seen_ids = set()

    for keyword in searches:
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "what": keyword,
            "where": "Paris",
            "distance": 30,
            "results_per_page": 10,
            "content-type": "application/json",
            "sort_by": "date",
        }

        resp = requests.get(
            "https://api.adzuna.com/v1/api/jobs/fr/search/1",
            params=params
        )

        print(f"Search '{keyword}' → status {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            resultats = data.get("results", [])
            print(f"  → {len(resultats)} offres trouvees")
            for job in resultats:
                jid = "adzuna_" + str(job.get("id", ""))
                if jid not in seen_ids:
                    seen_ids.add(jid)

                    salary_min = job.get("salary_min")
                    salary_max = job.get("salary_max")
                    if salary_min and salary_max:
                        salary = f"{int(salary_min)} - {int(salary_max)} EUR/an"
                    elif salary_min:
                        salary = f"A partir de {int(salary_min)} EUR/an"
                    else:
                        salary = "Non precise"

                    all_jobs.append({
                        "id": jid,
                        "title": job.get("title", ""),
                        "company": job.get("company", {}).get("display_name", "Non precise"),
                        "location": job.get("location", {}).get("display_name", ""),
                        "contract": job.get("contract_time", "") or job.get("contract_type", "") or "Non precise",
                        "salary": salary,
                        "description": job.get("description", "")[:800],
                        "url": job.get("redirect_url", "#"),
                        "date": job.get("created", ""),
                        "source": "Adzuna",
                        "score": 0,
                        "cv_recommended": "",
                        "ai_summary": "",
                        "title_rewrite": "",
                        "tagline_rewrite": "",
                        "profile_rewrite": "",
                        "status": "new"
                    })
        else:
            print(f"  → Erreur : {resp.text[:200]}")

    return all_jobs


def main():
    print(f"Fetching Adzuna jobs — {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    new_jobs = fetch_adzuna_jobs()
    print(f"{len(new_jobs)} offres Adzuna recuperees")

    # Charger les offres existantes (France Travail)
    existing = []
    if os.path.exists("data/jobs.json"):
        with open("data/jobs.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            existing = data.get("jobs", [])

    # Fusionner en evitant les doublons d'id
    existing_ids = set(j["id"] for j in existing)
    merged = existing + [j for j in new_jobs if j["id"] not in existing_ids]

    with open("data/jobs.json", "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": datetime.now().isoformat(),
            "total": len(merged),
            "jobs": merged
        }, f, ensure_ascii=False, indent=2)

    print(f"Total apres fusion : {len(merged)} offres")
    print("data/jobs.json mis a jour")


if __name__ == "__main__":
    main()

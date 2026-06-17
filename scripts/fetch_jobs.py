import requests
import json
import os
from datetime import datetime


def get_ft_token():
    client_id = os.environ["FT_CLIENT_ID"]
    client_secret = os.environ["FT_CLIENT_SECRET"]

    response = requests.post(
        "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "api_offresdemploiv2 o2dsoffre"
        }
    )

    result = response.json()
    print(f"Token response status: {response.status_code}")

    if "access_token" not in result:
        raise Exception(f"Erreur token France Travail : {result}")

    return result["access_token"]


def fetch_jobs(token):
    headers = {"Authorization": f"Bearer {token}"}

    searches = [
        "ITSM ServiceNow",
        "ITIL gouvernance IT",
        "Head IT Service Management",
        "ServiceNow consultant",
        "DSI transformation IT",
        "IT Service Management",
        "responsable ITSM",
        "gouvernance IT",
        "transformation digitale DSI",
        "pilotage IT",
    ]

    all_jobs = []
    seen_ids = set()

    for keyword in searches:
        params = {
            "motsCles": keyword,
            "departement": "75",
            "range": "0-14",
            "sort": "1",
        }

        resp = requests.get(
            "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search",
            headers=headers,
            params=params
        )

        print(f"Search '{keyword}' → status {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            resultats = data.get("resultats", [])
            print(f"  → {len(resultats)} offres trouvees")
            for job in resultats:
                if job["id"] not in seen_ids:
                    seen_ids.add(job["id"])
                    all_jobs.append({
                        "id": job["id"],
                        "title": job.get("intitule", ""),
                        "company": job.get("entreprise", {}).get("nom", "Non precise"),
                        "location": job.get("lieuTravail", {}).get("libelle", ""),
                        "contract": job.get("typeContratLibelle", ""),
                        "salary": job.get("salaire", {}).get("libelle", "Non precise"),
                        "description": job.get("description", "")[:800],
                        "url": job.get("origineOffre", {}).get("urlOrigine",
                               f"https://candidat.francetravail.fr/offres/emploi/detail/{job['id']}"),
                        "date": job.get("dateCreation", ""),
                        "source": "France Travail",
                        "score": 0,
                        "cv_recommended": "",
                        "ai_summary": "",
                        "title_rewrite": "",
                        "tagline_rewrite": "",
                        "profile_rewrite": "",
                        "status": "new"
                    })
        elif resp.status_code == 204:
            print(f"  → Aucun resultat")
        else:
            print(f"  → Erreur : {resp.text[:200]}")

    return all_jobs


def main():
    print(f"Fetching jobs — {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    token = get_ft_token()
    jobs = fetch_jobs(token)

    print(f"{len(jobs)} offres recuperees")

    os.makedirs("data", exist_ok=True)
    with open("data/jobs.json", "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": datetime.now().isoformat(),
            "total": len(jobs),
            "jobs": jobs
        }, f, ensure_ascii=False, indent=2)

    print("data/jobs.json sauvegarde")


if __name__ == "__main__":
    main()

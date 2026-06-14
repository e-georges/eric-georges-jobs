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
    print(f"Token response body: {result}")

    if "access_token" not in result:
        raise Exception(f"Erreur token France Travail : {result}")

    return result["access_token"]


def fetch_jobs(token):
    headers = {"Authorization": f"Bearer {token}"}

    searches = [
        {"keywords": "ITSM ServiceNow", "rome": "M1801"},
        {"keywords": "ITIL gouvernance IT", "rome": "M1801"},
        {"keywords": "Head IT Service Management", "rome": "M1801"},
        {"keywords": "ServiceNow consultant", "rome": "M1802"},
        {"keywords": "DSI transformation IT freelance", "rome": "M1801"},
    ]

    all_jobs = []
    seen_ids = set()

    for search in searches:
        params = {
            "motsCles": search["keywords"],
            "codeROME": search["rome"],
            "commune": "75056",
            "distance": 30,
            "range": "0-14",
            "sort": "1",
        }

        resp = requests.get(
            "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search",
            headers=headers,
            params=params
        )

        print(f"Search '{search['keywords']}' → status {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            for job in data.get("resultats", []):
                if job["id"] not in seen_ids:
                    seen_ids.add(job["id"])
                    all_jobs.append({
                        "id": job["id"],
                        "title": job.get("intitule", ""),
                        "company": job.get("entreprise", {}).get("nom", "Non précisé"),
                        "location": job.get("lieuTravail", {}).get("libelle", ""),
                        "contract": job.get("typeContratLibelle", ""),
                        "salary": job.get("salaire", {}).get("libelle", "Non précisé"),
                        "description": job.get("description", "")[:800],
                        "url": job.get("origineOffre", {}).get("urlOrigine",
                               f"https://candidat.francetravail.fr/offres/emploi/detail/{job['id']}"),
                        "date": job.get("dateCreation", ""),
                        "source": "France Travail",
                        "score": 0,
                        "cv_recommended": "",
                        "ai_summary": "",
                        "status": "new"
                    })
        else:
            print(f"Erreur recherche : {resp.text[:200]}")

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

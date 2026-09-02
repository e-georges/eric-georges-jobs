# English@Work — apprendre l'anglais professionnel

Application web statique pour travailler l'anglais des affaires : vocabulaire,
expressions idiomatiques, dialogues audio, flashcards à répétition espacée et quiz.
Pensée pour un francophone en environnement IT / conseil, avec une insistance
particulière sur les erreurs typiques des francophones.

Tout tourne dans le navigateur : pas de compte, pas de serveur, pas de clé d'API.
La progression est enregistrée dans le `localStorage` ; elle s'exporte et se restaure
sous forme d'un bloc JSON copiable, pour passer d'un appareil à l'autre.

## Contenu

| Module | Thème | Niveau |
|---|---|---|
| 🗣️ | Réunions & conf calls | B1 → B2 |
| ✉️ | Emails professionnels | A2 → B2 |
| 📊 | Présentations & pitchs | B1 → C1 |
| 🤝 | Négociation & relation client | B2 → C1 |
| 🎯 | Entretiens & carrière | B1 → C1 |
| ⚙️ | IT, projet & agilité | B1 → C1 |
| ☕ | Small talk & réseautage | A2 → B2 |
| 📞 | Chiffres, dates & téléphone | A2 → B1 |

Soit 190 cartes (110 mots, 80 expressions), 8 dialogues (72 répliques),
46 pièges corrigés et 56 questions de quiz.

Chaque module propose six onglets : **Vocabulaire**, **Expressions**, **Dialogue**,
**Pièges**, **Flashcards** et **Quiz**.

## Fonctionnement pédagogique

- **Flashcards FR → EN** par défaut : on produit l'anglais plutôt que de le reconnaître,
  car c'est l'effort de rappel qui ancre la mémoire. Le sens est inversable d'un clic.
- **Répétition espacée (Leitner, 5 boîtes)** : une bonne réponse fait monter la carte
  d'une boîte et allonge l'intervalle — 1, 3, 7, 21 puis 45 jours. Une erreur la ramène
  en boîte 1 et la carte revient dans la journée. Une carte en boîte 4 ou 5 est comptée
  comme acquise.
- **Révision du jour** : file unique regroupant les cartes échues de tous les modules,
  complétée par des nouvelles cartes si la file est courte.
- **Prononciation** : chaque phrase anglaise se lit à voix haute via l'API Web Speech
  du navigateur (voix `en-GB` privilégiée). Les dialogues s'écoutent en continu.
- **Quiz** : QCM et textes à trous, avec une explication affichée systématiquement,
  y compris en cas de bonne réponse.

Raccourcis clavier en mode flashcard : `Espace` retourne la carte, `1` / `←` la marque
comme ratée, `2` / `→` comme sue.

## Lancer en local

```bash
python scripts/build.py            # valide le contenu et génère ./output
python -m http.server 8000 -d output
# puis ouvrir http://localhost:8000
```

Aucune dépendance : la bibliothèque standard de Python suffit.

## Structure du dépôt

```
app/            source de l'application (index.html, styles.css, app.js)
data/modules/   un fichier JSON par module de cours
scripts/build.py  valide les modules, les fusionne et produit ./output
output/         artefact de build, non versionné
```

## Ajouter ou modifier un module

Créez un fichier dans `data/modules/`. Les fichiers sont chargés par ordre
alphabétique, d'où le préfixe numérique. `scripts/build.py` refuse de construire si
le schéma n'est pas respecté — les erreurs sont listées avec le nom du fichier.

```jsonc
{
  "id": "presentations",           // identifiant unique, utilisé dans l'URL
  "title": "Présentations & pitchs",
  "title_en": "Presentations & Pitches",
  "icon": "📊",
  "level": "B1 → C1",
  "summary": "Une phrase affichée sur la carte du module.",

  "vocabulary": [
    {
      "en": "outline", "fr": "plan, grandes lignes", "type": "n.",
      "example": "Let me start with a quick outline.",
      "example_fr": "Je commence par un aperçu rapide du plan."
    }
  ],

  "phrases": [
    { "en": "Shall we get started?", "fr": "On commence ?", "context": "Ouvrir" }
  ],

  "dialogue": {
    "title": "Steering committee",
    "lines": [{ "speaker": "Claire", "en": "Shall we begin?", "fr": "On commence ?" }]
  },

  "pitfalls": [
    {
      "wrong": "I am agree with you.",
      "right": "I agree with you.",
      "why": "Agree est un verbe, jamais un adjectif."
    }
  ],

  "quiz": [
    {
      "type": "mcq",
      "question": "« Actually » signifie :",
      "options": ["actuellement", "en fait"],
      "answer": 1,                 // index de la bonne option
      "explanation": "Faux ami : « actuellement » se dit currently."
    },
    {
      "type": "gap",
      "question": "Let's ___ base next week.",   // le trou s'écrit ___
      "answer": "touch",
      "alternatives": ["touch base"],            // facultatif
      "explanation": "To touch base = faire un point rapide."
    }
  ]
}
```

`en` et `fr` sont obligatoires pour chaque entrée de `vocabulary` et `phrases` ;
tous les autres champs de contenu (`dialogue`, `pitfalls`, `quiz`) sont facultatifs
mais validés s'ils sont présents. Chaque mot et chaque expression devient
automatiquement une flashcard.

## Déploiement

Le workflow `.github/workflows/deploy.yml` valide le contenu à chaque push et
publie `output/` sur la branche `gh-pages` lorsqu'un commit atteint `main`.
Les pull requests sont construites sans être déployées.

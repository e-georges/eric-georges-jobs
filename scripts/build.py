#!/usr/bin/env python3
"""Construit l'application English@Work dans ./output.

Fusionne les modules de data/modules/*.json en un seul curriculum, le valide,
puis copie l'application statique (HTML/CSS/JS) prête à être publiée.
"""

import json
import os
import shutil
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES_DIR = os.path.join(ROOT, "data", "modules")
APP_DIR = os.path.join(ROOT, "app")
OUT_DIR = os.path.join(ROOT, "output")


def load_modules():
    """Charge les modules par ordre alphabétique de nom de fichier."""
    if not os.path.isdir(MODULES_DIR):
        sys.exit("Repertoire introuvable : " + MODULES_DIR)

    modules = []
    for name in sorted(os.listdir(MODULES_DIR)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(MODULES_DIR, name)
        with open(path, "r", encoding="utf-8") as f:
            try:
                modules.append((name, json.load(f)))
            except json.JSONDecodeError as exc:
                sys.exit("JSON invalide dans %s : %s" % (name, exc))
    return modules


def validate(modules):
    """Verifie la structure des modules. Retourne la liste des erreurs."""
    errors = []
    seen_ids = set()

    for name, mod in modules:
        def err(msg):
            errors.append("%s : %s" % (name, msg))

        for field in ("id", "title", "title_en", "level", "summary"):
            if not mod.get(field):
                err("champ obligatoire manquant : " + field)

        mod_id = mod.get("id")
        if mod_id in seen_ids:
            err("identifiant en double : " + str(mod_id))
        seen_ids.add(mod_id)

        for i, item in enumerate(mod.get("vocabulary", [])):
            if not item.get("en") or not item.get("fr"):
                err("vocabulary[%d] : 'en' et 'fr' sont obligatoires" % i)

        for i, item in enumerate(mod.get("phrases", [])):
            if not item.get("en") or not item.get("fr"):
                err("phrases[%d] : 'en' et 'fr' sont obligatoires" % i)

        for i, line in enumerate((mod.get("dialogue") or {}).get("lines", [])):
            if not line.get("speaker") or not line.get("en"):
                err("dialogue.lines[%d] : 'speaker' et 'en' sont obligatoires" % i)

        for i, p in enumerate(mod.get("pitfalls", [])):
            if not p.get("wrong") or not p.get("right"):
                err("pitfalls[%d] : 'wrong' et 'right' sont obligatoires" % i)

        for i, q in enumerate(mod.get("quiz", [])):
            qtype = q.get("type")
            if qtype == "mcq":
                options = q.get("options") or []
                answer = q.get("answer")
                if len(options) < 2:
                    err("quiz[%d] : au moins deux options sont necessaires" % i)
                if not isinstance(answer, int) or not 0 <= answer < len(options):
                    err("quiz[%d] : 'answer' doit etre un index valide de 'options'" % i)
            elif qtype == "gap":
                if not q.get("answer"):
                    err("quiz[%d] : 'answer' est obligatoire pour un texte a trous" % i)
                if "___" not in (q.get("question") or ""):
                    err("quiz[%d] : la question devrait contenir '___'" % i)
            else:
                err("quiz[%d] : type inconnu %r (attendu 'mcq' ou 'gap')" % (i, qtype))

    return errors


def build(modules):
    curriculum = {
        "generated_at": date.today().isoformat(),
        "modules": [mod for _, mod in modules],
    }

    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)

    with open(os.path.join(APP_DIR, "index.html"), "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("<!--BUILD_DATE-->", "mis a jour le " + date.today().strftime("%d/%m/%Y"))

    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    payload = json.dumps(curriculum, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(OUT_DIR, "curriculum.js"), "w", encoding="utf-8") as f:
        f.write("window.CURRICULUM=" + payload + ";\n")

    # Egalement expose en JSON brut, pratique pour reutiliser le contenu ailleurs.
    with open(os.path.join(OUT_DIR, "curriculum.json"), "w", encoding="utf-8") as f:
        json.dump(curriculum, f, ensure_ascii=False, indent=2)

    for asset in ("styles.css", "app.js"):
        shutil.copyfile(os.path.join(APP_DIR, asset), os.path.join(OUT_DIR, asset))

    # Empeche Jekyll de filtrer les fichiers sur GitHub Pages.
    open(os.path.join(OUT_DIR, ".nojekyll"), "w").close()

    return curriculum


def summarise(curriculum):
    mods = curriculum["modules"]
    vocab = sum(len(m.get("vocabulary", [])) for m in mods)
    phrases = sum(len(m.get("phrases", [])) for m in mods)
    quiz = sum(len(m.get("quiz", [])) for m in mods)
    pitfalls = sum(len(m.get("pitfalls", [])) for m in mods)
    lines = sum(len((m.get("dialogue") or {}).get("lines", [])) for m in mods)
    print("Application generee dans ./output")
    print("  %d modules" % len(mods))
    print("  %d mots de vocabulaire" % vocab)
    print("  %d expressions" % phrases)
    print("  %d cartes au total" % (vocab + phrases))
    print("  %d questions de quiz" % quiz)
    print("  %d pieges corriges" % pitfalls)
    print("  %d repliques de dialogue" % lines)


def main():
    modules = load_modules()
    if not modules:
        sys.exit("Aucun module trouve dans " + MODULES_DIR)

    errors = validate(modules)
    if errors:
        print("Validation echouee :", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        sys.exit(1)

    summarise(build(modules))


if __name__ == "__main__":
    main()

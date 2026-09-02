/* English@Work — anglais professionnel
   Application statique : aucune donnée ne quitte le navigateur.
   La progression est stockée dans localStorage. */

(function () {
  "use strict";

  var DATA = window.CURRICULUM || { modules: [] };
  var MODULES = DATA.modules || [];
  var STORE_KEY = "eaw.progress.v2";

  /* Intervalles de répétition espacée (Leitner), en jours */
  var BOXES = [0, 1, 3, 7, 21, 45];  // index = boîte 1..5, valeur = jours avant la revision suivante
  var MASTER_BOX = 4;                // à partir de la boîte 4, la carte est "acquise"

  /* ---------------- Persistance ---------------- */

  var defaultState = function () {
    return { cards: {}, quiz: {}, days: [], xp: 0, dir: "fr2en", showFr: true };
  };

  var state = defaultState();

  function load() {
    try {
      var raw = localStorage.getItem(STORE_KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        var base = defaultState();
        for (var k in base) if (parsed[k] !== undefined) base[k] = parsed[k];
        state = base;
      }
    } catch (e) { state = defaultState(); }
  }

  function save() {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) {}
  }

  /* ---------------- Dates ---------------- */

  function today() {
    var d = new Date();
    return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
  }
  function pad(n) { return n < 10 ? "0" + n : "" + n; }
  function addDays(iso, n) {
    var p = iso.split("-");
    var d = new Date(+p[0], +p[1] - 1, +p[2]);
    d.setDate(d.getDate() + n);
    return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
  }
  function daysBetween(a, b) {
    var pa = a.split("-"), pb = b.split("-");
    var da = Date.UTC(+pa[0], +pa[1] - 1, +pa[2]);
    var db = Date.UTC(+pb[0], +pb[1] - 1, +pb[2]);
    return Math.round((db - da) / 86400000);
  }

  function markStudied() {
    var t = today();
    if (state.days.indexOf(t) === -1) { state.days.push(t); state.days.sort(); }
  }

  function streak() {
    if (!state.days.length) return 0;
    var t = today();
    var last = state.days[state.days.length - 1];
    var gap = daysBetween(last, t);
    if (gap > 1) return 0;             // série rompue
    var count = 1, cursor = last;
    for (var i = state.days.length - 2; i >= 0; i--) {
      if (daysBetween(state.days[i], cursor) === 1) { count++; cursor = state.days[i]; }
      else if (daysBetween(state.days[i], cursor) === 0) { continue; }
      else break;
    }
    return count;
  }

  /* ---------------- Cartes ---------------- */

  function cardsOf(mod) {
    var out = [];
    (mod.vocabulary || []).forEach(function (v, i) {
      out.push({
        id: mod.id + "|v|" + i, module: mod.id, kind: "vocab",
        en: v.en, fr: v.fr, note: v.type || "",
        example: v.example || "", exampleFr: v.example_fr || ""
      });
    });
    (mod.phrases || []).forEach(function (p, i) {
      out.push({
        id: mod.id + "|p|" + i, module: mod.id, kind: "phrase",
        en: p.en, fr: p.fr, note: p.context || "", example: "", exampleFr: ""
      });
    });
    return out;
  }

  var ALL_CARDS = [];
  var CARDS_BY_ID = {};
  MODULES.forEach(function (m) {
    cardsOf(m).forEach(function (c) { ALL_CARDS.push(c); CARDS_BY_ID[c.id] = c; });
  });

  function cardState(id) {
    return state.cards[id] || { box: 0, due: null, right: 0, wrong: 0 };
  }

  function isDue(id) {
    var cs = state.cards[id];
    if (!cs) return false;
    return !cs.due || cs.due <= today();
  }

  function dueCards(moduleId) {
    return ALL_CARDS.filter(function (c) {
      return (!moduleId || c.module === moduleId) && state.cards[c.id] && isDue(c.id);
    });
  }

  function newCards(moduleId) {
    return ALL_CARDS.filter(function (c) {
      return (!moduleId || c.module === moduleId) && !state.cards[c.id];
    });
  }

  function gradeCard(id, ok) {
    var cs = cardState(id);
    if (ok) {
      cs.box = Math.min(5, (cs.box || 0) + 1);
      cs.right++;
      state.xp += 1;
      cs.due = addDays(today(), BOXES[cs.box]);
    } else {
      cs.box = 1;
      cs.wrong++;
      cs.due = today();   // une carte ratee revient dans la journee
    }
    state.cards[id] = cs;
    markStudied();
    save();
  }

  function moduleProgress(mod) {
    var cards = cardsOf(mod);
    if (!cards.length) return { mastered: 0, seen: 0, total: 0, pct: 0 };
    var mastered = 0, seen = 0;
    cards.forEach(function (c) {
      var cs = state.cards[c.id];
      if (cs) { seen++; if (cs.box >= MASTER_BOX) mastered++; }
    });
    return { mastered: mastered, seen: seen, total: cards.length, pct: Math.round(100 * mastered / cards.length) };
  }

  /* ---------------- Utilitaires ---------------- */

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function attr(s) { return esc(s).replace(/\n/g, " "); }

  function normalise(s) {
    return String(s || "").toLowerCase().trim()
      .replace(/[’']/g, "'")
      .replace(/[.,!?;:]/g, "")
      .replace(/\s+/g, " ");
  }

  function shuffle(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  function moduleById(id) {
    for (var i = 0; i < MODULES.length; i++) if (MODULES[i].id === id) return MODULES[i];
    return null;
  }

  /* ---------------- Synthèse vocale ---------------- */

  var voice = null;
  function pickVoice() {
    if (!("speechSynthesis" in window)) return;
    var vs = window.speechSynthesis.getVoices() || [];
    voice = vs.filter(function (v) { return v.lang === "en-GB"; })[0]
         || vs.filter(function (v) { return /^en[-_]/.test(v.lang); })[0]
         || null;
  }
  if ("speechSynthesis" in window) {
    pickVoice();
    window.speechSynthesis.onvoiceschanged = pickVoice;
  }

  window.eawSpeak = function (text, ev) {
    if (ev) { ev.stopPropagation(); ev.preventDefault(); }
    if (!("speechSynthesis" in window)) return;
    try {
      window.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(text);
      u.lang = "en-GB";
      u.rate = 0.92;
      if (voice) u.voice = voice;
      window.speechSynthesis.speak(u);
    } catch (e) {}
  };

  function speakBtn(text) {
    return '<button class="speak" title="Écouter" onclick="eawSpeak(' +
      JSON.stringify(text).replace(/"/g, "&quot;") + ', event)">🔊</button>';
  }

  /* ---------------- Chrome de l'application ---------------- */

  function renderChrome() {
    var due = dueCards(null).length;
    var mastered = ALL_CARDS.filter(function (c) { return cardState(c.id).box >= MASTER_BOX; }).length;
    document.getElementById("topstats").innerHTML =
      '<span class="pill">Série <strong>' + streak() + ' j</strong></span>' +
      '<span class="pill">Acquis <strong>' + mastered + "/" + ALL_CARDS.length + '</strong></span>' +
      '<span class="pill">XP <strong>' + state.xp + '</strong></span>' +
      '<span class="pill">À réviser <strong>' + due + '</strong></span>';

    var route = location.hash || "#/";
    var links = [
      ["#/", "Accueil"],
      ["#/review", "Révision du jour" + (due ? " (" + due + ")" : "")],
      ["#/stats", "Progression"],
      ["#/guide", "Guide"]
    ];
    document.getElementById("tabs").innerHTML = links.map(function (l) {
      var active = (l[0] === "#/" ? route === "#/" || route === "" : route.indexOf(l[0]) === 0);
      return '<a href="' + l[0] + '"' + (active ? ' class="active"' : "") + ">" + esc(l[1]) + "</a>";
    }).join("");
  }

  /* ---------------- Vue : accueil ---------------- */

  function viewHome() {
    var due = dueCards(null).length;
    var fresh = newCards(null).length;

    var hero =
      '<div class="hero">' +
        "<div>" +
          "<h2>" + (due ? "Vous avez " + due + " carte" + (due > 1 ? "s" : "") + " à réviser aujourd'hui"
                        : (fresh ? "Aucune révision due — place aux nouvelles cartes"
                                 : "Tout est à jour. Beau travail.")) + "</h2>" +
          "<p>" + (due
            ? "La répétition espacée place chaque expression au bon moment pour la mémoriser durablement."
            : "Choisissez un module ci-dessous pour découvrir " + fresh + " nouvelles cartes.") + "</p>" +
        "</div>" +
        '<a class="btn btn-gold" href="#/review">Démarrer la session →</a>' +
      "</div>";

    var cards = MODULES.map(function (m) {
      var p = moduleProgress(m);
      var d = dueCards(m.id).length;
      return '<a class="mod-card" href="#/m/' + esc(m.id) + '/vocab">' +
        '<div class="mod-head"><div class="mod-icon">' + esc(m.icon || "📘") + "</div>" +
        "<div><div class=\"mod-title\">" + esc(m.title) + "</div>" +
        '<div class="mod-title-en">' + esc(m.title_en) + "</div></div></div>" +
        '<div class="mod-summary">' + esc(m.summary) + "</div>" +
        '<div class="mod-meta">' +
          '<span class="tag">' + esc(m.level) + "</span>" +
          '<span class="tag">' + (m.vocabulary || []).length + " mots</span>" +
          '<span class="tag">' + (m.phrases || []).length + " expressions</span>" +
          '<span class="tag">' + (m.quiz || []).length + " questions</span>" +
          (d ? '<span class="tag" style="border-color:var(--gold);color:var(--gold)">' + d + " à réviser</span>" : "") +
        "</div>" +
        '<div class="bar-label"><span>' + p.mastered + "/" + p.total + " acquis</span><span>" + p.pct + "%</span></div>" +
        '<div class="bar"><i style="width:' + p.pct + '%"></i></div>' +
      "</a>";
    }).join("");

    return hero +
      '<div class="section-label">Les 8 modules</div>' +
      '<div class="grid">' + cards + "</div>";
  }

  /* ---------------- Vue : module ---------------- */

  function viewModule(id, tab) {
    var m = moduleById(id);
    if (!m) return '<div class="empty">Module introuvable.</div>';
    tab = tab || "vocab";

    var tabs = [["vocab", "Vocabulaire"], ["phrases", "Expressions"], ["dialogue", "Dialogue"],
                ["pitfalls", "Pièges"], ["cards", "Flashcards"], ["quiz", "Quiz"]];
    var nav = '<div class="mod-meta" style="margin-bottom:1.2rem">' + tabs.map(function (t) {
      var on = t[0] === tab;
      return '<a class="btn ' + (on ? "btn-primary" : "btn-ghost") + '" href="#/m/' + esc(id) + "/" + t[0] + '">' + t[1] + "</a>";
    }).join("") + "</div>";

    var head =
      '<div class="hero" style="margin-bottom:1.2rem">' +
        '<div><h2>' + esc(m.icon) + " " + esc(m.title) + "</h2>" +
        "<p>" + esc(m.summary) + " · <em>" + esc(m.level) + "</em></p></div>" +
        '<a class="btn btn-ghost" href="#/">← Tous les modules</a>' +
      "</div>";

    var body = "";
    if (tab === "vocab") {
      body = '<div class="panel">' + (m.vocabulary || []).map(function (v) {
        return '<div class="entry"><div class="entry-top">' +
          '<span class="entry-en">' + esc(v.en) + "</span>" + speakBtn(v.en) +
          '<span class="entry-type">' + esc(v.type || "") + "</span>" +
          '<span class="entry-fr">— ' + esc(v.fr) + "</span></div>" +
          (v.example ? '<div class="entry-ex"><b>' + esc(v.example) + "</b> " + speakBtn(v.example) +
                       "<br>" + esc(v.example_fr || "") + "</div>" : "") +
        "</div>";
      }).join("") + "</div>";
    } else if (tab === "phrases") {
      body = '<div class="panel">' + (m.phrases || []).map(function (p) {
        return '<div class="entry">' +
          '<div class="ctx">' + esc(p.context || "") + "</div>" +
          '<div class="entry-top"><span class="entry-en">' + esc(p.en) + "</span>" + speakBtn(p.en) + "</div>" +
          '<div class="entry-fr">' + esc(p.fr) + "</div>" +
        "</div>";
      }).join("") + "</div>";
    } else if (tab === "dialogue") {
      var d = m.dialogue || { lines: [] };
      body = '<div class="panel">' +
        '<div class="section-label" style="margin-top:0">' + esc(d.title || "Dialogue") + "</div>" +
        '<div class="mod-meta">' +
          '<button class="btn btn-ghost" onclick="eawToggleFr()">Masquer / afficher le français</button>' +
          '<button class="btn btn-ghost" onclick="eawPlayDialogue()">▶ Écouter le dialogue</button>' +
        "</div>" +
        (d.lines || []).map(function (l) {
          return '<div class="line"><div class="who">' + esc(l.speaker) + "</div><div>" +
            "<div>" + esc(l.en) + " " + speakBtn(l.en) + "</div>" +
            '<div class="fr' + (state.showFr ? "" : " hidden") + '">' + esc(l.fr) + "</div>" +
          "</div></div>";
        }).join("") + "</div>";
      window.__dialogueLines = (d.lines || []).map(function (l) { return l.en; });
    } else if (tab === "pitfalls") {
      body = '<div class="panel">' +
        '<p class="muted" style="margin-bottom:.8rem">Les erreurs les plus fréquentes des francophones sur ce thème.</p>' +
        (m.pitfalls || []).map(function (p) {
          return '<div class="pitfall">' +
            '<div class="bad">✗ ' + esc(p.wrong) + "</div>" +
            '<div class="good">✓ ' + esc(p.right) + "</div>" +
            '<div class="why">' + esc(p.why) + "</div>" +
          "</div>";
        }).join("") + "</div>";
    } else if (tab === "cards") {
      return head + nav + '<div id="fc"></div>';
    } else if (tab === "quiz") {
      return head + nav + '<div id="quiz"></div>';
    }
    return head + nav + body;
  }

  window.eawToggleFr = function () {
    state.showFr = !state.showFr; save();
    Array.prototype.forEach.call(document.querySelectorAll(".line .fr"), function (el) {
      el.classList.toggle("hidden", !state.showFr);
    });
  };

  window.eawPlayDialogue = function () {
    var lines = window.__dialogueLines || [];
    if (!("speechSynthesis" in window) || !lines.length) return;
    window.speechSynthesis.cancel();
    lines.forEach(function (t) {
      var u = new SpeechSynthesisUtterance(t);
      u.lang = "en-GB"; u.rate = 0.92;
      if (voice) u.voice = voice;
      window.speechSynthesis.speak(u);
    });
  };

  /* ---------------- Flashcards ---------------- */

  var fc = null;

  function startFlashcards(moduleId, container) {
    var queue = dueCards(moduleId);
    var fresh = newCards(moduleId);
    // On complète la session avec des nouvelles cartes, 10 au maximum.
    queue = queue.concat(fresh.slice(0, Math.max(0, 10 - queue.length)));
    if (!queue.length) queue = shuffle(ALL_CARDS.filter(function (c) {
      return !moduleId || c.module === moduleId;
    })).slice(0, 10);

    fc = { queue: shuffle(queue), i: 0, flipped: false, done: 0, right: 0, container: container };
    renderFlashcard();
  }

  function renderFlashcard() {
    var el = document.getElementById(fc.container);
    if (!el) return;
    if (fc.i >= fc.queue.length) {
      el.innerHTML =
        '<div class="q-card center">' +
          '<div class="score-ring">' + fc.right + "/" + fc.done + "</div>" +
          '<p class="muted" style="margin:.5rem 0 1.2rem">Session terminée. Les cartes ratées reviendront dès demain.</p>' +
          '<div class="fc-actions">' +
            '<button class="btn btn-primary" onclick="eawRestartCards()">Nouvelle session</button>' +
            '<a class="btn btn-ghost" href="#/">Retour à l\'accueil</a>' +
          "</div>" +
        "</div>";
      return;
    }

    var c = fc.queue[fc.i];
    var cs = cardState(c.id);
    var front = state.dir === "fr2en" ? c.fr : c.en;
    var back = state.dir === "fr2en" ? c.en : c.fr;
    var readable = state.dir === "fr2en" ? c.en : c.en;

    el.innerHTML =
      '<div class="fc-stage">' +
        '<div class="fc-progress"><span>Carte ' + (fc.i + 1) + " / " + fc.queue.length + "</span>" +
        '<span class="fc-box">Boîte ' + (cs.box || 0) + "/5 · " + (c.kind === "vocab" ? "vocabulaire" : "expression") + "</span></div>" +
        '<div class="flashcard" onclick="eawFlip()">' +
          '<div class="fc-front">' + esc(front) + "</div>" +
          (fc.flipped
            ? '<div class="fc-back">' +
                '<div class="fc-answer">' + esc(back) + " " + speakBtn(readable) + "</div>" +
                (c.note ? '<div class="fc-box" style="margin-top:.4rem">' + esc(c.note) + "</div>" : "") +
                (c.example ? '<div class="fc-example">' + esc(c.example) + "</div>" : "") +
              "</div>"
            : '<div class="fc-hint">Cliquez sur la carte (ou Espace) pour révéler</div>') +
        "</div>" +
        '<div class="fc-actions">' +
          (fc.flipped
            ? '<button class="btn btn-red" onclick="eawGrade(false)">Je ne savais pas</button>' +
              '<button class="btn btn-green" onclick="eawGrade(true)">Je savais ✓</button>'
            : '<button class="btn btn-primary" onclick="eawFlip()">Révéler</button>') +
          '<button class="btn btn-ghost" onclick="eawToggleDir()">' +
            (state.dir === "fr2en" ? "FR → EN" : "EN → FR") + "</button>" +
        "</div>" +
      "</div>";
  }

  window.eawFlip = function () { fc.flipped = !fc.flipped; renderFlashcard(); };
  window.eawToggleDir = function () {
    state.dir = state.dir === "fr2en" ? "en2fr" : "fr2en"; save(); renderFlashcard();
  };
  window.eawGrade = function (ok) {
    var c = fc.queue[fc.i];
    gradeCard(c.id, ok);
    fc.done++; if (ok) fc.right++;
    fc.i++; fc.flipped = false;
    renderFlashcard();
    renderChrome();
  };
  window.eawRestartCards = function () { route(); };

  /* ---------------- Quiz ---------------- */

  var qz = null;

  function startQuiz(mod, container) {
    var questions = shuffle(mod.quiz || []);
    qz = { mod: mod, q: questions, i: 0, right: 0, answered: false, container: container };
    renderQuiz();
  }

  function renderQuiz() {
    var el = document.getElementById(qz.container);
    if (!el) return;

    if (qz.i >= qz.q.length) {
      var pct = qz.q.length ? Math.round(100 * qz.right / qz.q.length) : 0;
      var prev = state.quiz[qz.mod.id] || { best: 0, attempts: 0 };
      prev.attempts++;
      prev.best = Math.max(prev.best, pct);
      state.quiz[qz.mod.id] = prev;
      markStudied(); save(); renderChrome();

      el.innerHTML =
        '<div class="q-card center">' +
          '<div class="score-ring">' + pct + "%</div>" +
          "<p><strong>" + qz.right + " / " + qz.q.length + "</strong> bonnes réponses</p>" +
          '<p class="muted" style="margin:.4rem 0 1.2rem">Meilleur score sur ce module : ' + prev.best + "% · " + prev.attempts + " tentative" + (prev.attempts > 1 ? "s" : "") + "</p>" +
          '<div class="fc-actions">' +
            '<button class="btn btn-primary" onclick="eawRestartQuiz()">Recommencer</button>' +
            '<a class="btn btn-ghost" href="#/m/' + esc(qz.mod.id) + '/cards">Passer aux flashcards</a>' +
          "</div>" +
        "</div>";
      return;
    }

    var q = qz.q[qz.i];
    var html =
      '<div class="q-card">' +
        '<div class="q-num">Question ' + (qz.i + 1) + " / " + qz.q.length + "</div>" +
        '<div class="q-text">' + esc(q.question) + "</div>";

    if (q.type === "mcq") {
      html += q.options.map(function (o, i) {
        return '<button class="q-opt" id="opt' + i + '" onclick="eawAnswerMcq(' + i + ')">' + esc(o) + "</button>";
      }).join("");
    } else {
      html += '<input class="q-input" id="gap" placeholder="Tapez le mot manquant…" autocomplete="off" ' +
              'onkeydown="if(event.key===\'Enter\')eawAnswerGap()">' +
              '<div class="fc-actions" style="justify-content:flex-start;margin-top:.8rem">' +
              '<button class="btn btn-primary" onclick="eawAnswerGap()">Valider</button></div>';
    }

    html += '<div id="qfb"></div></div>';
    el.innerHTML = html;
    var gap = document.getElementById("gap");
    if (gap) gap.focus();
  }

  function quizFeedback(ok, q, given) {
    var solution = q.type === "mcq" ? q.options[q.answer] : q.answer;
    var fb = document.getElementById("qfb");
    fb.innerHTML =
      '<div class="q-feedback ' + (ok ? "ok" : "ko") + '">' +
        "<b>" + (ok ? "Correct" : "Réponse attendue : " + esc(solution)) + "</b>" +
        (!ok && given ? '<div class="muted">Votre réponse : ' + esc(given) + "</div>" : "") +
        esc(q.explanation || "") +
      "</div>" +
      '<div class="fc-actions" style="justify-content:flex-start;margin-top:.8rem">' +
        '<button class="btn btn-primary" onclick="eawNextQ()">' +
        (qz.i + 1 >= qz.q.length ? "Voir le résultat" : "Question suivante →") + "</button></div>";
    if (ok) { qz.right++; state.xp += 2; }
    qz.answered = true;
    markStudied(); save();
  }

  window.eawAnswerMcq = function (i) {
    if (qz.answered) return;
    var q = qz.q[qz.i];
    var ok = i === q.answer;
    Array.prototype.forEach.call(document.querySelectorAll(".q-opt"), function (b, idx) {
      b.disabled = true;
      if (idx === q.answer) b.classList.add("correct");
      else if (idx === i) b.classList.add("wrong");
    });
    quizFeedback(ok, q, null);
  };

  window.eawAnswerGap = function () {
    if (qz.answered) return;
    var q = qz.q[qz.i];
    var input = document.getElementById("gap");
    var given = input ? input.value : "";
    var accepted = [q.answer].concat(q.alternatives || []).map(normalise);
    var ok = accepted.indexOf(normalise(given)) !== -1;
    if (input) { input.disabled = true; input.style.borderColor = ok ? "var(--green)" : "var(--red)"; }
    quizFeedback(ok, q, given);
  };

  window.eawNextQ = function () { qz.i++; qz.answered = false; renderQuiz(); };
  window.eawRestartQuiz = function () { startQuiz(qz.mod, qz.container); };

  /* ---------------- Vue : progression ---------------- */

  function viewStats() {
    var mastered = 0, seen = 0;
    ALL_CARDS.forEach(function (c) {
      var cs = state.cards[c.id];
      if (cs) { seen++; if (cs.box >= MASTER_BOX) mastered++; }
    });
    var quizAvg = 0, quizN = 0;
    for (var k in state.quiz) { quizAvg += state.quiz[k].best; quizN++; }
    quizAvg = quizN ? Math.round(quizAvg / quizN) : 0;

    var boxes = [0, 0, 0, 0, 0, 0];
    ALL_CARDS.forEach(function (c) { var b = cardState(c.id).box || 0; boxes[b]++; });

    var rows = MODULES.map(function (m) {
      var p = moduleProgress(m);
      var q = state.quiz[m.id];
      return "<tr><td>" + esc(m.icon) + " " + esc(m.title) + "</td>" +
        "<td>" + p.seen + "/" + p.total + "</td>" +
        "<td>" + p.mastered + "</td>" +
        '<td style="min-width:120px"><div class="bar"><i style="width:' + p.pct + '%"></i></div></td>' +
        "<td>" + (q ? q.best + "%" : "—") + "</td>" +
        "<td>" + dueCards(m.id).length + "</td></tr>";
    }).join("");

    return '<div class="section-label">Vue d\'ensemble</div>' +
      '<div class="stat-grid">' +
        statBox(streak() + " j", "Série en cours") +
        statBox(state.xp, "Points d'expérience") +
        statBox(mastered + "/" + ALL_CARDS.length, "Cartes acquises") +
        statBox(seen, "Cartes découvertes") +
        statBox(quizAvg + "%", "Moyenne des quiz") +
        statBox(dueCards(null).length, "À réviser aujourd'hui") +
      "</div>" +
      '<div class="section-label">Répartition par boîte de révision</div>' +
      '<div class="panel"><p class="muted" style="margin-bottom:.7rem">Chaque bonne réponse fait monter la carte d\'une boîte, ' +
        'et l\'intervalle avant la prochaine révision s\'allonge : 1, 3, 7, 21 puis 45 jours. ' +
        'Une erreur la ramène en boîte 1 et la carte revient dans la journée.</p>' +
        '<table class="tbl"><tr><th>Boîte</th><th>Cartes</th><th>Prochaine révision</th></tr>' +
        boxes.map(function (n, i) {
          return "<tr><td>" + (i === 0 ? "Jamais vue" : "Boîte " + i) + "</td><td>" + n + "</td><td>" +
            (i === 0 ? "—" : "dans " + BOXES[i] + " jour" + (BOXES[i] > 1 ? "s" : "")) +
            "</td></tr>";
        }).join("") + "</table></div>" +
      '<div class="section-label">Détail par module</div>' +
      '<div class="panel"><table class="tbl">' +
        "<tr><th>Module</th><th>Vues</th><th>Acquises</th><th>Progression</th><th>Quiz</th><th>Dues</th></tr>" +
        rows + "</table></div>" +
      '<div class="section-label">Vos données</div>' +
      '<div class="panel"><p class="muted" style="margin-bottom:.8rem">Toute votre progression est stockée dans ce navigateur uniquement. ' +
        "Exportez-la pour la conserver ou la transférer sur un autre appareil.</p>" +
        '<div class="mod-meta">' +
          '<button class="btn btn-primary" onclick="eawExport()">Exporter ma progression</button>' +
          '<button class="btn btn-ghost" onclick="document.getElementById(\'imp\').click()">Importer un fichier</button>' +
          '<button class="btn btn-ghost" onclick="eawReset()">Tout réinitialiser</button>' +
        "</div>" +
        '<input type="file" id="imp" accept="application/json" style="display:none" onchange="eawImport(this)">' +
      "</div>";
  }

  function statBox(n, label) {
    return '<div class="stat-box"><div class="n">' + esc(n) + '</div><div class="l">' + esc(label) + "</div></div>";
  }

  window.eawExport = function () {
    var blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "english-at-work-progression-" + today() + ".json";
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
  };

  window.eawImport = function (input) {
    var file = input.files && input.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function () {
      try {
        var parsed = JSON.parse(reader.result);
        var base = defaultState();
        for (var k in base) if (parsed[k] !== undefined) base[k] = parsed[k];
        state = base; save(); route(); renderChrome();
        alert("Progression importée.");
      } catch (e) { alert("Fichier illisible."); }
    };
    reader.readAsText(file);
  };

  window.eawReset = function () {
    if (!confirm("Effacer définitivement toute votre progression ?")) return;
    state = defaultState(); save(); route(); renderChrome();
  };

  /* ---------------- Vue : guide ---------------- */

  function viewGuide() {
    return '<div class="section-label">Comment utiliser l\'application</div>' +
      '<div class="panel">' +
        "<div class=\"entry\"><div class=\"entry-top\"><span class=\"entry-en\">1. Lisez le module</span></div>" +
        '<div class="entry-fr">Vocabulaire, expressions, dialogue et pièges classiques des francophones. ' +
        "Chaque phrase anglaise se prononce d'un clic sur 🔊.</div></div>" +
        "<div class=\"entry\"><div class=\"entry-top\"><span class=\"entry-en\">2. Passez aux flashcards</span></div>" +
        '<div class="entry-fr">Le français s\'affiche, vous produisez l\'anglais — c\'est l\'effort de rappel qui fait mémoriser. ' +
        "Le bouton FR → EN inverse le sens si vous préférez commencer en reconnaissance.</div></div>" +
        "<div class=\"entry\"><div class=\"entry-top\"><span class=\"entry-en\">3. Revenez chaque jour</span></div>" +
        '<div class="entry-fr">« Révision du jour » regroupe les cartes de tous les modules arrivées à échéance. ' +
        "Dix à quinze minutes par jour valent mieux que deux heures le samedi.</div></div>" +
        "<div class=\"entry\"><div class=\"entry-top\"><span class=\"entry-en\">4. Testez-vous</span></div>" +
        '<div class="entry-fr">Le quiz de chaque module mêle QCM et textes à trous, avec une explication systématique — ' +
        "y compris quand vous avez juste.</div></div>" +
      "</div>" +
      '<div class="section-label">Contenu</div>' +
      '<div class="panel"><p class="muted">' +
        MODULES.length + " modules · " +
        ALL_CARDS.length + " cartes · " +
        MODULES.reduce(function (n, m) { return n + (m.quiz || []).length; }, 0) + " questions de quiz · " +
        MODULES.reduce(function (n, m) { return n + (m.pitfalls || []).length; }, 0) + " pièges corrigés · " +
        MODULES.reduce(function (n, m) { return n + ((m.dialogue || {}).lines || []).length; }, 0) + " répliques de dialogue." +
      "</p></div>" +
      '<div class="section-label">Ajouter votre propre contenu</div>' +
      '<div class="panel"><p class="muted">Chaque module est un fichier JSON dans <code>data/modules/</code>. ' +
        "Ajoutez-y un fichier, relancez <code>python scripts/build.py</code>, et le module apparaît dans l'application. " +
        "Le format est décrit dans le README.</p></div>";
  }

  /* ---------------- Routage ---------------- */

  function route() {
    var hash = location.hash || "#/";
    var parts = hash.replace(/^#\/?/, "").split("/").filter(Boolean);
    var app = document.getElementById("app");

    if (!parts.length) {
      app.innerHTML = viewHome();
    } else if (parts[0] === "m") {
      var id = decodeURIComponent(parts[1] || "");
      var tab = parts[2] || "vocab";
      app.innerHTML = viewModule(id, tab);
      var mod = moduleById(id);
      if (mod && tab === "cards") startFlashcards(id, "fc");
      if (mod && tab === "quiz") startQuiz(mod, "quiz");
    } else if (parts[0] === "review") {
      var due = dueCards(null).length, fresh = newCards(null).length;
      app.innerHTML =
        '<div class="hero" style="margin-bottom:1.2rem"><div>' +
          "<h2>Révision du jour</h2><p>" + due + " carte" + (due > 1 ? "s" : "") + " due" + (due > 1 ? "s" : "") +
          " · " + fresh + " nouvelle" + (fresh > 1 ? "s" : "") + " disponible" + (fresh > 1 ? "s" : "") + "</p>" +
        '</div><a class="btn btn-ghost" href="#/">← Accueil</a></div><div id="fc"></div>';
      startFlashcards(null, "fc");
    } else if (parts[0] === "stats") {
      app.innerHTML = viewStats();
    } else if (parts[0] === "guide") {
      app.innerHTML = viewGuide();
    } else {
      app.innerHTML = '<div class="empty">Page introuvable. <a href="#/">Retour à l\'accueil</a></div>';
    }

    renderChrome();
    window.scrollTo(0, 0);
  }

  document.addEventListener("keydown", function (e) {
    if (!fc || !document.getElementById(fc.container)) return;
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea") return;
    if (e.code === "Space") { e.preventDefault(); window.eawFlip(); }
    else if (fc.flipped && (e.key === "1" || e.key === "ArrowLeft")) window.eawGrade(false);
    else if (fc.flipped && (e.key === "2" || e.key === "ArrowRight")) window.eawGrade(true);
  });

  window.addEventListener("hashchange", route);

  load();
  route();
})();

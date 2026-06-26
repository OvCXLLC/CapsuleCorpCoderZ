/* ───────────────────────────────────────────────────────────────────────────
   KAKAROT'S LEGACY  –  Game Engine
   State machine: Home → Origin → Prologue Choice → Bridge Choice →
                  [Alignment Derived] → Crisis Choice → Ending → Aftermath
   ─────────────────────────────────────────────────────────────────────────── */

(function () {
  "use strict";

  // ── Game data injected by Flask template ─────────────────────────────────
  /** @type {{ stories, events, crisis_events, endings, aftermaths }} */
  const GD = window.GAME_DATA;

  // ── Stage constants ───────────────────────────────────────────────────────
  const STAGES = ["Origin", "Prologue", "Bridge", "Alignment", "Crisis", "Ending", "End"];

  const ALIGNMENT_INFO = {
    saiyan: {
      name: "Path of Saiyan Duty",
      desc: "Your choices trend toward strategic discipline and raw Saiyan programming. The mission comes first.",
    },
    feral: {
      name: "Path of Feral Bloodlust",
      desc: "Primal violence dominates your nature. The Great Ape stirs beneath every decision.",
    },
    tyrant: {
      name: "Path of Calculated Tyranny",
      desc: "Control over people, resources, and technology defines your approach. You play the long game.",
    },
  };

  // ── State ─────────────────────────────────────────────────────────────────
  let state = {
    story: null,          // story object
    stage: "home",        // home | intro | origin | prologue | bridge | alignment | crisis | ending | aftermath
    stageIndex: 0,        // numeric index for progress rail (0–6)
    eventQueue: [],       // ordered event IDs for this story
    queuePos: 0,          // current position in eventQueue
    stats: { ki: 0, malice: 0, infamy: 0, health: 0 },
    alignment: null,      // saiyan | feral | tyrant
    endingPath: null,     // saiyan | feral | tyrant
    timeline: [],         // [{ year, text, isChoice }]
  };

  // ── DOM refs ──────────────────────────────────────────────────────────────
  const $ = (id) => document.getElementById(id);
  const screenHome = $("screen-home");
  const screenGame = $("screen-game");
  const timelineList = $("timeline-list");
  const scenePanel = $("scene-panel");
  const statsKiFill   = $("fill-ki");
  const statsMaFill   = $("fill-malice");
  const statsInFill   = $("fill-infamy");
  const statsHpFill   = $("fill-health");
  const statsKiVal    = $("val-ki");
  const statsMaVal    = $("val-malice");
  const statsInVal    = $("val-infamy");
  const statsHpVal    = $("val-health");
  const progressRail  = $("progress-rail");
  const headerBrand   = $("header-brand");

  // ── Screen transitions ────────────────────────────────────────────────────
  function showScreen(name) {
    screenHome.classList.toggle("active", name === "home");
    screenGame.classList.toggle("active", name === "game");
  }

  // ── Build the story card grid on home ────────────────────────────────────
  function buildHomeScreen() {
    const grid = $("story-grid");
    grid.innerHTML = "";
    GD.stories.forEach((story) => {
      const card = document.createElement("div");
      card.className = "story-card";
      card.style.setProperty("--story-color", story.color);

      const ss = story.starting_stats;
      card.innerHTML = `
        <div class="story-card-icon">${story.icon}</div>
        <div class="story-card-title">${story.title}</div>
        <div class="story-card-subtitle">${story.subtitle}</div>
        <div class="story-card-tagline">${story.tagline}</div>
        <div class="story-card-desc">${story.description}</div>
        <div class="story-card-stats">
          <span class="stat-pip ki">Ki ${ss.ki}</span>
          <span class="stat-pip malice">Malice ${ss.malice}</span>
          <span class="stat-pip infamy">Infamy ${ss.infamy}</span>
          <span class="stat-pip health">Health ${ss.health}</span>
        </div>
      `;
      card.addEventListener("click", () => startStory(story.id));
      grid.appendChild(card);
    });
  }

  // ── Start a story ─────────────────────────────────────────────────────────
  function startStory(storyId) {
    const story = GD.stories.find((s) => s.id === storyId);
    if (!story) return;

    state.story      = story;
    state.stats      = { ...story.starting_stats };
    state.alignment  = null;
    state.endingPath = null;
    state.timeline   = [];
    state.stageIndex = 0;
    state.eventQueue = [...story.sequence]; // e.g. ['intro','mf_origin','mf_prologue','mf_bridge']
    state.queuePos   = 0;

    headerBrand.innerHTML = `DRAGON BALL <span>LEGACY</span>`;
    showScreen("game");
    renderStats();
    renderRail();
    renderCurrentEvent();
  }

  // ── Return to home screen ────────────────────────────────────────────────
  function goHome() {
    showScreen("home");
  }

  // ── Derive current event object from queue ────────────────────────────────
  function getCurrentEvent() {
    const id = state.eventQueue[state.queuePos];
    if (!id) return null;

    if (id === "__alignment__") return { __special: "alignment" };
    if (id === "__crisis__")    return GD.crisis_events[state.alignment];
    if (id === "__ending__")    return GD.endings[state.endingPath];
    if (id === "__aftermath__") return GD.aftermaths[state.endingPath];

    return GD.events[id] || null;
  }

  // ── Advance through the event queue ──────────────────────────────────────
  function advance() {
    const ev = getCurrentEvent();
    if (ev) {
      addTimelineEntry(ev.year || "", ev.title || "", false);
    }
    state.queuePos++;
    renderCurrentEvent();
  }

  // ── Handle a choice selection ─────────────────────────────────────────────
  function selectChoice(choice) {
    // Apply stat changes
    if (choice.stat_changes) {
      Object.entries(choice.stat_changes).forEach(([k, v]) => {
        state.stats[k] = Math.min(100, (state.stats[k] || 0) + v);
      });
    }
    renderStats();

    // Bridge choice → set alignment and inject crisis into queue
    if (choice.alignment) {
      state.alignment = choice.alignment;
      state.stageIndex = 3;
      // Inject alignment reveal + crisis after current position
      state.eventQueue.splice(state.queuePos + 1, 0, "__alignment__", "__crisis__");
    }

    // Crisis choice → set ending path and inject ending + aftermath
    if (choice.path && state.alignment && !choice.alignment) {
      state.endingPath = choice.path;
      state.stageIndex = 5;
      state.eventQueue.splice(state.queuePos + 1, 0, "__ending__", "__aftermath__");
    }

    addTimelineEntry(
      getCurrentEvent()?.year || "",
      choice.text,
      true
    );
    state.queuePos++;
    renderStats();
    renderRail();
    renderCurrentEvent();
  }

  // ── Render the current event into the scene panel ────────────────────────
  function renderCurrentEvent() {
    const ev = getCurrentEvent();

    if (!ev) {
      // Queue exhausted — should not normally happen
      return;
    }

    // ── Special: alignment reveal ─────────────────────────────────────────
    if (ev.__special === "alignment") {
      state.stageIndex = 3;
      renderAlignmentReveal();
      renderRail();
      return;
    }

    // ── Special: ending & aftermath ───────────────────────────────────────
    const curId = state.eventQueue[state.queuePos];
    if (curId === "__ending__") {
      state.stageIndex = 5;
      renderEndingCard(ev);
      renderRail();
      scrollSceneToTop();
      return;
    }
    if (curId === "__aftermath__") {
      state.stageIndex = 6;
      renderAftermathCard(ev);
      renderRail();
      scrollSceneToTop();
      return;
    }

    // ── Normal events — derive stageIndex from event type ─────────────────
    if (ev.type === "choice")  state.stageIndex = 1;   // prologue choice
    if (ev.type === "bridge")  state.stageIndex = 2;   // bridge choice
    if (ev.type === "crisis")  state.stageIndex = 4;   // crisis choice
    // 'narration' events stay at stageIndex 0 (Origin intro)

    renderSceneCard(ev);
    renderRail();
    scrollSceneToTop();
  }

  // ── Render a standard narration / choice scene ───────────────────────────
  function renderSceneCard(ev) {
    const pathBadge = state.alignment
      ? `<span class="badge-path ${state.alignment}">${ALIGNMENT_INFO[state.alignment]?.name || state.alignment}</span>`
      : "";

    let choicesHTML = "";
    if (ev.type === "choice" || ev.type === "bridge" || ev.type === "crisis") {
      const btns = (ev.choices || []).map((c) => {
        const tags = Object.entries(c.stat_changes || {})
          .map(([k, v]) => `<span class="stat-change-tag ${k}">+${k[0].toUpperCase()}${k.slice(1)} ${v}</span>`)
          .join("");
        return `
          <button class="choice-btn path-${c.path || c.alignment || ""}"
                  data-choice-id="${c.id}">
            <div class="choice-btn-title">${c.text}</div>
            <div class="choice-btn-detail">${c.detail}</div>
            <div class="choice-stat-tags">${tags}</div>
          </button>`;
      }).join("");
      choicesHTML = `<div class="choices-container">${btns}</div>`;
    } else {
      const label = ev.continue_label || "Continue →";
      choicesHTML = `<button class="continue-btn" id="continue-btn">${label}</button>`;
    }

    scenePanel.innerHTML = `
      <div class="scene-inner">
        <div class="scene-badges">
          <span class="badge-year">${ev.year || ""}</span>
          ${pathBadge}
        </div>
        <div class="scene-title">${ev.title || ""}</div>
        ${buildImagePlaceholder(ev.image_id)}
        <div class="scene-text">${ev.text || ""}</div>
        ${choicesHTML}
      </div>`;

    // Attach choice listeners
    scenePanel.querySelectorAll(".choice-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const cid = btn.dataset.choiceId;
        const ev2 = getCurrentEvent();
        const choice = (ev2.choices || []).find((c) => c.id === cid);
        if (choice) selectChoice(choice);
      });
    });

    // Attach continue listener
    const contBtn = $("continue-btn");
    if (contBtn) contBtn.addEventListener("click", advance);
  }

  // ── Render alignment reveal ───────────────────────────────────────────────
  function renderAlignmentReveal() {
    const al = state.alignment;
    const info = ALIGNMENT_INFO[al] || {};
    scenePanel.innerHTML = `
      <div class="scene-inner">
        <div class="scene-badges">
          <span class="badge-year">${getCurrentAlignmentYear()}</span>
        </div>
        <div class="scene-title">Alignment Locked In</div>
        <div class="alignment-card ${al}">
          <div class="align-label">Your path has been determined</div>
          <div class="align-name">${info.name || al}</div>
          <div class="align-desc">${info.desc || ""}</div>
        </div>
        <div class="scene-text" style="text-align:center;color:var(--text-dim);font-size:13px;">
          Raditz is coming. The next decision defines your fate.
        </div>
        <button class="continue-btn" id="continue-btn">Face the Crisis →</button>
      </div>`;
    $("continue-btn").addEventListener("click", advance);
  }

  function getCurrentAlignmentYear() {
    // Try to get the year from the bridge event
    const bridgeId = state.story?.sequence?.at(-1);
    return (bridgeId && GD.events[bridgeId]?.year) || "Age 757";
  }

  // ── Render ending card ────────────────────────────────────────────────────
  function renderEndingCard(ev) {
    const path = state.endingPath;
    scenePanel.innerHTML = `
      <div class="scene-inner">
        <div class="scene-badges">
          <span class="badge-year">${ev.year || "Age 762"}</span>
          <span class="badge-path ${path}">${ev.type_label || ""}</span>
        </div>
        <div class="scene-title">${ev.title}</div>
        ${buildImagePlaceholder(ev.image_id)}
        <div class="ending-card ${path}">
          <div class="ending-type-label">${ev.type_label || ""}</div>
          <div class="ending-title">${ev.title}</div>
          <div class="ending-text">${ev.text}</div>
          <div class="ending-outcome"><strong>Outcome:</strong> ${ev.outcome}</div>
        </div>
        <button class="continue-btn" id="continue-btn">Epilogue →</button>
      </div>`;
    $("continue-btn").addEventListener("click", advance);
  }

  // ── Render aftermath card ─────────────────────────────────────────────────
  function renderAftermathCard(ev) {
    const path = state.endingPath;
    scenePanel.innerHTML = `
      <div class="scene-inner">
        <div class="scene-badges">
          <span class="badge-year">${ev.year || ""}</span>
        </div>
        <div class="scene-title">Epilogue</div>
        ${buildImagePlaceholder(ev.image_id)}
        <div class="aftermath-card">
          <div class="aftermath-header">
            <span class="aftermath-title">${ev.title}</span>
            <span class="aftermath-year">${ev.year}</span>
          </div>
          <div class="aftermath-text">${ev.text}</div>
          <span class="aftermath-status ${path}">${ev.status || ""}</span>
        </div>
        ${buildFinalStats()}
        <button class="play-again-btn" id="play-again-btn">↻ Play Again</button>
      </div>`;
    $("play-again-btn").addEventListener("click", goHome);
  }

  // ── Build final stats summary ─────────────────────────────────────────────
  function buildFinalStats() {
    const s = state.stats;
    return `
      <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:18px 20px;margin-bottom:20px;">
        <div style="font-size:10px;text-transform:uppercase;letter-spacing:2px;color:var(--text-dim);margin-bottom:14px;">Final Stats</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
          ${buildStatRow("Ki", s.ki, "ki")}
          ${buildStatRow("Malice", s.malice, "malice")}
          ${buildStatRow("Infamy", s.infamy, "infamy")}
          ${buildStatRow("Health", s.health, "health")}
        </div>
      </div>`;
  }

  function buildStatRow(label, val, cls) {
    return `
      <div>
        <div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--text-dim);margin-bottom:4px;">${label}</div>
        <div style="height:6px;background:rgba(255,255,255,0.07);border-radius:99px;overflow:hidden;margin-bottom:2px;">
          <div style="height:100%;width:${val}%;background:var(--${cls});border-radius:99px;"></div>
        </div>
        <div style="font-size:11px;font-weight:700;color:var(--text-muted);">${val}</div>
      </div>`;
  }

  // ── Build image placeholder HTML ──────────────────────────────────────────
  function buildImagePlaceholder(imageId) {
    // Try loading an actual image; falls back to styled placeholder
    return `
      <div class="image-placeholder" id="img-wrap-${imageId}">
        <img src="/static/images/${imageId}.png"
             alt="${imageId}"
             style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;border-radius:var(--radius);"
             onerror="this.style.display='none';document.getElementById('img-wrap-${imageId}').classList.add('ph-active')">
        <span class="ph-icon">🎨</span>
        <span class="ph-label">Scene Image</span>
        <span class="ph-id">${imageId}</span>
      </div>`;
  }

  // ── Update stats header bars ──────────────────────────────────────────────
  function renderStats() {
    const s = state.stats;
    statsKiFill.style.width  = s.ki     + "%";
    statsMaFill.style.width  = s.malice + "%";
    statsInFill.style.width  = s.infamy + "%";
    statsHpFill.style.width  = s.health + "%";
    statsKiVal.textContent   = s.ki;
    statsMaVal.textContent   = s.malice;
    statsInVal.textContent   = s.infamy;
    statsHpVal.textContent   = s.health;
  }

  // ── Progress rail ─────────────────────────────────────────────────────────
  function renderRail() {
    const current = state.stageIndex;
    progressRail.innerHTML = STAGES.map((lbl, i) => {
      const isDone    = i < current;
      const isCurrent = i === current;
      const dotClass  = isDone ? "done" : isCurrent ? "current" : "";
      const conn = i < STAGES.length - 1
        ? `<div class="rail-connector ${isDone ? "done" : ""}"></div>`
        : "";
      return `
        <div class="rail-node ${dotClass}">
          <div class="rail-dot ${dotClass}">${isDone ? "✓" : i + 1}</div>
          <div class="rail-node-lbl">${lbl}</div>
        </div>${conn}`;
    }).join("");
  }

  // ── Timeline sidebar ──────────────────────────────────────────────────────
  function addTimelineEntry(year, text, isChoice) {
    state.timeline.push({ year, text, isChoice });
    renderTimeline();
  }

  function renderTimeline() {
    timelineList.innerHTML = state.timeline.map((entry, i) => {
      const divider = i > 0
        ? `<div class="tl-divider"></div>`
        : "";
      return `
        ${divider}
        <div class="timeline-entry">
          <div class="tl-year">${entry.year}</div>
          <div class="tl-text ${entry.isChoice ? "choice-entry" : ""}">${entry.text}</div>
        </div>`;
    }).join("");
    timelineList.scrollTop = timelineList.scrollHeight;
  }

  // ── Scroll scene back to top on each new event ───────────────────────────
  function scrollSceneToTop() {
    scenePanel.scrollTop = 0;
  }

  // ── Wire up home back button ──────────────────────────────────────────────
  $("back-to-home").addEventListener("click", goHome);

  // ── Init ──────────────────────────────────────────────────────────────────
  buildHomeScreen();
  showScreen("home");
  renderRail();
})();

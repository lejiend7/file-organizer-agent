// Talks only to window.pywebview.api - see organizer/ui/api.py for the
// full contract. No organizing logic lives in this file; it only renders
// state and forwards user actions.

let currentReviewItemId = null;

function api() {
  return window.pywebview && window.pywebview.api;
}

function showView(name) {
  document.querySelectorAll("section[id^='view-']").forEach((el) => el.classList.add("hidden"));
  document.getElementById(`view-${name}`).classList.remove("hidden");
  document.querySelectorAll(".nav-item").forEach((el) => el.classList.toggle("active", el.dataset.view === name));
}

document.querySelectorAll(".nav-item").forEach((el) => {
  el.addEventListener("click", () => {
    showView(el.dataset.view);
    if (el.dataset.view === "review") loadReviewQueue();
    if (el.dataset.view === "rules") loadRules();
  });
});

async function refreshState() {
  if (!api()) return;
  const state = await api().get_state();

  document.getElementById("source-path").textContent = state.source_folder || "Not selected";
  document.getElementById("dest-path").textContent = state.destination_folder || "Not selected";
  document.getElementById("dry-run-toggle").checked = state.dry_run;
  document.getElementById("ai-toggle").checked = state.ai_enabled;
  document.getElementById("ai-toggle-settings").checked = state.ai_enabled;

  document.getElementById("monitor-toggle").textContent = state.monitoring ? "Stop monitoring" : "Start monitoring";
  document.getElementById("stat-status").textContent = state.monitoring ? "Monitoring" : "Idle";
  document.getElementById("stat-review").textContent = state.review_count;
  document.getElementById("stat-moves").textContent = state.recent_activity.length;

  const badge = document.getElementById("review-badge");
  if (state.review_count > 0) {
    badge.textContent = state.review_count;
    badge.classList.remove("hidden");
  } else {
    badge.classList.add("hidden");
  }

  const activityList = document.getElementById("activity-list");
  if (state.recent_activity.length === 0) {
    activityList.innerHTML = '<div class="row-sub">Nothing organized yet.</div>';
  } else {
    activityList.innerHTML = state.recent_activity
      .slice()
      .reverse()
      .map((a) => `<div class="row-sub">${a.path.split("/").pop()} - ${a.outcome}</div>`)
      .join("");
  }
}

document.getElementById("select-source").addEventListener("click", async () => {
  const res = await api().select_source_folder();
  if (res.ok) {
    document.getElementById("dashboard-warning").classList.toggle("hidden", res.warning !== "destination_inside_source");
    refreshState();
  }
});

document.getElementById("select-dest").addEventListener("click", async () => {
  const res = await api().select_destination_folder();
  if (res.ok) {
    document.getElementById("dashboard-warning").classList.toggle("hidden", res.warning !== "destination_inside_source");
    refreshState();
  }
});

document.getElementById("monitor-toggle").addEventListener("click", async () => {
  const state = await api().get_state();
  if (state.monitoring) {
    await api().stop_monitoring();
  } else {
    const res = await api().start_monitoring();
    if (!res.ok) alert(res.error);
  }
  refreshState();
});

document.getElementById("dry-run-toggle").addEventListener("change", (e) => api().set_dry_run(e.target.checked));

function wireAiToggle(el) {
  el.addEventListener("change", async (e) => {
    await api().set_ai_enabled(e.target.checked);
    refreshState();
  });
}
wireAiToggle(document.getElementById("ai-toggle"));
wireAiToggle(document.getElementById("ai-toggle-settings"));

document.getElementById("launch-login-toggle").addEventListener("change", (e) => api().set_launch_at_login(e.target.checked));
document.getElementById("remove-credentials").addEventListener("click", async () => {
  await api().remove_ai_credentials();
  alert("Stored AI credentials removed.");
});

// ----- review queue -----

async function loadReviewQueue() {
  const items = await api().get_review_queue();
  const container = document.getElementById("review-list");
  if (items.length === 0) {
    container.innerHTML = '<div class="row-sub">No files awaiting review.</div>';
    return;
  }
  container.innerHTML = items
    .map((item) => {
      const rec = item.recommendation;
      const confPct = Math.round(rec.confidence * 100);
      const subClass = item.low_confidence ? "row-sub low" : "row-sub";
      const subText = item.low_confidence
        ? "Low confidence - staying in need_your_review"
        : `-> ${rec.relative_destination}/${rec.suggested_filename}`;
      return `
        <div class="list-row" data-id="${item.id}">
          <div style="flex:1; min-width:0;">
            <div class="row-title">${item.original_path.split("/").pop()}</div>
            <div class="${subClass}">${subText}</div>
          </div>
          <span class="badge" style="background:var(--success-bg); color:var(--success);">${confPct}%</span>
        </div>`;
    })
    .join("");

  container.querySelectorAll(".list-row").forEach((row) => {
    row.addEventListener("click", () => openReviewModal(row.dataset.id, items.find((i) => i.id === row.dataset.id)));
  });
}

function openReviewModal(itemId, item) {
  currentReviewItemId = itemId;
  const rec = item.recommendation;
  document.getElementById("review-modal-confidence").textContent = `confidence ${Math.round(rec.confidence * 100)}%`;
  document.getElementById("review-modal-current").textContent = item.original_path;
  document.getElementById("review-modal-filename").value = rec.suggested_filename;
  document.getElementById("review-modal-destination").value = rec.relative_destination;
  document.getElementById("review-modal-reason").textContent = rec.reason;
  document.getElementById("review-modal-privacy").textContent = item.content_left_device
    ? "This file's content left this device for this suggestion."
    : "Content stayed on this device for this suggestion.";
  updateReviewPreview();
  document.getElementById("review-modal").classList.remove("hidden");
}

function updateReviewPreview() {
  const filename = document.getElementById("review-modal-filename").value;
  const dest = document.getElementById("review-modal-destination").value;
  document.getElementById("review-modal-preview").textContent = `Will appear at: ${dest}/${filename}`;
}
document.getElementById("review-modal-filename").addEventListener("input", updateReviewPreview);
document.getElementById("review-modal-destination").addEventListener("input", updateReviewPreview);

document.getElementById("review-modal-skip").addEventListener("click", async () => {
  await api().skip_review(currentReviewItemId);
  document.getElementById("review-modal").classList.add("hidden");
  loadReviewQueue();
  refreshState();
});

document.getElementById("review-modal-confirm").addEventListener("click", async () => {
  const filename = document.getElementById("review-modal-filename").value;
  const destination = document.getElementById("review-modal-destination").value;
  const res = await api().approve_review(currentReviewItemId, filename, destination);
  if (!res.ok) {
    alert(`Could not complete transfer: ${res.error}`);
    return;
  }
  document.getElementById("review-modal").classList.add("hidden");
  loadReviewQueue();
  refreshState();
});

// ----- extension rules -----

async function loadRules() {
  const categories = await api().get_extension_rules();
  const container = document.getElementById("rules-list");
  container.innerHTML = Object.entries(categories)
    .map(
      ([name, exts]) => `
      <div class="card" data-category="${name}">
        <div style="font-weight:500; margin-bottom:8px;">${name}</div>
        <div class="tags">
          ${exts.map((ext) => `<span class="tag">${ext} <a href="#" class="remove-tag" data-ext="${ext}">x</a></span>`).join("")}
        </div>
        <input type="text" class="add-ext" placeholder="add extension, e.g. .webp" style="margin-top:8px; width:200px;" />
      </div>`
    )
    .join("");

  container.querySelectorAll(".remove-tag").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      const card = e.target.closest(".card");
      const cat = card.dataset.category;
      categories[cat] = categories[cat].filter((x) => x !== e.target.dataset.ext);
      await api().update_extension_rules(categories);
      loadRules();
    });
  });

  container.querySelectorAll(".add-ext").forEach((input) => {
    input.addEventListener("keydown", async (e) => {
      if (e.key !== "Enter" || !e.target.value.trim()) return;
      const card = e.target.closest(".card");
      const cat = card.dataset.category;
      let ext = e.target.value.trim().toLowerCase();
      if (!ext.startsWith(".")) ext = "." + ext;
      if (!categories[cat].includes(ext)) categories[cat].push(ext);
      await api().update_extension_rules(categories);
      loadRules();
    });
  });
}

// ----- onboarding -----

async function maybeShowOnboarding() {
  const state = await api().get_state();
  if (!state.source_folder || !state.destination_folder) {
    document.getElementById("onboarding-overlay").classList.remove("hidden");
  }
}
document.getElementById("onboarding-start").addEventListener("click", () => {
  document.getElementById("onboarding-overlay").classList.add("hidden");
});

// ----- boot -----

window.addEventListener("pywebviewready", () => {
  refreshState();
  maybeShowOnboarding();
  setInterval(refreshState, 3000);
});

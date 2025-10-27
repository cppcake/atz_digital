console.log("navigation.js loaded");

let visitedStatements = new Set();

// update UI with current therapy state
async function updateTherapyState() {
  const res = await fetch("/therapy/state");
  if (!res.ok) return;
  const state = await res.json();
  document.getElementById("topic_name").textContent =
    (state.topic?.content || "");
  const statements = state.topic?.statements || [];
  const idx = state.current_statement || 0;
  let statementText = "";
  let posInfo = "";
  if (statements[idx]) {
    statementText = statements[idx].content || "";
    posInfo = ` (${idx + 1}/${statements.length})`;
  }
  document.getElementById("current_statement").textContent =
    statementText;

  document.getElementById("counter").textContent =
    posInfo;

  // Mark current as visited
  visitedStatements.add(idx);

  // Render statement list
  renderStatementList(statements, idx);
}

function renderStatementList(statements, currentIdx) {
  const ul = document.getElementById("statement-list");
  ul.innerHTML = "";
  statements.forEach((stmt, i) => {
    const li = document.createElement("li");
    li.textContent = stmt.content || "";
    li.style.cursor = "pointer";
    li.className = "statement-list-item";
    // Color logic
    if (i === currentIdx) {
      li.style.background = "var(--accent_1-color)";
      li.style.color = "#fff";
    } else if (visitedStatements.has(i)) {
      li.style.background = "var(--accent_2-color)";
      li.style.color = "var(--font_1-color)";
    }
    li.onclick = () => jumpToStatement(i);
    ul.appendChild(li);
  });
}

async function jumpToStatement(idx) {
  const res = await fetch(`/therapy/jump/${idx}`, { method: "PUT" });
  if (res.ok) {
    await updateTherapyState();
  }
}

// forward therapy and then fetch for current state, see what current statement to display
window.forwardTherapy = async function () {
  const res = await fetch("/therapy/forward", { method: "PUT" });
  if (res.ok) updateTherapyState();
};

// backward therapy and then fetch for current state, see what current statement to display
window.backwardTherapy = async function () {
  const res = await fetch("/therapy/backward", { method: "PUT" });
  if (res.ok) updateTherapyState();
};

// --- Notes logic ---
let notesSaveTimeout = null;
const NOTES_SAVE_DEBOUNCE = 500; // ms

async function loadNotesFromBackend() {
  try {
    const res = await fetch("/therapy/state");
    if (!res.ok) return;
    const state = await res.json();
    if (state && typeof state.notes === "string") {
      const textarea = document.getElementById("therapy-notes");
      if (textarea) textarea.value = state.notes;
    } else {
      // fallback: try to fetch from /therapy/notes endpoint if needed
    }
  } catch (e) {
    // ignore
  }
}

async function saveNotesToBackend() {
  const textarea = document.getElementById("therapy-notes");
  if (!textarea) return;
  const notes = textarea.value;
  try {
    await fetch("/therapy/notes/", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes })
    });
  } catch (e) {
    // ignore
  }
}

function setupNotesAutosave() {
  const textarea = document.getElementById("therapy-notes");
  if (!textarea) return;
  textarea.addEventListener("input", function () {
    if (notesSaveTimeout) clearTimeout(notesSaveTimeout);
    notesSaveTimeout = setTimeout(saveNotesToBackend, NOTES_SAVE_DEBOUNCE);
  });
}

// end therapy
window.endTherapy = async function () {
  // Save notes before ending therapy
  await saveNotesToBackend();
  if (!confirm(`Denken Sie daran, alle Fernbedienungen auszuschalten!`)) {
    return;
  }
  gotoUri("/therapy/notes");
};

// on load, fetch state
document.addEventListener("DOMContentLoaded", async function () {
  await updateTherapyState();
  await loadNotesFromBackend();
  setupNotesAutosave();
});

// Listen for websocket changes to update navigation live
if ("WebSocket" in window) {
  try {
    const ws = new WebSocket(
      (location.protocol === "https:" ? "wss://" : "ws://") +
        location.host +
        "/subscribe_change"
    );
    ws.onmessage = function () {
      updateTherapyState();
    };
  } catch (e) {}
}
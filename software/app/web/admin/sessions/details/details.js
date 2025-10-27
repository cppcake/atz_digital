console.log("details.js loaded");

window.deleteSession = async function(filename) {
    if (!confirm("Möchten Sie diese Sitzung wirklich löschen?")) return;
    try {
        const resp = await fetch(`/sessions/${filename}`, { method: "DELETE" });
        const result = await resp.json();
        if (resp.ok && result.status === "success") {
            window.gotoUri("/sessions");
        } else {
            alert("Fehler beim Löschen: " + (result.detail || "Unbekannter Fehler"));
        }
    } catch (e) {
        alert("Netzwerkfehler beim Löschen.");
    }
};

window.addEventListener("DOMContentLoaded", function () {
    fillTopic(window.session_dict);
    renderStatementCharts(window.session_dict);

    // Attach delete handler
    const btn = document.getElementById("btn_delete_session");
    if (btn && window.session_dict && window.session_dict.date && window.session_dict.date.timestamp) {
        btn.onclick = function() {
            window.deleteSession(window.session_dict.date.timestamp);
        };
    }

    // Populate notes area from session_dict (client-side)
    const notesEl = document.getElementById("session-notes");
    if (notesEl) {
        const notes = (window.session_dict && window.session_dict.notes) ? window.session_dict.notes : null;
        if (notes && typeof notes === "string" && notes.trim() !== "") {
            notesEl.textContent = notes;
            notesEl.style.color = "";
        } else {
            notesEl.textContent = "Keine Notizen";
            notesEl.style.color = "#666";
        }
    }
});

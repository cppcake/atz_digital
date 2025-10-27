console.log("notes.js loaded")

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

    // Attach save & continue handler to the button
    const btnSave = document.getElementById("btn_save_and_continue");
    if (btnSave) {
        btnSave.onclick = async function () {
            await window.saveNotesAndContinue();
        };
    }
});

// Save notes to server and navigate to survey
window.saveNotesAndContinue = async function () {
    try {
        const textarea = document.getElementById("therapy-notes");
        const notes = textarea ? textarea.value : "";
        const resp = await fetch("/therapy/notes/", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ notes: notes })
        });
        if (resp.ok) {
            // Redirect to ~survey~ thanks page
            window.location.href = "/therapy/thanks";
        } else {
            let err = "Unbekannter Fehler";
            try { const j = await resp.json(); err = j.detail || JSON.stringify(j); } catch {}
            alert("Fehler beim Speichern der Notizen: " + err);
        }
    } catch (e) {
        alert("Netzwerkfehler beim Speichern der Notizen.");
    }
};
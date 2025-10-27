console.log("overview.js loaded");

document.addEventListener("DOMContentLoaded", async () => {
    const response = await fetch("/therapy/state/phase");
    const phase = await response.json();

    if (phase != 0) {
        const countSelect = document.getElementById("session_rejoin").style.display = "";
    }
});
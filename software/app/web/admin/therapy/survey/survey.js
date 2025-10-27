console.log("study.js loaded")

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('.study').forEach(function(studyDiv) {
        studyDiv.querySelectorAll('input[type="checkbox"]').forEach(function(checkbox) {
            checkbox.addEventListener('change', function() {
                if (this.checked) {
                    studyDiv.querySelectorAll('input[type="checkbox"]').forEach(function(cb) {
                        if (cb !== checkbox) cb.checked = false;
                    });
                }
            });
        });
    });
});

window.saveStudy = function() {
    const requiredDiv = document.getElementById("required");
    const surveyBlocks = requiredDiv.querySelectorAll('.survey');
    let answers = [];
    let allChecked = true;

    surveyBlocks.forEach(function(block) {
        const checked = block.querySelector('input[type="checkbox"]:checked');
        if (!checked) {
            allChecked = false;
        }
        answers.push(checked ? checked.parentElement.textContent.trim() : null);
    });

    if (!allChecked) {
        alert("Bitte beantworten Sie alle Pflichtfragen.");
        return;
    }

    const optionalText = document.querySelector('textarea.studytext')?.value || "";

    const payload = {
        answers: answers,
        feedback: optionalText
    };

    fetch("/therapy/survey", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    }).then(res => {
        if (res.ok) {
            window.gotoUri("/therapy/thanks");
        } else {
            alert("Fehler beim Senden der Umfrage.");
        }
    });
}
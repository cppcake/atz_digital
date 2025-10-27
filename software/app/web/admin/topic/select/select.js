console.log("select.js loaded");

function fillTopic(versionObj) {
    // Set topic name
    document.getElementById("topic_name").textContent =
        versionObj.content || "";

    // Fill statements
    const olStatements = document.getElementById("ol_statements");
    olStatements.innerHTML = "";
    (versionObj.statements || []).forEach((st) => {
        const li = document.createElement("li");
        li.textContent = st.content;
        li.className = "span1";
        olStatements.appendChild(li);
    });

    // Fill answers, icons, and images, hide unused ones
    const colors = ["green", "yellow", "red", "blue", "purple"];
    const olAnswers = document.getElementById("ol_answers");
    const answerLis = olAnswers.querySelectorAll("li");
    colors.forEach((color, idx) => {
        const span = document.getElementById(color);
        const ans = (versionObj.answers || []).find((a) => a.color === color);

        // Set answer text
        if (span) {
            span.textContent = ans ? ans.content : "";
        }

        // Remove any previous image next to the color-square
        if (answerLis[idx]) {
            // Remove any previous img element
            const prevImg = answerLis[idx].querySelector("img.answer-icon-img");
            if (prevImg) prevImg.remove();

            // Insert image if icon is present
            if (ans && ans.icon) {
                const img = document.createElement("img");
                img.src = `/web/imgs/answers/${ans.icon}.png`;
                img.alt = ans.icon;
                img.className = "answer-icon-img";
                img.style.height = "32px";
                img.style.width = "32px";
                img.style.objectFit = "contain"; // keep aspect ratio
                img.style.aspectRatio = "1 / 1"; // keep aspect ratio
                img.style.marginLeft = "8px";
                // Insert after color-square
                const colorSquare = answerLis[idx].querySelector(".color-square");
                if (colorSquare) {
                    colorSquare.insertAdjacentElement("afterend", img);
                }
            }
        }

        // Hide or show the <li> depending on answer presence
        if (answerLis[idx]) {
            if (!ans || !ans.content) {
                answerLis[idx].style.display = "none";
            } else {
                answerLis[idx].style.display = "";
            }
        }
    });

    // Update edit button link
    document.getElementById("edit_btn").onclick = function () {
        window.gotoUri(`/topic/edit/${versionObj.id}`);
    };

    // Update start button action
    document.getElementById("start_btn").onclick = function () {
        // This will be overridden below to use gotoUri with version
    };

    // Remove any previous click handler to avoid stacking
    const startBtn = document.getElementById("start_btn");
    startBtn.onclick = null;
}

window.ignoreTopic = function () {
  // Show confirmation dialog with topic name
  const topicName = document.getElementById("topic_name").textContent || "";
  if (!confirm(`Möchten Sie das Thema "${topicName}" wirklich löschen?`)) {
    return;
  }
  // Send POST request
  console.log("hey");
  fetch(`/topic/ignore/${topic_id}`, {
    method: "PUT"
  })
    .then(async (resp) => {
      if (!resp.ok) {
        const data = await resp.json();
        alert("Fehler beim Löschen des Themas: " + (data.detail || resp.status));
      } else {
        gotoUri("/topic/overview");
      }
    })
    .catch((err) => {
      alert("Netzwerkfehler: " + err);
    });
}

window.addEventListener("DOMContentLoaded", function () {
    const versions = window.topic_versions || [];
    const select = document.getElementById("versions");
    select.innerHTML = "";

    // Populate select options (latest first)
    versions.forEach((ver, idx) => {
        const opt = document.createElement("option");
        opt.value = idx;
        opt.textContent = `Version ${ver.version + 1}`;
        select.appendChild(opt);
    });

    // Default to latest version (index 0)
    if (versions.length > 0) {
        select.selectedIndex = 0;
        fillTopic(versions[0]);
    }

    // Set start_btn to use gotoUri with selected version
    const startBtn = document.getElementById("start_btn");
    startBtn.onclick = function () {
        const idx = select.selectedIndex;
        const versionObj = versions[idx];
        if (versionObj) {
            const topicId = versionObj.id;
            const topicVersion = versionObj.version;
            window.gotoUri(`/therapy/prepare/${topicId}/${topicVersion}`);
        }
    };

    // On change, update display and re-assign start_btn handler
    select.addEventListener("change", function () {
        const idx = parseInt(this.value, 10);
        fillTopic(versions[idx]);
        // Re-assign start_btn handler to always use the currently selected version
        startBtn.onclick = function () {
            const idx = select.selectedIndex;
            const versionObj = versions[idx];
            if (versionObj) {
                const topicId = versionObj.id;
                const topicVersion = versionObj.version;
                window.gotoUri(`/therapy/prepare/${topicId}/${topicVersion}`);
            }
        };
    });
});

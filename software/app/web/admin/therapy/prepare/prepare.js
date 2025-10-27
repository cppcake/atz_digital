console.log("prepare.js loaded");

window.addPerson = function () {
  const ul = document.getElementById("player_list");
  const countSelect = document.getElementById("count");
  const targetCount = parseInt(countSelect.value, 10) || 1;
  let currentCount = ul.querySelectorAll("li").length;

  // Remove extra persons if needed
  while (currentCount > targetCount) {
    const lastLi = ul.querySelector("li:last-child");
    if (lastLi) {
      ul.removeChild(lastLi);
    }
    currentCount--;
  }

  // Add or update entries to match the selected count
  for (let idx = 0; idx < targetCount; idx++) {
    let li = ul.querySelector(`li[data-idx="${idx}"]`);
    if (!li) {
      li = document.createElement("li");
      li.setAttribute("data-idx", idx);
      const flexdiv = document.createElement("div");
      flexdiv.className = "flexdiv";

      // Name input
      const input = document.createElement("input");
      input.type = "text";
      input.placeholder = "Name";

      // Icon select button
      const iconBtn = document.createElement("button");
      iconBtn.type = "button";
      iconBtn.className = "btn_small";
      iconBtn.innerHTML = '<i class="fa fa-image"></i>';
      iconBtn.onclick = function () {
        // Use /imgs/players for listing, /image/upload_players for upload
        window.openImageMenu(this, "/imgs/players", "/image/upload_players");
      };

      // Remote ID select (0–5, shown as 1–6)
      const idSelect = document.createElement("select");
      idSelect.className = "options";
      idSelect.style = "min-width: 40px; text-align: center; display: inline-block;";
      for (let i = 0; i < 6; i++) {
        const opt = document.createElement("option");
        opt.value = i;
        opt.textContent = (i + 1).toString();
        idSelect.appendChild(opt);
      }
      idSelect.value = idx; // default: assign unique id

      flexdiv.appendChild(input);
      flexdiv.appendChild(iconBtn);
      flexdiv.appendChild(idSelect);
      li.appendChild(flexdiv);
      ul.appendChild(li);
    }
  }
};

document.addEventListener("DOMContentLoaded", function () {
  const countSelect = document.getElementById("count");
  if (countSelect) {
    countSelect.addEventListener("change", function () {
      window.addPerson();
    });
    window.addPerson();
  }
});

window.startTherapy = function (topic_id, topic_version) {
  let players = [];

  const player_list = document.getElementById("player_list");
  const lis = player_list.querySelectorAll("li");
  let usedIds = new Set();
  let duplicate = false;

  // Get required number of persons from count select
  const countSelect = document.getElementById("count");
  const requiredCount = parseInt(countSelect.value, 10) || 1;

  for (let li of lis) {
    const input = li.querySelector('input[type="text"]');
    const iconBtn = li.querySelector('button.btn_small');
    const idSelect = li.querySelector("select");
    const name = input ? input.value.trim() : "";
    const icon = iconBtn && iconBtn.dataset.selected ? iconBtn.dataset.selected : "";
    const id = idSelect ? idSelect.value : "";

    if (name && icon && id !== "") {
      if (usedIds.has(id)) {
        duplicate = true;
      }
      usedIds.add(id);
      players.push({
        id: Number(id),
        name: name,
        icon: icon,
        answers: [],
      });
    }
  }

  if (players.length !== requiredCount) {
    alert(
      `Bitte gib für alle ${requiredCount} Personen einen Namen, ein Bild und eine Fernbedienungsnummer an.`
    );
    return;
  }

  if (duplicate) {
    alert("Jede Fernbedienungsnummer darf nur einmal vergeben werden.");
    return;
  }

  // Build JSON
  const delayedAnswers = document.getElementById("delayed_answers")?.checked || false;
  const payload = {
    players: players,
    delayed_answers: delayedAnswers,
  };

  console.log(payload);
  // Send POST request
  fetch(`/therapy/start/${topic_id}/${topic_version}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
    .then(async (resp) => {
      if (!resp.ok) {
        const data = await resp.json();
        alert("Fehler: " + (data.detail || resp.status));
      } else {
        gotoUri("/therapy/navigation");
      }
    })
    .catch((err) => {
      alert("Netzwerkfehler: " + err);
    });
};

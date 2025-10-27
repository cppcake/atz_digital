console.log("edit.js loaded");

window.fillAnswersFromTopic = async function(topic_uuid, version) {
  // Fetch topic details from backend
  try {
    const res = await fetch(`/topic/details/${topic_uuid}/${version}`);
    const topic = await res.json();
    const answers = topic.answers || [];
    const colorMap = {};
    answers.forEach(a => {
      colorMap[a.color] = a;
    });
    const colors = ["green", "yellow", "red", "blue", "purple"];
    colors.forEach(color => {
      const input = document.getElementById(color);
      const btn_img = document.getElementById(`img_select_${color}`);
      if (input && colorMap[color]) {
        input.value = colorMap[color].content || "";
      }
      if (btn_img && colorMap[color] && colorMap[color].icon) {
        btn_img.dataset.selected = colorMap[color].icon;
        btn_img.innerHTML = `<img src="/web/imgs/answers/${colorMap[color].icon}.png" alt="${colorMap[color].icon}" class="image-menu-img-thumb">`;
      }
    });
  } catch (e) {
    // fallback: do nothing
  }
};

window.updateTopic = function (id) {
  /*
    This method extracts the content of admin/topic/edit.html and tries to
    make a JSON like this one:
    
    {
        "content": "Climate change",
        "statements": ["Climate change is manmade", "Climate change is bad", "Animals are suffering because of climate change"],
        "answers": {
            "green": ["Yes", "IMAGE_NAME"],
            "yellow": ["Maybe", "IMAGE_NAME"],
            "red": ["No", "IMAGE_NAME"]
        }
    }

    If thats is not possible, for example because:
    - the content-input field is empty
    - one of the statement-input fields is empty
    - there are less than two answers given

    It alerts the user and gives the reason.

    If the JSON was made successfully, it sends a POST request to
    /create_topic with the JSON to create a new topic in the database.
    */

  // Get topic name
  const topicInput = document.getElementById("topic_name");
  const topicName = topicInput.value.trim();
  if (!topicName) {
    alert("Bitte gib einen Themenname ein.");
    return;
  }

  // Get statements
  const ol = document.getElementById("ol_statements");
  const statementInputs = ol.querySelectorAll('input[type="text"]');
  const statements = [];
  for (let input of statementInputs) {
    const val = input.value.trim();
    if (!val) {
      alert("Bitte fülle alle Aussagen aus.");
      return;
    }
    statements.push(val);
  }

  // Get answers
  const colors = ["green", "yellow", "red", "blue", "purple"];
  const answers = {};
  let answerCount = 0;
  for (let color of colors) {
    const input = document.getElementById(color);
    const btn_img = document.getElementById(`img_select_${color}`);
    if (input && input.value.trim()) {
      let imgName = (btn_img && btn_img.dataset.selected !== undefined)
        ? btn_img.dataset.selected
        : "missing";
      answers[color] = [input.value.trim(), imgName];
      answerCount++;
    }
  }
  if (answerCount < 2) {
    alert("Bitte gib mindestens zwei Antworten an.");
    return;
  }

  // Build JSON
  const payload = {
    content: topicName,
    statements: statements,
    answers: answers,
  };

  // Send POST request
  const url = "/topic/edit/" + id;
  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
    .then(async (resp) => {
      if (!resp.ok) {
        const data = await resp.json();
        alert("Fehler beim Erstellen: " + (data.detail || resp.status));
      } else {
        gotoUri(`/topic/select/${id}`);
      }
    })
    .catch((err) => {
      alert("Netzwerkfehler: " + err);
    });
};

// Fill answers and icons on page load
window.addEventListener("DOMContentLoaded", function () {
  // ...existing code for colorIds and button setup...
  // Get topic id and version from injected variables or fallback to URL
  const topicId =
    window.topicId ||
    (typeof window.topic_id !== "undefined" ? window.topic_id : window.location.pathname.split("/").pop());
  const version =
    typeof window.topic_version !== "undefined"
      ? window.topic_version
      : (window.topicVersion || 0);

  window.fillAnswersFromTopic(topicId, version);
});

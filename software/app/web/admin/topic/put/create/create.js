console.log("create.js loaded");



pressed = false
window.createTopic = function () {
  /*
    This method extracts the content of topic_create.html and tries to
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

  
  if(pressed == false)
  {
    pressed = true
    // Build JSON
    const payload = {
      content: topicName,
      statements: statements,
      answers: answers,
    };
  
    // Send POST request
    fetch("/topic/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(async (resp) => {
        if (!resp.ok) {
          const data = await resp.json();
          pressed = false
          alert("Fehler beim Erstellen: " + (data.detail || resp.status));
        } else {
          gotoUri("/topic/overview");
          pressed = false
        }
      })
      .catch((err) => {
        alert("Netzwerkfehler: " + err);
        pressed = false
      });
  }
};

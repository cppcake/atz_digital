import {new_player, new_answer, player_to_answer, player_unanswer, clear, set_topic} from "./visualizer.js"


const visualizer = {
  rejk: null,
  afeef: null,
  green: null,
  yellow: null,
  purple: null,
  red: null,
  set_topic: set_topic,
  answer: player_to_answer,
  unanswer: player_unanswer,
  add_player: new_player,
  add_answer: new_answer,
};




// Start the visualizer once the page has fully loaded
document.addEventListener("DOMContentLoaded", () => debug_ui());


async function debug_ui()
{
  const sessionInfoElem = document.getElementById("session-info");
  if (sessionInfoElem) sessionInfoElem.style.display = "none";

  visualizer.green = new_answer("Grün", "green", "Richtig");
  visualizer.yellow = new_answer("Gelb", "yellow", "Unsicher");
  visualizer.red = new_answer("Rot", "red", "Falsch");

  visualizer.rejk = new_player("Rejk", 0);
  visualizer.afeef = new_player("A", 1);
  visualizer.afeef = new_player("Af", 2);
  visualizer.afeef = new_player("Afe", 3);
  visualizer.afeef = new_player("Afee", 4);

  window.visualizer = visualizer;
}

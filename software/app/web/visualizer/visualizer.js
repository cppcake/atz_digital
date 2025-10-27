export {
  player_to_answer_by_id,
  player_unanswer_by_id,
  new_player, new_answer,
  player_to_answer,
  player_unanswer,
  clear,
  set_topic,
  set_statement,
  set_qrcode,
  hide_session_info,
  set_wifi_ssid,
  set_wifi_password,
  mark_player_finished,
  show_counter,
  set_counter,
};


const player_map = new Map();
const player_clones = new Map();
const player_answers = new Set();
const answer_map = new Map();

let players;
let answers;


document.addEventListener("DOMContentLoaded", function(){
  players = document.getElementById("players");
  answers = document.getElementById("answers");

  // For Debugging
  // purple = new_answer("This is the purple Question", "purple");
  // green = new_answer("This is the green Question", "green");
  // yellow = new_answer("This is the yellow Question", "yellow");
  // red = new_answer("This is the red Question", "red");

  // // For Debugging
  // rejk = new_player("Rejk", 0);
  // afeef = new_player("Afeef", 1);
});


function new_answer(text, color, icon_path)
{
  const template = document.getElementById("answer-template");
  const instance = template.content.cloneNode(true);


  const me = 
  {
    me: instance.children[0],
    droparea: instance.querySelector(".answer-droparea"),
    text: instance.querySelector(".answer-text"),
    icon: instance.querySelector(".answer-image"),
    // added badge reference
    badge: instance.querySelector(".answer-badge")
  };
  
  answers.appendChild(instance);

  me.text.innerHTML = text;
  me.me.classList.add(color);
  // Scale image to fit within 48x48px, keep aspect ratio and resolution
  me.icon.innerHTML = `<img src="/web/imgs/answers/${icon_path}.png" style="max-width:156px;max-height:156px;width:auto;height:auto;display:block;">`;

  // Set the answer-badge image according to the color (override template default)
  if (me.badge) {
    me.badge.setAttribute('src', `/web/imgs/buttons/${color}.svg`);
  }

  // ToDo, set "src="/web/imgs/buttons/{color}.svg"" for <img class="answer-badge" src="/web/imgs/buttons/green.svg" />

  answer_map.set(color, me);

  return me;
}


function new_player(name, id, icon_path)
{
  const template = document.getElementById("player-template");
  const instance = template.content.cloneNode(true);

  const me = {
    me: instance.children[0],
    name: instance.querySelector(".player-name"),
    icon: instance.querySelector(".player-icon"),
    id: id,
    icon_path: icon_path
  };

  player_map.set(id, me);
  
  players.appendChild(instance);
  me.name.innerHTML = name;
  me.icon.innerHTML = `<img src="/web/imgs/players/${icon_path}.png" style="width:48px;height:48px;">`;
  return me;
}


function player_to_answer(player, answer)
{
  if (player_answers.has(player.id))
  {
    const player_clone = player_clones.get(player.id);
    move_element(player_clone, player_clone.getBoundingClientRect(), answer.droparea, 450);
    return;
  }
  
  const player_clone = player.me.cloneNode(true);
  player.me.classList.add("slot");
  setTimeout(() => player_clone.classList.add("collapse"), 50);

  player_answers.add(player.id);
  player_clones.set(player.id, player_clone);
  
  move_element(player_clone, player.me.getBoundingClientRect(), answer.droparea, 450);
}


function player_unanswer(player)
{
  player.me.classList.remove("slot");
  player_answers.delete(player.id);

  let clone = player_clones.get(player.id);
  
  if (clone)
  {
    clone.classList.remove("collapse");
    move_element(player.me, clone.getBoundingClientRect(), player.me, 450);
    clone.remove();
    player_clones.delete(player.id);
  }  
}


function move_element(from, start, to, duration, append = true)
{
  const { left: x0, top: y0 } = start;
  if (from != to && append) to.appendChild(from);
  let { left: x1, top: y1 } = append ? from.getBoundingClientRect() : to.getBoundingClientRect();

  const dx = x0 - x1;
  const dy = y0 - y1;
  
  if (dx === 0 && dy === 0) {
    return;
  }

  const transformFrom = `translate3d(${dx}px, ${dy}px, 0)`;
  const transformTo = `translate3d(0, 0, 0)`;

  const animation = from.animate([
    { transform: transformFrom },
    { transform: transformTo },
  ], {
    duration: duration,
    easing: 'ease',
  });
}


function player_exists(player_id)
{
  return player_map.has(player_id);
}


function answer_exists(answer_color)
{
  return answer_map.has(answer_color);
}


function clear()
{
  players.innerHTML = "";
  answers.innerHTML = "";

  player_map.clear()
  player_clones.clear()
  player_answers.clear()
  answer_map.clear()
}


function player_to_answer_by_id(player_id, answer_color)
{
  if (!player_exists(player_id) || !answer_exists(answer_color))
  {
    console.warn("the player_id " + player_id + " or answer_color " + answer_color + " does not exist");
    return;
  }
  
  const player = player_map.get(player_id);
  const answer = answer_map.get(answer_color);
  
  player_to_answer(player, answer);
}


function player_unanswer_by_id(player_id)
{
  if (!player_exists(player_id))
  {
    console.warn("the player_id " + player_id + " does not exist");
    return;
  }
  
  player_unanswer(player_map.get(player_id))
}


function set_topic(title)
{
  document.getElementById("topic-title").innerText = title;
}


function set_statement(title)
{
  document.getElementById("topic-statement").innerText = title;
}


function set_qrcode(src)
{
  document.getElementById("session-info").style.display = "flex";
  document.getElementById("qrcode").setAttribute("src", src);
}


function show_counter(visible)
{
  const outer = document.getElementById("outer-counter-box");
  if (!outer) return;
  outer.style.display = visible ? "flex" : "none";
}

function set_counter(a, b)
{
  const el = document.getElementById("counter");
  if (!el) return;
  el.innerText = `${a} / ${b}`;
}


function hide_session_info()
{
  document.getElementById("session-info").style.display = "none";
}


function set_wifi_ssid(ssid)
{
  document.getElementById("wifi-ssid").innerHTML = ssid;
}

function set_wifi_password(pass)
{
  document.getElementById("wifi-pass").innerHTML = pass;
}

/**
 * Mark the player's DOM element as having answered (delayed mode).
 * @param {number} player_id
 */
function mark_player_finished(player_id) {
  const playerObj = player_map.get(player_id);
  if (playerObj && playerObj.me) {
    playerObj.me.classList.remove('box');
    playerObj.me.classList.add('box_2');
  }
}


console.log("put.js loaded");

window.addStatement = function () {
  const ol = document.getElementById("ol_statements");
  const li = document.createElement("li");

  // Create flexdiv
  const flexdiv = document.createElement("div");
  flexdiv.className = "flexdiv";

  // Create input
  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = `Neue Aussage`;
  // No value for new statement

  // Create delete button
  const delete_button = document.createElement("button");
  delete_button.type = "button";
  delete_button.className = "btn_delete_small";
  delete_button.innerHTML = '<i class="fa fa-trash"></i>';
  delete_button.onclick = function () {
    window.removeItem(this);
  };

  // Assemble
  flexdiv.appendChild(input);
  flexdiv.appendChild(delete_button);
  li.appendChild(flexdiv);
  ol.appendChild(li);
};

// Attach to all color buttons on page load
window.addEventListener("DOMContentLoaded", function () {
  const colorIds = [
    "img_select_green",
    "img_select_yellow",
    "img_select_red",
    "img_select_blue",
    "img_select_purple"
  ];
  colorIds.forEach(function (id) {
    const btn = document.getElementById(id);
    if (btn) {
      btn.onclick = function (e) {
        window.openImageMenu(this);
      };
    }
  });
});
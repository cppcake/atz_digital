// This file has been generated using GitHub CoPilot with GPT-4.1

console.log("utils.js loaded");

window.gotoUri = function (uri) {
  window.location.href = uri;
};

window.gotoUriWAlert = function (uri, context) {
  if (!confirm(context + ` wirklich abbrechen?`)) {
    return;
  }
  window.location.href = uri;
};

window.removeItem = function (btn) {
  const li = btn.closest("li");

  const ul = btn.closest("ul");
  if (ul && li && li.parentElement === ul) {
    if (ul.children.length <= 1) {
      alert("Mindenstens ein Eintrag ist notwendig.");
      return;
    }
    ul.removeChild(li);
  }

  const ol = btn.closest("ol");
  if (ol && li && li.parentElement === ol) {
    if (ol.children.length <= 1) {
      alert("Mindenstens ein Eintrag ist notwendig.");
      return;
    }
    ol.removeChild(li);
  }
};

// Helper to open image selection menu, now with optional location parameter
window.openImageMenu = async function (btn, location = "/imgs/answers", uploadUrl = "/image/upload") {
  // Remove any existing menu
  const oldMenu = document.getElementById("image-menu-popup");
  if (oldMenu) oldMenu.remove();

  // Create menu container
  const menu = document.createElement("div");
  menu.id = "image-menu-popup";
  menu.className = "image-menu-popup";

  // Position menu near button
  const rect = btn.getBoundingClientRect();
  menu.style.left = `${rect.left + window.scrollX}px`;
  menu.style.top = `${rect.bottom + window.scrollY + 4}px`;

  // Show loading indicator
  const loadingDiv = document.createElement("div");
  loadingDiv.id = "image-menu-loading";
  loadingDiv.className = "image-menu-loading";
  loadingDiv.innerHTML = `<span class="fa fa-spinner fa-spin"></span> Bilder werden geladen...`;
  menu.appendChild(loadingDiv);

  // --- Add image upload input ---
  const uploadDiv = document.createElement("div");
  uploadDiv.className = "image-upload-div";

  const uploadLabel = document.createElement("label");
  uploadLabel.textContent = "Bild hochladen:";
  uploadLabel.htmlFor = "imageInput";
  uploadLabel.className = "image-upload-label";

  const uploadInput = document.createElement("input");
  uploadInput.type = "file";
  uploadInput.id = "imageInput";
  uploadInput.accept = "image/*";
  uploadInput.multiple = true;

  uploadDiv.appendChild(uploadLabel);
  uploadDiv.appendChild(uploadInput);
  menu.appendChild(uploadDiv);

  // Add close button
  const closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.innerHTML = "&times;";
  closeBtn.className = "image-menu-close-btn";
  closeBtn.onclick = () => menu.remove();
  menu.appendChild(closeBtn);

  document.body.appendChild(menu);

  // Remove menu if clicked outside
  setTimeout(() => {
    function handler(e) {
      if (!menu.contains(e.target)) {
        menu.remove();
        document.removeEventListener("mousedown", handler);
      }
    }
    document.addEventListener("mousedown", handler);
  }, 10);

  // Fetch images from server and render
  let images = {};
  try {
    const res = await fetch(location);
    images = await res.json();
  } catch (e) {
    loadingDiv.innerHTML = "Fehler beim Laden der Bilder.";
    return;
  }

  // Remove loading indicator
  loadingDiv.remove();

  // Sort image names
  const sortedEntries = Object.entries(images).sort((a, b) => a[0].localeCompare(b[0]));

  // Add images to menu
  sortedEntries.forEach(([name, b64]) => {
    const imgBtn = document.createElement("button");
    imgBtn.type = "button";
    imgBtn.className = "image-menu-img-btn";
    imgBtn.title = name;
    imgBtn.onmouseover = function () {
      imgBtn.classList.add("image-menu-img-btn-hover");
    };
    imgBtn.onmouseout = function () {
      imgBtn.classList.remove("image-menu-img-btn-hover");
    };
    imgBtn.onclick = function () {
      btn.dataset.selected = name;
      btn.innerHTML = `<img src="data:image/png;base64,${b64}" alt="${name}" class="image-menu-img-thumb">`;
      menu.remove();
    };
    const img = document.createElement("img");
    img.src = `data:image/png;base64,${b64}`;
    img.alt = name;
    img.className = "image-menu-img-thumb";
    imgBtn.appendChild(img);
    menu.appendChild(imgBtn);
  });

  // --- Hook image upload input ---
  uploadInput.addEventListener('change', function(event) {
    const files = event.target.files;
    let base64Images = [];
    let readPromises = [];
    for (let i = 0; i < files.length; i++) {
      if (files[i]) {
        readPromises.push(new Promise((resolve) => {
          const reader = new FileReader();
          reader.onload = function(e) {
            const img = new Image();
            img.onload = function() {
              let maxDim = 480;
              let w = img.width;
              let h = img.height;
              let scale = Math.min(maxDim / w, maxDim / h, 1.0);
              let nw = Math.round(w * scale);
              let nh = Math.round(h * scale);

              const canvas = document.createElement('canvas');
              canvas.width = nw;
              canvas.height = nh;
              const ctx = canvas.getContext('2d');
              ctx.drawImage(img, 0, 0, nw, nh);

              let mimeType = files[i].type || 'image/png';
              let compressedDataUrl;
              if (mimeType === 'image/jpeg' || mimeType === 'image/jpg') {
                compressedDataUrl = canvas.toDataURL(mimeType, 0.92);
              } else {
                compressedDataUrl = canvas.toDataURL(mimeType);
              }
              base64Images.push(compressedDataUrl.split(',')[1]);
              resolve();
            };
            img.src = e.target.result;
          };
          reader.readAsDataURL(files[i]);
        }));
      }
    }
    Promise.all(readPromises).then(async () => {
      // Show loading indicator while uploading
      const uploadLoading = document.createElement("div");
      uploadLoading.id = "image-upload-loading";
      uploadLoading.className = "image-upload-loading";
      uploadLoading.innerHTML = `<span class="fa fa-spinner fa-spin"></span> Bilder werden hochgeladen...`;
      menu.appendChild(uploadLoading);

      // Upload images
      if (base64Images.length === 0) {
        alert("No images selected!");
        uploadLoading.remove();
        return;
      }
      // Use the correct uploadUrl
      const response = await fetch(uploadUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ images: base64Images })
      });
      const result = await response.json();

      // Close menu after upload
      menu.remove();
      // Reopen menu to refresh images
      window.openImageMenu(btn, location, uploadUrl);
    });
  });
};

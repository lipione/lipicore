const statuses = [
  "Starting secure desktop session",
  "Connecting to LipiCore",
  "Preparing workspace"
];

let index = 0;
const statusElement = document.getElementById("status");

window.setInterval(() => {
  index = (index + 1) % statuses.length;
  statusElement.textContent = statuses[index];
}, 1200);

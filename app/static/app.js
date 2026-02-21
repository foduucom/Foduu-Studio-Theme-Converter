const form = document.querySelector("form");
const statusBox = document.getElementById("statusBox");
const button = document.getElementById("convertBtn");

// ✅ WebSocket connection
let ws;

function connectWS() {
  ws = new WebSocket(`ws://${window.location.host}/ws`);

  ws.onopen = () => {
    console.log("✅ WebSocket connected");
  };

  ws.onmessage = (event) => {
    statusBox.style.display = "block";
    statusBox.innerText = event.data;
  };

  ws.onclose = () => {
    console.log("❌ WebSocket closed. Reconnecting...");
    setTimeout(connectWS, 1000);
  };

  ws.onerror = () => {
    ws.close();
  };
}

// Start connection
connectWS();

form.addEventListener("submit", async function (e) {
  e.preventDefault();
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    connectWS();
  }
  
  statusBox.style.display = "block";
  statusBox.innerText = "Starting conversion...";

  button.disabled = true;
  button.innerText = "Converting please wait...";

  const formData = new FormData(form);

  try {
    const response = await fetch("/generate", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      statusBox.innerText = "❌ Conversion failed";
      // ✅ Show Retry
      button.disabled = false;
      button.innerText = "Retry";

      return;
    }

    // ZIP ready
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);

    // ✅ Replace status with download button only
    statusBox.innerHTML = `
      <div>✅ Conversion Complete!</div>
      <a href="${url}" download="converted-theme.zip" class="download-btn">
        Download Converted ZIP
      </a>
    `;

  } catch (err) {
    statusBox.innerText = "❌ Server error";
    // ✅ Show Retry
    button.disabled = false;
    button.innerText = "Retry";
  }

  button.disabled = false;
  button.innerText = "Convert Theme";
});

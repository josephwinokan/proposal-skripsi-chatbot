function toggleChat() {
  const chat = document.getElementById("chat-container");
  chat.style.display = chat.style.display === "flex" ? "none" : "flex";

  // kalau baru dibuka, kasih salam awal
  if (chat.style.display === "flex" && document.getElementById("chat-box").children.length === 0) {
    appendMessage("bot", "Halo 👋, saya Chatbot Akademik UM. Pilih salah satu pertanyaan atau ketik pesan di bawah.");
  }
}

function appendMessage(sender, message) {
  const chatBox = document.getElementById("chat-box");
  const bubble = document.createElement("div");

  bubble.className = sender === "user" ? "chat-bubble user-bubble" : "chat-bubble bot-bubble";
  bubble.innerText = message;

  chatBox.appendChild(bubble);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function sendMessage() {
  const input = document.getElementById("user-input");
  const message = input.value.trim();
  if (!message) return;

  appendMessage("user", message);
  input.value = "";

  fetch("/get", {
    method: "POST",
    body: JSON.stringify({ msg: message }),
    headers: { "Content-Type": "application/json" },
  })
    .then(res => res.json())
    .then(data => {
      appendMessage("bot", data.response);
    });
}

// fungsi quick reply
function sendQuick(msg) {
  appendMessage("user", msg);
  fetch("/get", {
    method: "POST",
    body: JSON.stringify({ msg }),
    headers: { "Content-Type": "application/json" },
  })
    .then(res => res.json())
    .then(data => {
      appendMessage("bot", data.response);
    });
}


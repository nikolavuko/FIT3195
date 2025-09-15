// Simple web client: mic STT (Web Speech API) -> backend -> TTS (SpeechSynthesis)

const chatEl = document.getElementById('chat');
const micBtn = document.getElementById('micBtn');
const statusEl = document.getElementById('status');
const avatarEl = document.getElementById('avatar');
const formEl = document.getElementById('textForm');
const inputEl = document.getElementById('textInput');

// Conversation messages
const messages = [
  { role: 'system', content: 'You are Dachikou, a warm, patient elderly companion.' }
];

function addBubble(role, text) {
  const div = document.createElement('div');
  div.className = `bubble ${role}`;
  div.textContent = text;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function setTalking(on) {
  avatarEl.classList.toggle('talking', !!on);
}

function speak(text) {
  if (!('speechSynthesis' in window)) return;
  const utter = new SpeechSynthesisUtterance(text);
  utter.onstart = () => setTalking(true);
  utter.onend = () => setTalking(false);
  speechSynthesis.speak(utter);
}

async function callBackend() {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.reply;
}

async function handleUserMessage(text) {
  const content = text.trim();
  if (!content) return;

  messages.push({ role: 'user', content });
  addBubble('user', content);

  micBtn.disabled = true;
  inputEl.disabled = true;
  statusEl.textContent = 'Thinking...';

  try {
    const reply = await callBackend();
    messages.push({ role: 'assistant', content: reply });
    addBubble('assistant', reply);
    speak(reply);
  } catch (e) {
    console.error(e);
    addBubble('assistant', 'Sorry, I ran into an error.');
  } finally {
    micBtn.disabled = false;
    inputEl.disabled = false;
    statusEl.textContent = 'Idle';
  }
}

formEl.addEventListener('submit', (e) => {
  e.preventDefault();
  const text = inputEl.value;
  inputEl.value = '';
  handleUserMessage(text);
});

// Web Speech API (STT)
let recognition = null;
let recognizing = false;

function getRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return null;
  const rec = new SR();
  rec.lang = 'en-US';
  rec.interimResults = false;
  rec.maxAlternatives = 1;
  return rec;
}

function startListening() {
  if (recognizing) return;
  recognition = getRecognition();
  if (!recognition) {
    alert('SpeechRecognition not supported in this browser. Try Chrome/Edge.');
    return;
  }
  recognizing = true;
  micBtn.textContent = '🛑 Stop Listening';
  micBtn.setAttribute('aria-pressed', 'true');
  statusEl.textContent = 'Listening...';

  recognition.onresult = (e) => {
    const transcript = Array.from(e.results)
      .map(r => r[0].transcript)
      .join(' ');
    handleUserMessage(transcript);
  };
  recognition.onerror = () => {
    statusEl.textContent = 'Idle';
  };
  recognition.onend = () => {
    recognizing = false;
    micBtn.textContent = '🎤 Start Listening';
    micBtn.setAttribute('aria-pressed', 'false');
    statusEl.textContent = 'Idle';
  };
  recognition.start();
}

function stopListening() {
  if (!recognizing || !recognition) return;
  recognition.stop();
}

micBtn.addEventListener('click', () => {
  if (recognizing) stopListening();
  else startListening();
});

// Greet on load
addBubble('assistant', 'Hello! Tap the mic or type a message.');


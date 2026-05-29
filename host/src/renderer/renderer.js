// PeerJS is loaded globally via script tag (window.Peer)
const VIEWER_URL = 'https://Krishnasai4248.github.io/ChromeRemoteDesktopBuild';
const PEERJS_CONFIG = {
  host: '0.peerjs.com',
  port: 443,
  secure: true,
  path: '/',
  config: {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' }
    ]
  }
};

const sessionCodeEl = document.getElementById('sessionCode');
const statusDotEl   = document.getElementById('statusDot');
const statusTextEl  = document.getElementById('statusText');
const copyBtn       = document.getElementById('copyBtn');
const stopBtn       = document.getElementById('stopBtn');
const connectionInfo = document.getElementById('connectionInfo');
const clientCountEl = document.getElementById('clientCount');
const viewerLink    = document.getElementById('viewerLink');

let peer = null;
let screenStream = null;
let activeConnections = 0;
let sessionId = '';

function setStatus(type, text) {
  statusDotEl.className = 'status-dot ' + type;
  statusTextEl.textContent = text;
}

function generateSessionId() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  return Array.from({ length: 6 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
}

async function getScreenStream() {
  const sources = await window.electronAPI.getScreenSources();
  if (!sources.length) throw new Error('No screen sources found');
  const primary = sources[0];

  return navigator.mediaDevices.getUserMedia({
    audio: false,
    video: {
      mandatory: {
        chromeMediaSource: 'desktop',
        chromeMediaSourceId: primary.id,
        maxWidth: window.screen.width,
        maxHeight: window.screen.height,
        maxFrameRate: 30
      }
    }
  });
}

async function init() {
  sessionId = generateSessionId();
  sessionCodeEl.textContent = sessionId;

  viewerLink.href = `${VIEWER_URL}?code=${sessionId}`;
  viewerLink.textContent = 'Open viewer in browser';

  setStatus('waiting', 'Connecting to relay...');

  peer = new window.Peer(sessionId, PEERJS_CONFIG);

  peer.on('open', () => {
    setStatus('ready', 'Waiting for viewer to connect...');
  });

  peer.on('error', (err) => {
    if (err.type === 'unavailable-id') {
      // Regenerate ID and retry
      sessionId = generateSessionId();
      sessionCodeEl.textContent = sessionId;
      peer.destroy();
      init();
    } else {
      setStatus('error', 'Error: ' + err.message);
    }
  });

  // Incoming media call → answer with screen stream
  peer.on('call', async (call) => {
    try {
      if (!screenStream) {
        screenStream = await getScreenStream();
      }
      call.answer(screenStream);
    } catch (err) {
      setStatus('error', 'Screen capture failed: ' + err.message);
    }
  });

  // Incoming data connection → receive input events
  peer.on('connection', async (conn) => {
    conn.on('open', async () => {
      activeConnections++;
      updateConnectionUI();

      // Send screen dimensions so client can scale mouse coordinates
      const info = await window.electronAPI.getScreenInfo();
      conn.send({ type: 'metadata', ...info });
    });

    conn.on('data', (event) => {
      window.electronAPI.injectInput(event);
    });

    conn.on('close', () => {
      activeConnections = Math.max(0, activeConnections - 1);
      updateConnectionUI();
    });
  });
}

function updateConnectionUI() {
  if (activeConnections > 0) {
    setStatus('connected', `${activeConnections} viewer(s) connected`);
    connectionInfo.style.display = 'block';
    stopBtn.style.display = 'block';
    clientCountEl.textContent = activeConnections;
  } else {
    setStatus('ready', 'Waiting for viewer to connect...');
    connectionInfo.style.display = 'none';
    stopBtn.style.display = 'none';
  }
}

copyBtn.addEventListener('click', () => {
  navigator.clipboard.writeText(sessionId).then(() => {
    copyBtn.title = 'Copied!';
    setTimeout(() => { copyBtn.title = 'Copy code'; }, 1500);
  });
});

stopBtn.addEventListener('click', () => {
  if (peer) {
    peer.destroy();
    screenStream?.getTracks().forEach(t => t.stop());
    screenStream = null;
    activeConnections = 0;
    updateConnectionUI();
    init();
  }
});

init();

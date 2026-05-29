import { useEffect, useRef, useState, useCallback } from 'react';
import Peer from 'peerjs';

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

// Cursor SVG arrow (matches Windows default cursor shape)
const CURSOR_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">
  <path d="M2 2 L2 16 L6 12 L9 18 L11 17 L8 11 L14 11 Z"
    fill="white" stroke="black" stroke-width="1.2" stroke-linejoin="round"/>
</svg>`;

export default function Viewer({ sessionCode, onDisconnect }) {
  const videoRef   = useRef(null);
  const cursorRef  = useRef(null);   // local cursor overlay — moved via direct DOM (instant)
  const peerRef    = useRef(null);
  const dataRef    = useRef(null);
  const screenInfo = useRef({ width: 1920, height: 1080 });
  const lastMove   = useRef(0);
  const insideVideo = useRef(false);

  const [status, setStatus]         = useState('connecting');
  const [statusText, setStatusText] = useState('Connecting...');

  function toRemote(clientX, clientY) {
    const rect = videoRef.current.getBoundingClientRect();
    return {
      x: Math.round((clientX - rect.left) * (screenInfo.current.width  / rect.width)),
      y: Math.round((clientY - rect.top)  * (screenInfo.current.height / rect.height))
    };
  }

  function send(data) {
    if (dataRef.current?.open) dataRef.current.send(data);
  }

  // Move local cursor overlay directly via DOM — zero React overhead, feels instant
  function moveCursorOverlay(clientX, clientY) {
    if (!cursorRef.current || !videoRef.current) return;
    const rect = videoRef.current.getBoundingClientRect();
    const lx = clientX - rect.left;
    const ly = clientY - rect.top;
    cursorRef.current.style.transform = `translate(${lx}px, ${ly}px)`;
  }

  const onMouseEnter = useCallback(() => {
    insideVideo.current = true;
    if (cursorRef.current) cursorRef.current.style.opacity = '1';
  }, []);

  const onMouseLeave = useCallback(() => {
    insideVideo.current = false;
    if (cursorRef.current) cursorRef.current.style.opacity = '0';
  }, []);

  const onMouseMove = useCallback((e) => {
    // Move local overlay instantly — no waiting for remote
    moveCursorOverlay(e.clientX, e.clientY);

    // Send to remote throttled at ~120fps
    const now = Date.now();
    if (now - lastMove.current < 8) return;
    lastMove.current = now;
    send({ type: 'mousemove', ...toRemote(e.clientX, e.clientY) });
  }, []);

  const onMouseDown = useCallback((e) => {
    e.preventDefault();
    send({ type: 'mousedown', button: e.button, ...toRemote(e.clientX, e.clientY) });
  }, []);

  const onMouseUp = useCallback((e) => {
    send({ type: 'mouseup', button: e.button });
  }, []);

  const onWheel = useCallback((e) => {
    e.preventDefault();
    send({ type: 'wheel', deltaX: e.deltaX, deltaY: e.deltaY });
  }, []);

  const onKeyDown = useCallback((e) => {
    if (!dataRef.current?.open || !insideVideo.current) return;
    e.preventDefault();
    send({ type: 'keydown', key: e.key, code: e.code });
  }, []);

  const onKeyUp = useCallback((e) => {
    if (!dataRef.current?.open || !insideVideo.current) return;
    e.preventDefault();
    send({ type: 'keyup', key: e.key, code: e.code });
  }, []);

  useEffect(() => {
    const peer = new Peer(PEERJS_CONFIG);
    peerRef.current = peer;

    peer.on('open', () => {
      setStatusText('Establishing connection...');
      const conn = peer.connect(sessionCode, { reliable: false, ordered: false });
      dataRef.current = conn;

      conn.on('open', () => {
        setStatusText('Starting screen stream...');
        const canvas = document.createElement('canvas');
        canvas.width = 1; canvas.height = 1;
        const call = peer.call(sessionCode, canvas.captureStream());

        call.on('stream', (remoteStream) => {
          videoRef.current.srcObject = remoteStream;
          videoRef.current.play().catch(() => {});
          setStatus('connected');
          setStatusText('Connected');
        });

        call.on('close', () => { setStatus('error'); setStatusText('Stream closed'); });
        call.on('error', (err) => { setStatus('error'); setStatusText('Stream error: ' + err.message); });
      });

      conn.on('data', (data) => {
        if (data.type === 'metadata') {
          screenInfo.current = { width: data.width, height: data.height };
        }
      });

      conn.on('close', () => { setStatus('error'); setStatusText('Host disconnected'); });
      conn.on('error', (err) => { setStatus('error'); setStatusText('Error: ' + err.message); });
    });

    peer.on('error', (err) => {
      setStatus('error');
      setStatusText(err.type === 'peer-unavailable'
        ? 'Session code not found. Is the host running?'
        : 'Error: ' + err.message);
    });

    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);

    return () => {
      peer.destroy();
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
    };
  }, [sessionCode]);

  const dotClass = status === 'connected' ? 'green' : status === 'error' ? 'red' : 'yellow';

  return (
    <div className="viewer-screen">
      <div className="viewer-toolbar">
        <div className="toolbar-status">
          <span className={`dot ${dotClass}`} />
          {statusText}
        </div>
        <div className="toolbar-code">Session: <span>{sessionCode}</span></div>
        <button className="disconnect-btn" onClick={onDisconnect}>Disconnect</button>
      </div>

      <div className="viewer-canvas" style={{ position: 'relative' }}>
        {status !== 'connected' && (
          <div className="loading-overlay">
            {status !== 'error' && <div className="spinner" />}
            <span>{statusText}</span>
          </div>
        )}

        {/* Video — cursor: none so only our overlay cursor shows */}
        <video
          ref={videoRef}
          className="remote-video"
          style={{ display: status === 'connected' ? 'block' : 'none', cursor: 'none' }}
          onMouseMove={onMouseMove}
          onMouseDown={onMouseDown}
          onMouseUp={onMouseUp}
          onMouseEnter={onMouseEnter}
          onMouseLeave={onMouseLeave}
          onWheel={onWheel}
          onContextMenu={(e) => e.preventDefault()}
          tabIndex={0}
          muted
          autoPlay
          playsInline
        />

        {/* Local cursor overlay — moves instantly via direct DOM transform */}
        <div
          ref={cursorRef}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: 20,
            height: 20,
            pointerEvents: 'none',
            opacity: 0,
            transform: 'translate(0px, 0px)',
            zIndex: 20,
            // dangerouslySetInnerHTML used below for the SVG
          }}
          dangerouslySetInnerHTML={{ __html: CURSOR_SVG }}
        />
      </div>
    </div>
  );
}

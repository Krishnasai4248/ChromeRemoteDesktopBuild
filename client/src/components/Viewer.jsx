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

export default function Viewer({ sessionCode, onDisconnect }) {
  const videoRef    = useRef(null);
  const peerRef     = useRef(null);
  const dataRef     = useRef(null);
  const screenInfo  = useRef({ width: 1920, height: 1080 });
  const lastMove    = useRef(0);

  const [status, setStatus]           = useState('connecting');
  const [statusText, setStatusText]   = useState('Connecting...');
  const [pointerLocked, setPointerLocked] = useState(false);

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

  // Pointer lock change listener
  useEffect(() => {
    const onChange = () => setPointerLocked(document.pointerLockElement === videoRef.current);
    document.addEventListener('pointerlockchange', onChange);
    return () => document.removeEventListener('pointerlockchange', onChange);
  }, []);

  const requestLock = useCallback(() => {
    if (status === 'connected' && videoRef.current) {
      videoRef.current.requestPointerLock();
    }
  }, [status]);

  // Mouse handlers
  const onMouseMove = useCallback((e) => {
    if (document.pointerLockElement === videoRef.current) {
      // Pointer locked — raw delta, feels native
      if (e.movementX !== 0 || e.movementY !== 0) {
        send({ type: 'mousedelta', dx: e.movementX, dy: e.movementY });
      }
    } else {
      // Not locked — absolute coordinates
      const now = Date.now();
      if (now - lastMove.current < 8) return;
      lastMove.current = now;
      send({ type: 'mousemove', ...toRemote(e.clientX, e.clientY) });
    }
  }, [status]);

  const onMouseDown = useCallback((e) => {
    e.preventDefault();
    if (!pointerLocked) requestLock();
    send({ type: 'mousedown', button: e.button, ...toRemote(e.clientX, e.clientY) });
  }, [pointerLocked, requestLock]);

  const onMouseUp = useCallback((e) => {
    send({ type: 'mouseup', button: e.button });
  }, []);

  const onWheel = useCallback((e) => {
    e.preventDefault();
    send({ type: 'wheel', deltaX: e.deltaX, deltaY: e.deltaY });
  }, []);

  const onKeyDown = useCallback((e) => {
    if (!dataRef.current?.open) return;
    e.preventDefault();
    send({ type: 'keydown', key: e.key, code: e.code });
  }, []);

  const onKeyUp = useCallback((e) => {
    if (!dataRef.current?.open) return;
    e.preventDefault();
    send({ type: 'keyup', key: e.key, code: e.code });
  }, []);

  useEffect(() => {
    const peer = new Peer(PEERJS_CONFIG);
    peerRef.current = peer;

    peer.on('open', () => {
      setStatusText('Establishing data channel...');
      const conn = peer.connect(sessionCode, { reliable: false, ordered: false });
      dataRef.current = conn;

      conn.on('open', () => {
        setStatusText('Requesting screen stream...');
        const canvas = document.createElement('canvas');
        canvas.width = 1; canvas.height = 1;
        const call = peer.call(sessionCode, canvas.captureStream());

        call.on('stream', (remoteStream) => {
          videoRef.current.srcObject = remoteStream;
          videoRef.current.play().catch(() => {});
          setStatus('connected');
          setStatusText('Connected — click screen to capture mouse');
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
          {pointerLocked ? 'Mouse captured — Press Escape to release' : statusText}
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

        {/* Click-to-capture overlay — shown when connected but mouse not locked */}
        {status === 'connected' && !pointerLocked && (
          <div
            className="loading-overlay"
            style={{ background: 'rgba(0,0,0,0.45)', cursor: 'pointer' }}
            onClick={requestLock}
          >
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="1.5">
              <path d="M12 2C8.13 2 5 5.13 5 9v3H4v10h16V12h-1V9c0-3.87-3.13-7-7-7zm0 2c2.76 0 5 2.24 5 5v3H7V9c0-2.76 2.24-5 5-5z" fill="#60a5fa" stroke="none"/>
            </svg>
            <span style={{ color: '#60a5fa', fontWeight: 600 }}>Click to capture mouse</span>
            <span style={{ color: '#94a3b8', fontSize: 12 }}>Press Escape to release</span>
          </div>
        )}

        <video
          ref={videoRef}
          className="remote-video"
          style={{ display: status === 'connected' ? 'block' : 'none' }}
          onMouseMove={onMouseMove}
          onMouseDown={onMouseDown}
          onMouseUp={onMouseUp}
          onWheel={onWheel}
          onContextMenu={(e) => e.preventDefault()}
          tabIndex={0}
          muted
          autoPlay
          playsInline
        />
      </div>
    </div>
  );
}

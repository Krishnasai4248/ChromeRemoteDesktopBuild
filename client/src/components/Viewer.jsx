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
  const videoRef   = useRef(null);
  const peerRef    = useRef(null);
  const dataRef    = useRef(null);
  const screenInfo = useRef({ width: 1920, height: 1080 });
  const lastMove   = useRef(0);

  const [status, setStatus] = useState('connecting');
  const [statusText, setStatusText] = useState('Connecting...');

  // Scale video-element coordinates → remote screen coordinates
  function toRemote(clientX, clientY) {
    const rect = videoRef.current.getBoundingClientRect();
    const scaleX = screenInfo.current.width  / rect.width;
    const scaleY = screenInfo.current.height / rect.height;
    return {
      x: Math.round((clientX - rect.left) * scaleX),
      y: Math.round((clientY - rect.top)  * scaleY)
    };
  }

  function send(data) {
    if (dataRef.current?.open) dataRef.current.send(data);
  }

  // Mouse handlers
  const onMouseMove = useCallback((e) => {
    const now = Date.now();
    if (now - lastMove.current < 8) return; // ~120fps throttle
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

  // Keyboard handlers — attached to window so capture works globally
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

      // 1. Open data connection for input events
      const conn = peer.connect(sessionCode, { reliable: false });
      dataRef.current = conn;

      conn.on('open', () => {
        setStatusText('Requesting screen stream...');

        // 2. Call the host for the video stream
        const canvas = document.createElement('canvas');
        canvas.width = 1; canvas.height = 1;
        const emptyStream = canvas.captureStream();
        const call = peer.call(sessionCode, emptyStream);

        call.on('stream', (remoteStream) => {
          videoRef.current.srcObject = remoteStream;
          videoRef.current.play().catch(() => {});
          setStatus('connected');
          setStatusText('Connected');
        });

        call.on('error', (err) => {
          setStatus('error');
          setStatusText('Stream error: ' + err.message);
        });

        call.on('close', () => {
          setStatus('error');
          setStatusText('Stream closed');
        });
      });

      conn.on('data', (data) => {
        if (data.type === 'metadata') {
          screenInfo.current = { width: data.width, height: data.height };
        }
      });

      conn.on('close', () => {
        setStatus('error');
        setStatusText('Host disconnected');
      });

      conn.on('error', (err) => {
        setStatus('error');
        setStatusText('Connection error: ' + err.message);
      });
    });

    peer.on('error', (err) => {
      if (err.type === 'peer-unavailable') {
        setStatus('error');
        setStatusText('Session code not found. Is the host running?');
      } else {
        setStatus('error');
        setStatusText('Error: ' + err.message);
      }
    });

    // Keyboard listeners on window (full capture)
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
        <div className="toolbar-code">
          Session: <span>{sessionCode}</span>
        </div>
        <button className="disconnect-btn" onClick={onDisconnect}>
          Disconnect
        </button>
      </div>

      <div className="viewer-canvas" style={{ position: 'relative' }}>
        {status !== 'connected' && (
          <div className="loading-overlay">
            {status !== 'error' && <div className="spinner" />}
            <span>{statusText}</span>
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

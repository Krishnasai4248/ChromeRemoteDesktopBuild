import { useState, useEffect } from 'react';
import ConnectForm from './components/ConnectForm';
import Viewer from './components/Viewer';

export default function App() {
  const [sessionCode, setSessionCode] = useState('');
  const [connected, setConnected] = useState(false);

  // Pre-fill session code from URL param ?code=XXXXXX
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    if (code) setSessionCode(code.toUpperCase().slice(0, 6));
  }, []);

  function handleConnect(code) {
    setSessionCode(code);
    setConnected(true);
  }

  function handleDisconnect() {
    setConnected(false);
    setSessionCode('');
  }

  return connected
    ? <Viewer sessionCode={sessionCode} onDisconnect={handleDisconnect} />
    : <ConnectForm initialCode={sessionCode} onConnect={handleConnect} />;
}

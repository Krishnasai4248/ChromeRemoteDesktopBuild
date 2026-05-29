import { useState } from 'react';

export default function ConnectForm({ initialCode, onConnect }) {
  const [code, setCode] = useState(initialCode || '');
  const [error, setError] = useState('');

  function handleInput(e) {
    const val = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
    setCode(val);
    setError('');
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (code.length !== 6) {
      setError('Please enter the full 6-character session code.');
      return;
    }
    onConnect(code);
  }

  return (
    <div className="connect-screen">
      <div className="connect-card">
        <div className="connect-logo">
          <svg width="52" height="52" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="#2563EB"/>
            <rect x="8" y="10" width="32" height="22" rx="3" fill="white" opacity="0.9"/>
            <rect x="18" y="32" width="12" height="3" fill="white" opacity="0.9"/>
            <rect x="14" y="35" width="20" height="3" rx="1.5" fill="white" opacity="0.9"/>
          </svg>
          <h1>Remote Desktop</h1>
          <p>Enter the session code shown on the host machine</p>
        </div>

        <form className="form-group" onSubmit={handleSubmit}>
          <label htmlFor="codeInput">Session Code</label>
          <input
            id="codeInput"
            type="text"
            placeholder="ABC123"
            value={code}
            onChange={handleInput}
            autoFocus
            autoComplete="off"
            spellCheck={false}
          />
          {error && <span className="error-msg">{error}</span>}
          <button
            className="connect-btn"
            type="submit"
            disabled={code.length !== 6}
            style={{ marginTop: 4 }}
          >
            Connect
          </button>
        </form>
      </div>
    </div>
  );
}

"""Claude Code Stop hook - captures token usage per agent turn.

Called by Claude Code after each agent turn completes.
Receives a JSON payload on stdin with usage data.

Pushes token data directly to the telemetry service immediately.
Falls back to writing a local file if the push fails, so the next
polaris CLI invocation can sweep and retry.

Never raises or prints errors - silent failure is intentional.
The CLI is never blocked by this script.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def _read_service_config() -> tuple[str, str]:
    """Read service_url and api_key from ~/.polaris/config.yaml."""
    config_path = Path.home() / ".polaris" / "config.yaml"
    if not config_path.exists():
        return "", ""
    try:
        import yaml
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        telemetry = config.get("telemetry", {})
        if not isinstance(telemetry, dict):
            return "", ""
        return telemetry.get("service_url", ""), telemetry.get("api_key", "")
    except Exception:
        return "", ""


def _push_to_service(token_data: dict, service_url: str, api_key: str) -> bool:
    """POST token data directly to the service. Returns True on success."""
    try:
        import urllib.request
        endpoint = f"{service_url.rstrip('/')}/tokens/batch"
        payload = json.dumps([token_data]).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        }
        req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status < 300
    except Exception:
        return False


def _write_fallback_file(token_data: dict, session_id: str, session_seq: int) -> None:
    """Write token data to a local file as fallback for next CLI sweep."""
    try:
        token_dir = Path.home() / ".polaris" / "telemetry"
        token_dir.mkdir(parents=True, exist_ok=True)
        token_file = token_dir / f"token-{session_id}-{session_seq}.json"
        token_file.write_text(json.dumps(token_data), encoding="utf-8")
    except Exception:
        pass


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    usage = payload.get("usage") or {}
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    cache_read = int(usage.get("cache_read_input_tokens") or 0)
    cache_creation = int(usage.get("cache_creation_input_tokens") or 0)

    # Nothing to record if there are no tokens
    if (input_tokens + output_tokens) == 0:
        return

    # Effective input tokens includes cache hits (still consumed compute)
    effective_input = input_tokens + cache_read + cache_creation

    # Read session and last command info from last-command.json
    last_cmd_file = Path.home() / ".polaris" / "telemetry" / "last-command.json"
    command = ""
    session_id = ""
    session_seq = 0
    project = ""
    user_email = ""

    if last_cmd_file.exists():
        try:
            last = json.loads(last_cmd_file.read_text(encoding="utf-8"))
            command = last.get("command") or ""
            session_id = last.get("session_id") or ""
            session_seq = int(last.get("session_seq") or 0)
            project = last.get("project") or ""
            user_email = last.get("git_user_email") or ""
        except Exception:
            pass

    # Fall back to env var if last-command.json is not yet written
    if not session_id:
        session_id = os.environ.get("POLARIS_SESSION_ID") or ""
    if not session_id:
        return

    token_data = {
        "session_id": session_id,
        "session_seq": session_seq,
        "command": command,
        "user_email": user_email,
        "project": project,
        "input_tokens": effective_input,
        "output_tokens": output_tokens,
        "total_tokens": effective_input + output_tokens,
        "model_id": str(payload.get("model") or ""),
        "provider": "anthropic",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }

    # Try to push immediately to service
    service_url, api_key = _read_service_config()
    if service_url and api_key:
        pushed = _push_to_service(token_data, service_url, api_key)
        if pushed:
            return  # Success - no need for fallback file

    # Fallback: write file for next polaris CLI command to sweep and retry
    _write_fallback_file(token_data, session_id, session_seq)


if __name__ == "__main__":
    main()

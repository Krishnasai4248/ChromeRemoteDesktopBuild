// Input injection via a persistent PowerShell process.
// Uses Windows user32.dll (SetCursorPos, mouse_event, keybd_event) — no native npm modules needed.
const { spawn } = require('child_process');
const os   = require('os');
const path = require('path');
const fs   = require('fs');

// Browser KeyboardEvent.key → Windows Virtual Key code
const VK = {
  // Letters
  a:0x41,b:0x42,c:0x43,d:0x44,e:0x45,f:0x46,g:0x47,h:0x48,
  i:0x49,j:0x4A,k:0x4B,l:0x4C,m:0x4D,n:0x4E,o:0x4F,p:0x50,
  q:0x51,r:0x52,s:0x53,t:0x54,u:0x55,v:0x56,w:0x57,x:0x58,y:0x59,z:0x5A,
  // Number row
  '0':0x30,'1':0x31,'2':0x32,'3':0x33,'4':0x34,
  '5':0x35,'6':0x36,'7':0x37,'8':0x38,'9':0x39,
  // Control
  Enter:0x0D, Backspace:0x08, Delete:0x2E, Escape:0x1B, Tab:0x09, ' ':0x20,
  // Arrows
  ArrowLeft:0x25, ArrowUp:0x26, ArrowRight:0x27, ArrowDown:0x28,
  // Modifiers
  Control:0xA2, Shift:0xA0, Alt:0xA4, Meta:0x5B,
  // Function keys
  F1:0x70,F2:0x71,F3:0x72,F4:0x73,F5:0x74,F6:0x75,
  F7:0x76,F8:0x77,F9:0x78,F10:0x79,F11:0x7A,F12:0x7B,
  // Navigation
  Home:0x24, End:0x23, PageUp:0x21, PageDown:0x22, Insert:0x2D,
  // Symbols
  '-':0xBD,'=':0xBB,'[':0xDB,']':0xDD,'\\':0xDC,
  ';':0xBA,"'":0xDE,',':0xBC,'.':0xBE,'/':0xBF,'`':0xC0
};

// Inline C# loaded once into a persistent PowerShell process.
// mouse_event / keybd_event flags used here:
//   mouse: 0x0002=LEFTDOWN, 0x0004=LEFTUP, 0x0008=RIGHTDOWN, 0x0010=RIGHTUP, 0x0800=WHEEL
//   keybd: 0=press, 0x0002=KEYUP
const PS_SCRIPT = String.raw`
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W32 {
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint x, uint y, int d, IntPtr e);
    [DllImport("user32.dll")] public static extern void keybd_event(byte v, byte s, uint f, IntPtr e);
}
"@
while ($true) {
    $line = [Console]::ReadLine()
    if ($null -eq $line) { break }
    try {
        $c = $line | ConvertFrom-Json
        switch ($c.type) {
            'mousemove' { [W32]::SetCursorPos([int]$c.x, [int]$c.y) }
            'mousedown' {
                [W32]::SetCursorPos([int]$c.x, [int]$c.y)
                if ($c.button -eq 2) { [W32]::mouse_event(8,   0,0,0,[IntPtr]::Zero) }
                else                 { [W32]::mouse_event(2,   0,0,0,[IntPtr]::Zero) }
            }
            'mouseup' {
                if ($c.button -eq 2) { [W32]::mouse_event(16,  0,0,0,[IntPtr]::Zero) }
                else                 { [W32]::mouse_event(4,   0,0,0,[IntPtr]::Zero) }
            }
            'wheel' {
                $d = if ($c.deltaY -gt 0) { -120 } else { 120 }
                [W32]::mouse_event(2048, 0,0,$d,[IntPtr]::Zero)
            }
            'keydown' { [W32]::keybd_event([byte]$c.vk, 0, 0, [IntPtr]::Zero) }
            'keyup'   { [W32]::keybd_event([byte]$c.vk, 0, 2, [IntPtr]::Zero) }
        }
    } catch {}
}
`;

let psProc = null;

function startPs() {
  const scriptPath = path.join(os.tmpdir(), 'rdhost-input.ps1');
  fs.writeFileSync(scriptPath, PS_SCRIPT, 'utf8');

  psProc = spawn('powershell', [
    '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
    '-File', scriptPath
  ], { stdio: ['pipe', 'ignore', 'ignore'] });

  psProc.on('exit', () => setTimeout(startPs, 500));
}

startPs();

function send(cmd) {
  if (psProc?.stdin?.writable) {
    psProc.stdin.write(JSON.stringify(cmd) + '\n');
  }
}

function resolveVK(key) {
  return VK[key] ?? VK[key.toLowerCase()] ?? null;
}

async function handleInput(event) {
  switch (event.type) {
    case 'mousemove':
      send({ type: 'mousemove', x: Math.round(event.x), y: Math.round(event.y) });
      break;
    case 'mousedown':
      send({ type: 'mousedown', button: event.button, x: Math.round(event.x), y: Math.round(event.y) });
      break;
    case 'mouseup':
      send({ type: 'mouseup', button: event.button });
      break;
    case 'wheel':
      send({ type: 'wheel', deltaY: event.deltaY });
      break;
    case 'keydown': {
      const vk = resolveVK(event.key);
      if (vk) send({ type: 'keydown', vk });
      break;
    }
    case 'keyup': {
      const vk = resolveVK(event.key);
      if (vk) send({ type: 'keyup', vk });
      break;
    }
  }
}

module.exports = { handleInput };

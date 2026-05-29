// Input injection via a compiled C# helper exe (compiled once on startup using csc.exe).
// Falls back to PowerShell if .NET csc.exe is not found.
const { spawn, execSync } = require('child_process');
const os   = require('os');
const path = require('path');
const fs   = require('fs');

const EXE_PATH = path.join(os.tmpdir(), 'rdhost-input-v2.exe');
const CS_PATH  = path.join(os.tmpdir(), 'rdhost-input-v2.cs');

// Tiny C# console app: reads plain-text commands from stdin, calls Win32 directly.
// Protocol: m x y | ld x y | lu | rd x y | ru | w delta | kd vk | ku vk
const CS_SOURCE = `
using System;
using System.Runtime.InteropServices;
class I {
    [DllImport("user32.dll")] static extern bool SetCursorPos(int x,int y);
    [DllImport("user32.dll")] static extern void mouse_event(uint f,uint x,uint y,int d,IntPtr e);
    [DllImport("user32.dll")] static extern void keybd_event(byte v,byte s,uint f,IntPtr e);
    static void Main(){
        string line;
        while((line=Console.ReadLine())!=null){
            try{
                var p=line.Split(' ');
                switch(p[0]){
                    case "m":  SetCursorPos(int.Parse(p[1]),int.Parse(p[2])); break;
                    case "ld": SetCursorPos(int.Parse(p[1]),int.Parse(p[2])); mouse_event(2,0,0,0,IntPtr.Zero); break;
                    case "lu": mouse_event(4,0,0,0,IntPtr.Zero); break;
                    case "rd": SetCursorPos(int.Parse(p[1]),int.Parse(p[2])); mouse_event(8,0,0,0,IntPtr.Zero); break;
                    case "ru": mouse_event(16,0,0,0,IntPtr.Zero); break;
                    case "md": mouse_event(1,(uint)int.Parse(p[1]),(uint)int.Parse(p[2]),0,IntPtr.Zero); break;
                    case "w":  mouse_event(2048,0,0,int.Parse(p[1])>0?-120:120,IntPtr.Zero); break;
                    case "kd": keybd_event((byte)int.Parse(p[1]),0,0,IntPtr.Zero); break;
                    case "ku": keybd_event((byte)int.Parse(p[1]),0,2,IntPtr.Zero); break;
                }
            }catch{}
        }
    }
}`;

// Fallback PowerShell script (same protocol, used if csc.exe not available)
const PS_SCRIPT = String.raw`
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W32 {
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,int d,IntPtr e);
    [DllImport("user32.dll")] public static extern void keybd_event(byte v,byte s,uint f,IntPtr e);
}
"@
while($true){
    $line=[Console]::ReadLine()
    if($null -eq $line){break}
    $p=$line -split ' '
    switch($p[0]){
        'm'  {[W32]::SetCursorPos([int]$p[1],[int]$p[2])}
        'ld' {[W32]::SetCursorPos([int]$p[1],[int]$p[2]);[W32]::mouse_event(2,0,0,0,[IntPtr]::Zero)}
        'lu' {[W32]::mouse_event(4,0,0,0,[IntPtr]::Zero)}
        'rd' {[W32]::SetCursorPos([int]$p[1],[int]$p[2]);[W32]::mouse_event(8,0,0,0,[IntPtr]::Zero)}
        'ru' {[W32]::mouse_event(16,0,0,0,[IntPtr]::Zero)}
        'md' {[W32]::mouse_event(1,[uint][int]$p[1],[uint][int]$p[2],0,[IntPtr]::Zero)}
        'w'  {$d=if([int]$p[1]-gt 0){-120}else{120};[W32]::mouse_event(2048,0,0,$d,[IntPtr]::Zero)}
        'kd' {[W32]::keybd_event([byte][int]$p[1],0,0,[IntPtr]::Zero)}
        'ku' {[W32]::keybd_event([byte][int]$p[1],0,2,[IntPtr]::Zero)}
    }
}`;

// Browser KeyboardEvent.key → Windows Virtual Key code
const VK = {
  a:0x41,b:0x42,c:0x43,d:0x44,e:0x45,f:0x46,g:0x47,h:0x48,
  i:0x49,j:0x4A,k:0x4B,l:0x4C,m:0x4D,n:0x4E,o:0x4F,p:0x50,
  q:0x51,r:0x52,s:0x53,t:0x54,u:0x55,v:0x56,w:0x57,x:0x58,y:0x59,z:0x5A,
  '0':0x30,'1':0x31,'2':0x32,'3':0x33,'4':0x34,
  '5':0x35,'6':0x36,'7':0x37,'8':0x38,'9':0x39,
  Enter:0x0D,Backspace:0x08,Delete:0x2E,Escape:0x1B,Tab:0x09,' ':0x20,
  ArrowLeft:0x25,ArrowUp:0x26,ArrowRight:0x27,ArrowDown:0x28,
  Control:0xA2,Shift:0xA0,Alt:0xA4,Meta:0x5B,
  F1:0x70,F2:0x71,F3:0x72,F4:0x73,F5:0x74,F6:0x75,
  F7:0x76,F8:0x77,F9:0x78,F10:0x79,F11:0x7A,F12:0x7B,
  Home:0x24,End:0x23,PageUp:0x21,PageDown:0x22,Insert:0x2D,
  '-':0xBD,'=':0xBB,'[':0xDB,']':0xDD,'\\':0xDC,
  ';':0xBA,"'":0xDE,',':0xBC,'.':0xBE,'/':0xBF,'`':0xC0
};

function findCsc() {
  const candidates = [
    'C:\\Windows\\Microsoft.NET\\Framework64\\v4.0.30319\\csc.exe',
    'C:\\Windows\\Microsoft.NET\\Framework\\v4.0.30319\\csc.exe',
  ];
  return candidates.find(p => fs.existsSync(p));
}

function buildExe() {
  const csc = findCsc();
  if (!csc) return false;
  try {
    fs.writeFileSync(CS_PATH, CS_SOURCE, 'utf8');
    execSync(`"${csc}" /nologo /out:"${EXE_PATH}" "${CS_PATH}"`, { timeout: 15000 });
    return fs.existsSync(EXE_PATH);
  } catch {
    return false;
  }
}

let proc = null;

function startProc() {
  let useExe = fs.existsSync(EXE_PATH) || buildExe();

  if (useExe) {
    proc = spawn(EXE_PATH, [], { stdio: ['pipe', 'ignore', 'ignore'] });
  } else {
    // Fallback: PowerShell
    const psPath = path.join(os.tmpdir(), 'rdhost-input.ps1');
    fs.writeFileSync(psPath, PS_SCRIPT, 'utf8');
    proc = spawn('powershell', [
      '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', psPath
    ], { stdio: ['pipe', 'ignore', 'ignore'] });
  }

  proc.on('exit', () => setTimeout(startProc, 500));
}

startProc();

function write(cmd) {
  if (proc?.stdin?.writable) proc.stdin.write(cmd + '\n');
}

function resolveVK(key) {
  return VK[key] ?? VK[key.toLowerCase()] ?? null;
}

async function handleInput(event) {
  switch (event.type) {
    case 'mousedelta':
      write(`md ${Math.round(event.dx)} ${Math.round(event.dy)}`);
      break;
    case 'mousemove':
      write(`m ${Math.round(event.x)} ${Math.round(event.y)}`);
      break;
    case 'mousedown':
      write(event.button === 2
        ? `rd ${Math.round(event.x)} ${Math.round(event.y)}`
        : `ld ${Math.round(event.x)} ${Math.round(event.y)}`);
      break;
    case 'mouseup':
      write(event.button === 2 ? 'ru' : 'lu');
      break;
    case 'wheel':
      write(`w ${event.deltaY}`);
      break;
    case 'keydown': {
      const vk = resolveVK(event.key);
      if (vk) write(`kd ${vk}`);
      break;
    }
    case 'keyup': {
      const vk = resolveVK(event.key);
      if (vk) write(`ku ${vk}`);
      break;
    }
  }
}

module.exports = { handleInput };

const { app, BrowserWindow, ipcMain, desktopCapturer, screen } = require('electron');
const path = require('path');
const { handleInput } = require('./input');

// DXGI Desktop Duplication fails in RDP/virtual machine sessions.
// Disabling hardware acceleration forces GDI capture which works everywhere.
app.disableHardwareAcceleration();

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 420,
    height: 560,
    resizable: false,
    title: 'Remote Desktop Host',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
  mainWindow.setMenuBarVisibility(false);
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// Return all available screen sources to renderer
ipcMain.handle('get-screen-sources', async () => {
  const sources = await desktopCapturer.getSources({
    types: ['screen'],
    thumbnailSize: { width: 0, height: 0 }
  });
  return sources.map(s => ({ id: s.id, name: s.name }));
});

// Return primary display dimensions for coordinate mapping
ipcMain.handle('get-screen-info', () => {
  const display = screen.getPrimaryDisplay();
  return {
    width: display.bounds.width,
    height: display.bounds.height,
    scaleFactor: display.scaleFactor
  };
});

// Inject keyboard/mouse input from remote client
ipcMain.on('inject-input', async (_event, inputEvent) => {
  try {
    await handleInput(inputEvent);
  } catch (err) {
    console.error('Input injection error:', err.message);
  }
});

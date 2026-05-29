const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getScreenSources: () => ipcRenderer.invoke('get-screen-sources'),
  getScreenInfo: () => ipcRenderer.invoke('get-screen-info'),
  injectInput: (event) => ipcRenderer.send('inject-input', event)
});

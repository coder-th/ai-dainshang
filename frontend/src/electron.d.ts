interface UpdaterStatus {
  status: 'idle' | 'checking' | 'available' | 'not-available' | 'downloading' | 'downloaded' | 'error'
  version?: string
  percent?: number
  message?: string
}

interface ElectronAPI {
  minimize(): void
  maximize(): void
  close(): void
  reload(): void
  isMaximized(): Promise<boolean>
  onMaximizeChange(cb: (val: boolean) => void): void
  selectDirectory(): Promise<string | undefined>
  checkForUpdates(): Promise<void>
  installUpdate(): Promise<void>
  onUpdateStatus(cb: (payload: UpdaterStatus) => void): void
}

interface Window {
  electronAPI?: ElectronAPI
  __APP_VERSION__?: string
}

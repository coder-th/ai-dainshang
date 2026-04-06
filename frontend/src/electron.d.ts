interface ElectronAPI {
  minimize(): void
  maximize(): void
  close(): void
  reload(): void
  isMaximized(): Promise<boolean>
  onMaximizeChange(cb: (val: boolean) => void): void
  selectDirectory(): Promise<string | undefined>
}

interface Window {
  electronAPI: ElectronAPI
}

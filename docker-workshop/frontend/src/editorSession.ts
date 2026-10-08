export interface FileDocument {
  path: string
  content: string
  language: string
}

export interface FileClient {
  read(path: string): Promise<FileDocument>
  write(path: string, content: string): Promise<void>
}

/** Keeps pending edits separate from the last successfully saved snapshot. */
export class EditorSession {
  path = ''
  content = ''
  savedContent = ''
  error = ''
  saving = false
  loading = false
  client: FileClient
  private requestedPath = ''
  private requestedReload = false
  private opening: Promise<void> | null = null
  private pendingSave: Promise<boolean> | null = null

  constructor(client: FileClient) {
    this.client = client
  }

  get dirty(): boolean {
    return this.content !== this.savedContent
  }

  async open(path: string, reload = false): Promise<boolean> {
    this.requestedPath = path
    this.requestedReload = reload
    if (!this.opening) {
      this.opening = this.openRequestedFile().finally(() => { this.opening = null })
    }
    await this.opening
    return this.path === path && !this.error
  }

  async reload(): Promise<boolean> {
    if (this.dirty) {
      this.error = 'Save your pending edits before reloading this file.'
      return false
    }
    if (!this.path || this.opening || this.saving) return false
    return this.open(this.path, true)
  }

  private async openRequestedFile(): Promise<void> {
    while (this.requestedPath) {
      if (!(await this.save()) || this.dirty) {
        this.requestedPath = ''
        return
      }
      const path = this.requestedPath
      const reload = this.requestedReload
      this.requestedPath = ''
      if (path === this.path && !reload) continue
      this.loading = true
      this.error = ''
      try {
        const file = await this.client.read(path)
        // A later lesson/file request supersedes this response.
        if (!this.requestedPath || this.requestedPath === path) {
          this.path = file.path
          this.content = file.content
          this.savedContent = file.content
        }
      } catch (error) {
        if (!this.requestedPath) this.error = error instanceof Error ? error.message : String(error)
      } finally {
        this.loading = false
      }
    }
  }

  async save(): Promise<boolean> {
    if (this.pendingSave) return this.pendingSave
    if (!this.path || !this.dirty) return true
    this.pendingSave = this.writeSnapshot().finally(() => { this.pendingSave = null })
    return this.pendingSave
  }

  private async writeSnapshot(): Promise<boolean> {
    const content = this.content
    this.saving = true
    this.error = ''
    try {
      await this.client.write(this.path, content)
      this.savedContent = content
      return true
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error)
      return false
    } finally {
      this.saving = false
    }
  }
}

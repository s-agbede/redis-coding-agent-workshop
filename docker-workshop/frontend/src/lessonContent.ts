/** Enhance trusted, rendered lesson HTML without putting UI text inside code. */
export function withCopyButtons(html: string): string {
  return html.replace(/<pre><code\b([^>]*)>([\s\S]*?)<\/code><\/pre>/g,
    (block: string, attributes: string): string => {
      const runnable = /class="language-(?:bash|sh|shell)"/.test(attributes)
      const label = runnable ? 'Run code' : /class="language-(?:text|json)"/.test(attributes) ? 'Copy text' : 'Copy code'
      const action = runnable ? 'run' : 'copy'
      const description = runnable ? 'Run code in Terminal' : `${label} to clipboard`
      return `<div class="lesson-code"><button type="button" data-${action}-code aria-label="${description}">${label}</button><span data-${action}-error role="alert" hidden></span><span data-run-status role="status" hidden></span>${block}</div>`
    })
}

type CodeActionResult = { ok: boolean; message: string }

/** Dispatch once: a lost response must never cause a command to run twice. */
export async function runCode(command: string, endpoint: string, request: typeof fetch = fetch): Promise<CodeActionResult> {
  try {
    const response = await request(endpoint, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command })
    })
    const payload: unknown = await response.json()
    if (response.ok && payload && typeof payload === 'object' && 'status' in payload && payload.status === 'sent') {
      return { ok: true, message: 'Sent to Terminal. Check the output there.' }
    }
    if (!response.ok && payload && typeof payload === 'object' && 'detail' in payload && typeof payload.detail === 'string') {
      return { ok: false, message: payload.detail }
    }
  } catch {
    // A network/proxy failure may happen after the terminal accepted the command.
  }
  return { ok: false, message: 'Could not confirm delivery. Check Terminal before running again.' }
}

/** Link exact workspace paths in prose, leaving copied code and web links intact. */
export function withFileButtons(html: string, filePaths: readonly string[]): string {
  const paths = new Set(filePaths.filter(path =>
    /^[a-zA-Z0-9_.-]+(?:\/[a-zA-Z0-9_.-]+)*$/.test(path) &&
    path.split('/').every(part => part !== '.' && part !== '..')
  ))
  return html.replace(/<pre\b[^>]*>[\s\S]*?<\/pre>|<a\b[^>]*>[\s\S]*?<\/a>|<button\b[^>]*>[\s\S]*?<\/button>|<(code|strong)>([a-zA-Z0-9_./-]+)<\/\1>/g,
    (original: string, tag?: string, path?: string): string => tag && path && paths.has(path)
      ? `<button type="button" class="lesson-file" data-open-file="${path}" aria-label="Open ${path} in editor" title="Open ${path} in editor">${original}</button>`
      : original)
}

export async function copyCode(text: string, clipboard?: Pick<Clipboard, 'writeText'>): Promise<{ ok: boolean; message: string }> {
  try {
    if (!clipboard) throw new Error('Clipboard unavailable')
    await clipboard.writeText(text)
    return { ok: true, message: 'Copied' }
  } catch {
    return { ok: false, message: 'Copy failed. Select the code and copy it manually.' }
  }
}

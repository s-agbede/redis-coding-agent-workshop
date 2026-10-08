export interface TextState {
  content: string
  start: number
  end: number
}

const INDENT = '    '

export function indentText(state: TextState, outdent = false): TextState {
  const { content, start, end } = state
  if (start === end && !outdent) {
    return { content: content.slice(0, start) + INDENT + content.slice(end), start: start + 4, end: start + 4 }
  }
  const first = start === 0 ? 0 : content.lastIndexOf('\n', start - 1) + 1
  const last = end > start && content[end - 1] === '\n' ? end - 1 : end
  const edits: Array<{ at: number; remove: number; insert: string }> = []
  for (let at = first; at <= last;) {
    const remove = outdent ? (content.slice(at).match(/^(?:\t| {1,4})/)?.[0].length || 0) : 0
    edits.push({ at, remove, insert: outdent ? '' : INDENT })
    const next = content.indexOf('\n', at)
    if (next < 0) break
    at = next + 1
  }
  const position = (offset: number): number => offset + edits.reduce((delta, edit) => {
    if (edit.at > offset) return delta
    return delta + edit.insert.length - Math.min(edit.remove, offset - edit.at)
  }, 0)
  let result = content
  for (const edit of [...edits].reverse()) {
    result = result.slice(0, edit.at) + edit.insert + result.slice(edit.at + edit.remove)
  }
  return { content: result, start: position(start), end: position(end) }
}

export function enterText({ content, start, end }: TextState): TextState {
  const line = content.slice(start === 0 ? 0 : content.lastIndexOf('\n', start - 1) + 1, start)
  const indent = line.match(/^[\t ]*/)?.[0] || ''
  const insert = '\n' + indent + (line.trimEnd().endsWith(':') ? INDENT : '')
  return { content: content.slice(0, start) + insert + content.slice(end), start: start + insert.length, end: start + insert.length }
}

export function nextExercise(state: TextState): TextState | null {
  // Older workspaces keep their original labels; only visit the exercise header.
  const markers = [...state.content.matchAll(/^[\t ]*#[\t ]*((?:EXERCISE|BLANK)[\t ]+\d+\b[^\r\n]*)/gm)]
    .map(match => ({ start: match.index + match[0].length - match[1].length, end: match.index + match[0].length }))
  const marker = markers.find(item => item.start >= state.end) || markers[0]
  return marker ? { content: state.content, ...marker } : null
}

/** Local history includes programmatic indentation as well as native text input. */
export class TextHistory {
  private entries: TextState[]
  private index = 0

  constructor(initial: TextState) { this.entries = [{ ...initial }] }

  record(state: TextState): void {
    if (this.entries[this.index].content === state.content) {
      this.entries[this.index] = { ...state }
      return
    }
    this.entries = this.entries.slice(0, this.index + 1)
    this.entries.push({ ...state })
    if (this.entries.length > 200) this.entries.shift()
    this.index = this.entries.length - 1
  }

  undo(): TextState | null {
    if (this.index === 0) return null
    return { ...this.entries[--this.index] }
  }

  redo(): TextState | null {
    if (this.index === this.entries.length - 1) return null
    return { ...this.entries[++this.index] }
  }
}

const WORKSHOP_FILES = [
  'first_call.py', 'tools.py', 'agent.py', 'main.py', 'ui.py',
  'checkpoints/history.py', 'checkpoints/outcome_demo.py', 'checkpoints/stage2_one_tool.py',
  'checkpoints/stage1_chat.py', 'checkpoints/description_lab.py', 'checkpoints/notes.txt',
  'checkpoints/recovery.py', 'capstone/app.py',
  'capstone/index.html', 'capstone/AGENTS.md', 'check_setup.py', 'verify_capstone.py'
]

export function visibleFiles<T extends { path: string }>(files: T[], all: boolean, current: string): T[] {
  if (all) return files
  const paths = [...WORKSHOP_FILES, ...(WORKSHOP_FILES.includes(current) ? [] : [current])]
  return paths.flatMap(path => files.filter(file => file.path === path))
}

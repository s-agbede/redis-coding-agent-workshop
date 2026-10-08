type ProgressStorage = Pick<Storage, 'getItem' | 'setItem'>
interface Lesson { file: string; title: string }

export interface LessonEvidence {
  practicalChecked: boolean
  explanationCompared: boolean
  liveModelAttempted: boolean
  notes: string
}

const emptyEvidence = (): LessonEvidence => ({
  practicalChecked: false, explanationCompared: false, liveModelAttempted: false, notes: ''
})

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function isEvidence(value: unknown): value is LessonEvidence {
  return isRecord(value) && typeof value.practicalChecked === 'boolean' &&
    typeof value.explanationCompared === 'boolean' && typeof value.liveModelAttempted === 'boolean' &&
    typeof value.notes === 'string'
}

/** Learner-reported evidence; no field implies automatic grading or live success. */
export class SelfChecks {
  static readonly storageKey = 'coding-agent-build-self-checks-v2'
  private values: Record<string, LessonEvidence> = {}
  private storage: () => ProgressStorage
  error = ''

  constructor(storage: () => ProgressStorage) {
    this.storage = storage
    try {
      const current = storage().getItem(SelfChecks.storageKey)
      const parsed: unknown = JSON.parse(current ?? storage().getItem('coding-agent-build-self-checks-v1') ?? '{}')
      if (!isRecord(parsed)) throw new Error('Invalid evidence')
      if (current !== null) {
        if (!Object.values(parsed).every(isEvidence)) throw new Error('Invalid evidence record')
        this.values = Object.fromEntries(Object.entries(parsed).map(([file, value]) => [file, { ...value as LessonEvidence }]))
      } else {
        // Old checkmarks cannot establish explanation comparison or a live attempt.
        this.values = Object.fromEntries(Object.entries(parsed).map(([file, value]) => [file, { ...emptyEvidence(), practicalChecked: value === true }]))
      }
    } catch {
      this.error = 'Your saved evidence could not be loaded. You can still work through every lesson.'
    }
  }

  evidence(file: string): LessonEvidence {
    return Object.prototype.hasOwnProperty.call(this.values, file) ? { ...this.values[file] } : emptyEvidence()
  }

  confirmed(file: string): boolean { return this.evidence(file).practicalChecked }

  set(file: string, confirmed: boolean): void { this.update(file, { practicalChecked: confirmed }) }

  update(file: string, changes: Partial<LessonEvidence>): void {
    this.values = { ...this.values, [file]: { ...this.evidence(file), ...changes } }
    try {
      this.storage().setItem(SelfChecks.storageKey, JSON.stringify(this.values))
      this.error = ''
    } catch {
      this.error = 'Your evidence is shown for now, but it will be lost when you reload the page.'
    }
  }

  summary(lessons: Lesson[]): Array<Lesson & LessonEvidence & { confirmed: boolean }> {
    return lessons.map(lesson => ({ ...lesson, ...this.evidence(lesson.file), confirmed: this.confirmed(lesson.file) }))
  }
}

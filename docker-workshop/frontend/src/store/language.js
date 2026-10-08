import { reactive } from 'vue'

/**
 * Lightweight reactive store for the selected backend language.
 * Persists the choice to sessionStorage so it survives page navigation.
 */

const STORAGE_KEY = 'workshop-selected-language'

const state = reactive({
  selected: sessionStorage.getItem(STORAGE_KEY) || null,
  available: []
})

export function initLanguageStore(languages, defaultLanguage) {
  state.available = languages || []
  if (!state.selected || !state.available.includes(state.selected)) {
    state.selected = defaultLanguage || state.available[0] || 'java'
    sessionStorage.setItem(STORAGE_KEY, state.selected)
  }
}

export function setLanguage(lang) {
  state.selected = lang
  sessionStorage.setItem(STORAGE_KEY, lang)
}

export function getLanguageState() {
  return state
}

/**
 * Build the backend API base URL for the currently selected language.
 * The hub proxies /api/** to the active backend, but when multiple
 * language backends exist the frontend service routes by language via
 * /api/lang/<language>/** or a query param — for now we expose a simple
 * helper that views can use to pass the language to requests.
 */
export function getSelectedLanguage() {
  return state.selected
}

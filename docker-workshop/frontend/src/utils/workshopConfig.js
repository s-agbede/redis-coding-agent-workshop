import { getBasePath } from './basePath.js'

/**
 * Workshop configuration loader.
 * 
 * Loads workshop.config.yaml from the public folder and provides
 * helper functions for phase navigation and configuration.
 */

let cachedConfig = null

/**
 * Strip inline comments from a YAML value
 */
function stripComment(value) {
  if (!value) return value
  // Handle inline comments - be careful of # inside quoted strings
  const hashIdx = value.indexOf('#')
  if (hashIdx > 0) {
    return value.substring(0, hashIdx).trim()
  }
  return value
}

/**
 * Simple YAML parser for workshop config
 * Handles nested objects, arrays, and basic scalar values
 */
function parseConfigYaml(yamlContent) {
  const config = {
    title: 'Workshop',
    subtitle: '',
    phases: {
      welcome: { enabled: true, title: 'Welcome' },
      review: { enabled: false, title: 'Review' },
      demo: { enabled: false, title: 'Demo' },
      build: { enabled: true, title: 'Workshop' }
    },
    demoPanel: {
      title: 'Interactive Panel',
      position: 'right',
      defaultWidth: 480,
      tabs: [],
      defaultTab: 'terminal',
      appUrl: '',
      appTitle: 'Application',
      redisInsightUrl: 'http://localhost:5540',
      terminalWebsocketUrl: ''
    },
    backend: {
      defaultLanguage: 'python',
      languages: ['python']
    }
  }

  const lines = yamlContent.split('\n')
  let currentSection = null
  let currentSubsection = null
  let currentPhase = null
  let currentTab = null
  let inTabsArray = false

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmed = line.trim()
    
    // Skip comments and empty lines
    if (!trimmed || trimmed.startsWith('#')) continue

    const indent = line.search(/\S/)
    
    // Top-level keys (indent 0)
    if (indent === 0 && trimmed.includes(':')) {
      const colonIdx = trimmed.indexOf(':')
      const key = trimmed.substring(0, colonIdx).trim()
      const value = trimmed.substring(colonIdx + 1).trim()
      if (value && !value.startsWith('#')) {
        config[key] = value
      } else {
        currentSection = key
        currentSubsection = null
        currentPhase = null
        inTabsArray = false
      }
    }
    // Section content (indent 2)
    else if (indent === 2 && currentSection) {
      const colonIdx = trimmed.indexOf(':')
      if (colonIdx > 0) {
        const key = trimmed.substring(0, colonIdx).trim()
        let value = stripComment(trimmed.substring(colonIdx + 1).trim())
        
        // Handle quoted strings
        if (value.startsWith('"') && value.endsWith('"')) {
          value = value.slice(1, -1)
        }
        // Handle null/empty values
        if (value === '~' || value === 'null') {
          value = ''
        }
        
        if (currentSection === 'phases') {
          if (!value) {
            currentPhase = key
            if (!config.phases[key]) {
              config.phases[key] = { enabled: true, title: key }
            }
          }
        } else if (currentSection === 'demoPanel') {
          if (key === 'tabs') {
            inTabsArray = true
            config.demoPanel.tabs = []
          } else if (key === 'defaultWidth') {
            config.demoPanel[key] = parseInt(value, 10)
          } else if (value) {
            config.demoPanel[key] = value
          } else {
            currentSubsection = key
          }
        } else if (currentSection === 'backend') {
          if (key === 'languages') {
            config.backend.languages = []
          } else if (value) {
            config.backend[key] = value
          }
        }
      }
      // Array item at indent 2 (for backend languages)
      else if (trimmed.startsWith('- ') && currentSection === 'backend') {
        config.backend.languages.push(trimmed.replace('- ', ''))
      }
    }
    // Phase/subsection properties (indent 4)
    else if (indent === 4) {
      if (currentSection === 'backend' && trimmed.startsWith('- ')) {
        config.backend.languages.push(trimmed.slice(2).trim())
      } else if (currentSection === 'phases' && currentPhase) {
        const colonIdx = trimmed.indexOf(':')
        if (colonIdx > 0) {
          const key = trimmed.substring(0, colonIdx).trim()
          const value = stripComment(trimmed.substring(colonIdx + 1).trim())
          if (key === 'enabled') {
            config.phases[currentPhase].enabled = value === 'true'
          } else if (key === 'title') {
            config.phases[currentPhase].title = value
          }
        }
      }
      // Tab array items
      else if (currentSection === 'demoPanel' && inTabsArray && trimmed.startsWith('- ')) {
        // Start of a new tab object
        const rest = trimmed.substring(2).trim()
        currentTab = {}
        config.demoPanel.tabs.push(currentTab)
        
        // Parse inline property (e.g., "- id: terminal")
        if (rest.includes(':')) {
          const colonIdx = rest.indexOf(':')
          const key = rest.substring(0, colonIdx).trim()
          let value = rest.substring(colonIdx + 1).trim()
          if (value.startsWith('"') && value.endsWith('"')) {
            value = value.slice(1, -1)
          }
          currentTab[key] = value
        }
      }
    }
    // Tab object properties (indent 6)
    else if (indent === 6 && currentSection === 'demoPanel' && inTabsArray && currentTab) {
      const colonIdx = trimmed.indexOf(':')
      if (colonIdx > 0) {
        const key = trimmed.substring(0, colonIdx).trim()
        let value = trimmed.substring(colonIdx + 1).trim()
        if (value.startsWith('"') && value.endsWith('"')) {
          value = value.slice(1, -1)
        }
        currentTab[key] = value
      }
    }
  }

  return config
}

/**
 * Load the workshop configuration
 */
export async function loadWorkshopConfig() {
  if (cachedConfig) {
    return cachedConfig
  }

  try {
    const basePath = getBasePath()
    const response = await fetch(`${basePath}/workshop.config.yaml`)
    
    if (!response.ok) {
      console.warn('workshop.config.yaml not found, using defaults')
      return getDefaultConfig()
    }
    
    const yamlContent = await response.text()
    cachedConfig = parseConfigYaml(yamlContent)
    return cachedConfig
  } catch (err) {
    console.warn('Failed to load workshop config:', err)
    return getDefaultConfig()
  }
}

/**
 * Get default configuration
 */
function getDefaultConfig() {
  return {
    title: 'Workshop',
    subtitle: '',
    phases: {
      welcome: { enabled: true, title: 'Welcome' },
      review: { enabled: false, title: 'Review' },
      demo: { enabled: false, title: 'Demo' },
      build: { enabled: true, title: 'Workshop' }
    },
    demoPanel: {
      title: 'Interactive Panel',
      position: 'right',
      defaultWidth: 480
    },
    backend: {
      defaultLanguage: 'python',
      languages: ['python']
    }
  }
}

/**
 * Get enabled phases as an array of { id, title, route }
 */
export function getEnabledPhases(config) {
  config = config || getDefaultConfig()
  const phaseOrder = ['welcome', 'review', 'demo', 'build']
  const routes = {
    welcome: '/',
    review: '/review',
    demo: '/demo',
    build: '/build'
  }

  return phaseOrder
    .filter(id => config.phases[id]?.enabled !== false)
    .map(id => ({
      id,
      title: config.phases[id]?.title || id.charAt(0).toUpperCase() + id.slice(1),
      route: routes[id]
    }))
}

/**
 * Get phase step titles for the header component
 */
export function getPhaseStepTitles(config) {
  return getEnabledPhases(config).map(p => p.title)
}

/**
 * Get the current phase index (1-based for header component)
 */
export function getCurrentPhaseIndex(config, currentPhaseId) {
  const phases = getEnabledPhases(config)
  const index = phases.findIndex(p => p.id === currentPhaseId)
  return index + 1
}

/**
 * Get the next enabled phase after the current one
 */
export function getNextPhase(config, currentPhaseId) {
  const phases = getEnabledPhases(config)
  const currentIndex = phases.findIndex(p => p.id === currentPhaseId)
  
  if (currentIndex < phases.length - 1) {
    return phases[currentIndex + 1]
  }
  return null
}

/**
 * Get the previous enabled phase before the current one
 */
export function getPreviousPhase(config, currentPhaseId) {
  const phases = getEnabledPhases(config)
  const currentIndex = phases.findIndex(p => p.id === currentPhaseId)
  
  if (currentIndex > 0) {
    return phases[currentIndex - 1]
  }
  return null
}

/**
 * Check if a phase is the last enabled phase
 */
export function isLastPhase(config, phaseId) {
  const phases = getEnabledPhases(config)
  return phases[phases.length - 1]?.id === phaseId
}

/**
 * Check if a phase is enabled
 */
export function isPhaseEnabled(config, phaseId) {
  return config.phases[phaseId]?.enabled !== false
}

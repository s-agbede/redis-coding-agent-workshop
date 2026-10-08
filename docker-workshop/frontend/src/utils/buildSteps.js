import { getBasePath } from './basePath.js'

/**
 * Loads build steps from static markdown files.
 * 
 * Steps are defined in /public/build-steps/manifest.yaml
 * Each step is a markdown file with YAML front-matter.
 */

/**
 * Parse YAML front-matter from markdown content
 */
function parseFrontMatter(content) {
  const frontMatterRegex = /^---\n([\s\S]*?)\n---\n([\s\S]*)$/
  const match = content.match(frontMatterRegex)
  
  if (!match) {
    return { metadata: {}, content: content }
  }
  
  const yamlStr = match[1]
  const markdownContent = match[2]
  
  // Simple YAML parser for our use case
  const metadata = {}
  const lines = yamlStr.split('\n')
  let currentKey = null
  let currentIndent = 0
  let nestedObj = null
  
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue
    
    const indent = line.search(/\S/)
    const keyMatch = trimmed.match(/^(\w+):\s*(.*)$/)
    
    if (keyMatch) {
      const [, key, value] = keyMatch
      
      if (indent === 0) {
        if (value) {
          metadata[key] = value
        } else {
          metadata[key] = {}
          currentKey = key
          nestedObj = metadata[key]
        }
        currentIndent = indent
      } else if (nestedObj && indent > currentIndent) {
        nestedObj[key] = value
      }
    }
  }
  
  return { metadata, content: markdownContent }
}

/**
 * Simple YAML parser for manifest.yaml
 */
function parseManifestYaml(yamlContent) {
  const steps = []
  const lines = yamlContent.split('\n')
  let currentStep = null
  
  for (const line of lines) {
    const trimmed = line.trim()
    
    // Skip comments and empty lines
    if (!trimmed || trimmed.startsWith('#')) continue
    
    // New step starts with "- file:"
    if (trimmed.startsWith('- file:')) {
      if (currentStep) steps.push(currentStep)
      currentStep = { file: trimmed.replace('- file:', '').trim() }
    } else if (currentStep && trimmed.startsWith('title:')) {
      currentStep.title = trimmed.replace('title:', '').trim()
    } else if (currentStep && trimmed.startsWith('description:')) {
      currentStep.description = trimmed.replace('description:', '').trim()
    }
  }
  
  if (currentStep) steps.push(currentStep)
  return { steps }
}

/**
 * Load the build steps manifest
 */
export async function loadBuildStepsManifest() {
  const basePath = getBasePath()
  const response = await fetch(`${basePath}/build-steps/manifest.yaml`)
  
  if (!response.ok) {
    throw new Error(`Failed to load build manifest: ${response.status}`)
  }
  
  const yamlContent = await response.text()
  return parseManifestYaml(yamlContent)
}

/**
 * Load a single build step markdown file
 */
export async function loadBuildStep(filename) {
  const basePath = getBasePath()
  const response = await fetch(`${basePath}/build-steps/${filename}`)
  
  if (!response.ok) {
    throw new Error(`Failed to load build step ${filename}: ${response.status}`)
  }
  
  const content = await response.text()
  const { metadata, content: markdownContent } = parseFrontMatter(content)
  
  return {
    ...metadata,
    content: markdownContent,
    file: filename
  }
}

/**
 * Load all build steps defined in the manifest
 */
export async function loadAllBuildSteps() {
  const manifest = await loadBuildStepsManifest()
  
  const steps = await Promise.all(
    manifest.steps.map(async (stepDef, index) => {
      try {
        const step = await loadBuildStep(stepDef.file)
        return {
          id: `build-step-${index}`,
          title: step.title || stepDef.title || `Step ${index + 1}`,
          description: step.description || stepDef.description || '',
          editorFile: step.editorFile || '',
          content: step.content || '',
          action: step.action || null,
          file: stepDef.file
        }
      } catch (err) {
        console.warn(`Failed to load build step ${stepDef.file}:`, err)
        return {
          id: `build-step-${index}`,
          title: stepDef.title || `Step ${index + 1}`,
          description: stepDef.description || '',
          content: `Failed to load: ${stepDef.file}`,
          action: null,
          file: stepDef.file
        }
      }
    })
  )
  
  return steps
}

/**
 * Convert markdown to HTML (basic implementation)
 */
import { markdownToHtml } from './markdown.js'
export { markdownToHtml }

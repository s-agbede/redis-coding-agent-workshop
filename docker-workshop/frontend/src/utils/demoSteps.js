import { getBasePath } from './basePath.js'

/**
 * Loads demo steps from static markdown files.
 * 
 * Steps are defined in /public/demo-steps/manifest.yaml
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
 * Load the demo steps manifest
 */
export async function loadDemoStepsManifest() {
  const basePath = getBasePath()
  const response = await fetch(`${basePath}/demo-steps/manifest.yaml`)
  
  if (!response.ok) {
    throw new Error(`Failed to load manifest: ${response.status}`)
  }
  
  const yamlContent = await response.text()
  return parseManifestYaml(yamlContent)
}

/**
 * Load a single demo step markdown file
 */
export async function loadDemoStep(filename) {
  const basePath = getBasePath()
  const response = await fetch(`${basePath}/demo-steps/${filename}`)
  
  if (!response.ok) {
    throw new Error(`Failed to load step ${filename}: ${response.status}`)
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
 * Load all demo steps defined in the manifest
 */
export async function loadAllDemoSteps() {
  const manifest = await loadDemoStepsManifest()
  
  const steps = await Promise.all(
    manifest.steps.map(async (stepDef) => {
      const step = await loadDemoStep(stepDef.file)
      return {
        id: stepDef.file.replace('.md', ''),
        title: step.title || stepDef.title,
        description: stepDef.description,
        editorFile: step.editorFile || '',
          content: step.content,
        action: step.action
      }
    })
  )
  
  return steps
}

/**
 * Convert markdown to HTML (basic implementation)
 * For production, consider using a library like marked or markdown-it
 */
import { renderMarkdown as markdownToHtml } from '../../../vendor/workshop-front-end-components/src/content-renderer/markdown.js'
export { markdownToHtml }

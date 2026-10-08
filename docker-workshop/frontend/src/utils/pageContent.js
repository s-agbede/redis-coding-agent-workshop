import { getBasePath } from './basePath.js'

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
  
  // Simple YAML parser
  const metadata = {}
  const lines = yamlStr.split('\n')
  let currentKey = null
  let currentList = null
  
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue
    
    // List item
    if (trimmed.startsWith('- ') && currentKey && currentList) {
      currentList.push(trimmed.slice(2).trim())
      continue
    }
    
    const keyMatch = trimmed.match(/^(\w+):\s*(.*)$/)
    if (keyMatch) {
      const [, key, value] = keyMatch
      if (value) {
        metadata[key] = value
        currentKey = null
        currentList = null
      } else {
        // Start of a list
        currentKey = key
        currentList = []
        metadata[key] = currentList
      }
    }
  }
  
  return { metadata, content: markdownContent }
}

/**
 * Convert markdown to HTML (basic implementation)
 */
import { markdownToHtml } from './markdown.js'
export { markdownToHtml }

/**
 * Load welcome page content from markdown file
 */
export async function loadWelcomeContent() {
  const basePath = getBasePath()
  const response = await fetch(`${basePath}/welcome.md`)
  
  if (!response.ok) {
    return null
  }
  
  const text = await response.text()
  const { metadata, content } = parseFrontMatter(text)
  
  return {
    title: metadata.title || 'Workshop',
    subtitle: metadata.subtitle || '',
    description: metadata.description || '',
    estimatedMinutes: parseInt(metadata.estimatedMinutes) || 30,
    difficulty: metadata.difficulty || 'Beginner',
    topics: metadata.topics || [],
    content: content,
    htmlContent: markdownToHtml(content)
  }
}

/**
 * Load review page content from markdown file
 */
export async function loadReviewContent() {
  const basePath = getBasePath()
  const response = await fetch(`${basePath}/review.md`)
  
  if (!response.ok) {
    return null
  }
  
  const text = await response.text()
  const { metadata, content } = parseFrontMatter(text)
  
  return {
    title: metadata.title || 'Review',
    content: content,
    htmlContent: markdownToHtml(content)
  }
}

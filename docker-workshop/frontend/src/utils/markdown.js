import { renderMarkdown } from '../../../vendor/workshop-front-end-components/src/content-renderer/markdown.js'
import { getBasePath } from './basePath.js'

export function markdownToHtml(content) {
  return renderMarkdown(content, { assetBasePath: getBasePath() })
}

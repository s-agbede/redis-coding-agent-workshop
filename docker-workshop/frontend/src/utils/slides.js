/** Split authored Markdown without treating separators inside examples as slides. */
export function splitSlides(markdown) {
  const slides = []
  let lines = [], fence = null
  for (const line of markdown.replace(/\r\n/g, '\n').split('\n')) {
    const marker = line.match(/^\s{0,3}(`{3,}|~{3,})(.*)$/)
    if (marker) {
      if (!fence) fence = marker[1]
      else if (marker[1][0] === fence[0] && marker[1].length >= fence.length && !marker[2].trim()) fence = null
    }
    if (!fence && /^\s*---\s*$/.test(line)) {
      if (lines.join('\n').trim()) slides.push(lines.join('\n').trim())
      lines = []
    } else lines.push(line)
  }
  if (lines.join('\n').trim()) slides.push(lines.join('\n').trim())
  return slides
}

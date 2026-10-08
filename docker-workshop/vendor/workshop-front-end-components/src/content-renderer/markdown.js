const BLOCKQUOTE_PATTERN = /^\s*>\s?/;
const HEADING_PATTERN = /^\s*(#{1,6})\s+(.+?)\s*$/;
const ORDERED_LIST_PATTERN = /^\s*\d+\.\s+/;
const UNORDERED_LIST_PATTERN = /^\s*[-*]\s+/;
const FENCE_PATTERN = /^\s*```([a-zA-Z0-9_-]*)\s*$/;
const DETAILS_PATTERN = /^\s*<details>\s*$/;

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function sanitizeUrl(url) {
  if (typeof url !== 'string') {
    return null;
  }

  const trimmed = url.trim();
  if (!/^https?:\/\//i.test(trimmed)) {
    return null;
  }

  return escapeHtml(trimmed);
}

function safeImagePath(path, assetBasePath) {
  // Static local assets only: no host, query, fragment, encoding or dot segments.
  if (!/^\/images\/(?:[a-zA-Z0-9_-]+\/)*[a-zA-Z0-9_-]+\.(?:svg|png|jpe?g|gif|webp)$/i.test(path)) return null;
  const base = assetBasePath.replace(/\/$/, '');
  if (base && !/^(?:\/[a-zA-Z0-9_-]+)+$/.test(base)) return null;
  return base + path;
}

function renderInlineMarkdown(text, options = {}) {
  const source = String(text || '');
  const plain = value => escapeHtml(value)
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>');
  const pattern = /`([^`]+)`|(!?)\[([^\]]*)\]\(([^)\s]+)\)/g;
  const tokens = [];
  // Keep code and generated attributes out of emphasis parsing. A prefix absent
  // from the source prevents literal Markdown text from impersonating a token.
  let tokenPrefix = '\u0000INLINE';
  while (source.includes(tokenPrefix)) tokenPrefix += '_';
  const protectedSource = source.replace(pattern, (_, code, image, label, path) => {
    let html;
    if (code !== undefined) {
      html = `<code>${escapeHtml(code)}</code>`;
    } else if (image === '!') {
      const src = safeImagePath(path, options.assetBasePath || '');
      html = src ? `<img src="${escapeHtml(src)}" alt="${escapeHtml(label)}" loading="lazy">` : escapeHtml(label);
    } else {
      const href = sanitizeUrl(path);
      html = href ? `<a href="${href}" target="_blank" rel="noopener noreferrer">${plain(label)}</a>` : plain(label);
    }
    const token = `${tokenPrefix}${tokens.length}\u0000`;
    tokens.push(html);
    return token;
  });
  // A single replacement pass never reparses restored code, labels or URLs.
  return plain(protectedSource).replace(new RegExp(`${tokenPrefix}(\\d+)\u0000`, 'g'), (_, index) => tokens[Number(index)]);
}

function tableCells(line) {
  const cells = [];
  let cell = '';
  let inCode = false;
  const source = line.trim().replace(/^\|/, '').replace(/\|$/, '');
  for (let index = 0; index < source.length; index += 1) {
    const character = source[index];
    if (character === '\\' && source[index + 1] === '|') { cell += '|'; index += 1; continue; }
    if (character === '`') inCode = !inCode;
    if (character === '|' && !inCode) { cells.push(cell.trim()); cell = ''; }
    else cell += character;
  }
  cells.push(cell.trim());
  return cells;
}

function isTableStart(lines, index) {
  if (!lines[index]?.includes('|') || !lines[index + 1]?.includes('|')) return false;
  const header = tableCells(lines[index]);
  const divider = tableCells(lines[index + 1]);
  return header.length === divider.length && divider.every(cell => /^:?-{3,}:?$/.test(cell));
}

function collectTable(lines, startIndex, options) {
  const headers = tableCells(lines[startIndex]);
  const rows = [];
  let index = startIndex + 2;
  while (index < lines.length && lines[index].trim() && lines[index].includes('|')) {
    const cells = tableCells(lines[index]);
    if (cells.length !== headers.length) break;
    rows.push(`<tr>${cells.map(cell => `<td>${renderInlineMarkdown(cell, options)}</td>`).join('')}</tr>`);
    index += 1;
  }
  return {
    html: `<div class="lesson-table" tabindex="0" role="region" aria-label="Lesson reference table"><table><thead><tr>${headers.map(cell => `<th scope="col">${renderInlineMarkdown(cell, options)}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`,
    nextIndex: index
  };
}

function collectParagraph(lines, startIndex, options) {
  const paragraphLines = [];
  let index = startIndex;

  while (index < lines.length) {
    const line = lines[index];
    if (
      !line.trim() ||
      isTableStart(lines, index) ||
      FENCE_PATTERN.test(line) ||
      DETAILS_PATTERN.test(line) ||
      HEADING_PATTERN.test(line) ||
      BLOCKQUOTE_PATTERN.test(line) ||
      ORDERED_LIST_PATTERN.test(line) ||
      UNORDERED_LIST_PATTERN.test(line)
    ) {
      break;
    }

    paragraphLines.push(line.trim());
    index += 1;
  }

  return {
    html: `<p>${renderInlineMarkdown(paragraphLines.join(' '), options)}</p>`,
    nextIndex: index
  };
}

function collectHeading(lines, startIndex, options) {
  const line = lines[startIndex];
  const match = line.match(HEADING_PATTERN);

  if (!match) {
    return null;
  }

  const level = Math.min(match[1].length, 6);
  const content = renderInlineMarkdown(match[2].trim(), options);

  return {
    html: `<h${level}>${content}</h${level}>`,
    nextIndex: startIndex + 1
  };
}

function collectList(lines, startIndex, ordered, options) {
  const pattern = ordered ? ORDERED_LIST_PATTERN : UNORDERED_LIST_PATTERN;
  const tag = ordered ? 'ol' : 'ul';
  const items = [];
  let index = startIndex;

  while (index < lines.length) {
    const line = lines[index];
    if (!pattern.test(line)) {
      break;
    }

    items.push(`<li>${renderInlineMarkdown(line.replace(pattern, '').trim(), options)}</li>`);
    index += 1;
  }

  return {
    html: `<${tag}>${items.join('')}</${tag}>`,
    nextIndex: index
  };
}

function collectBlockquote(lines, startIndex, options) {
  const quoteLines = [];
  let index = startIndex;

  while (index < lines.length) {
    const line = lines[index];
    if (!BLOCKQUOTE_PATTERN.test(line)) {
      break;
    }

    quoteLines.push(line.replace(BLOCKQUOTE_PATTERN, ''));
    index += 1;
  }

  return {
    html: `<blockquote>${renderMarkdown(quoteLines.join('\n'), options)}</blockquote>`,
    nextIndex: index
  };
}

export function renderMarkdown(markdown, options = {}) {
  if (!markdown) {
    return '';
  }

  const normalized = String(markdown).replace(/\r\n/g, '\n').trim();
  if (!normalized) {
    return '';
  }

  const lines = normalized.split('\n');
  const blocks = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }

    // Only this exact disclosure syntax is allowed; all other HTML stays escaped.
    if (DETAILS_PATTERN.test(line)) {
      index += 1;
      const summary = (lines[index] || '').match(/^\s*<summary>(.*?)<\/summary>\s*$/);
      if (summary) index += 1;
      const body = [];
      let depth = 1;
      let inFence = false;
      while (index < lines.length) {
        const current = lines[index];
        if (FENCE_PATTERN.test(current)) inFence = !inFence;
        if (!inFence && DETAILS_PATTERN.test(current)) depth += 1;
        if (!inFence && /^\s*<\/details>\s*$/.test(current)) depth -= 1;
        index += 1;
        if (depth === 0) break;
        body.push(current);
      }
      blocks.push(`<details><summary>${renderInlineMarkdown(summary ? summary[1] : 'Hint', options)}</summary>${renderMarkdown(body.join('\n'), options)}</details>`);
      continue;
    }

    const fence = line.match(FENCE_PATTERN);
    if (fence) {
      const code = [];
      index += 1;
      while (index < lines.length && !/^\s*```\s*$/.test(lines[index])) {
        code.push(lines[index]);
        index += 1;
      }
      blocks.push(`<pre><code class="language-${fence[1]}">${escapeHtml(code.join('\n'))}</code></pre>`);
      if (index < lines.length) index += 1;
      continue;
    }

    if (isTableStart(lines, index)) {
      const table = collectTable(lines, index, options);
      blocks.push(table.html);
      index = table.nextIndex;
      continue;
    }

    if (BLOCKQUOTE_PATTERN.test(line)) {
      const blockquote = collectBlockquote(lines, index, options);
      blocks.push(blockquote.html);
      index = blockquote.nextIndex;
      continue;
    }

    if (HEADING_PATTERN.test(line)) {
      const heading = collectHeading(lines, index, options);
      blocks.push(heading.html);
      index = heading.nextIndex;
      continue;
    }

    if (ORDERED_LIST_PATTERN.test(line)) {
      const list = collectList(lines, index, true, options);
      blocks.push(list.html);
      index = list.nextIndex;
      continue;
    }

    if (UNORDERED_LIST_PATTERN.test(line)) {
      const list = collectList(lines, index, false, options);
      blocks.push(list.html);
      index = list.nextIndex;
      continue;
    }

    const paragraph = collectParagraph(lines, index, options);
    blocks.push(paragraph.html);
    index = paragraph.nextIndex;
  }

  return blocks.join('');
}

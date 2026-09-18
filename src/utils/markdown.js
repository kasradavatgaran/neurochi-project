function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatInline(value) {
  return value
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    .replace(/\*([^*\n]+)\*/g, '<em>$1</em>')
    .replace(/_([^_\n]+)_/g, '<em>$1</em>');
}

export function renderMarkdown(value) {
  const escaped = escapeHtml(value).replace(/\r\n/g, '\n');
  const lines = escaped.split('\n');
  const output = [];
  let listItems = [];

  const flushList = () => {
    if (listItems.length) {
      output.push(`<ul>${listItems.join('')}</ul>`);
      listItems = [];
    }
  };

  for (const line of lines) {
    const bullet = line.match(/^\s*[-*]\s+(.+)$/);
    const numbered = line.match(/^\s*\d+[.)]\s+(.+)$/);
    const heading = line.match(/^\s*#{1,4}\s+(.+)$/);
    if (bullet || numbered) {
      listItems.push(`<li>${formatInline((bullet || numbered)[1])}</li>`);
    } else if (heading) {
      flushList();
      output.push(`<h4>${formatInline(heading[1])}</h4>`);
    } else {
      flushList();
      output.push(formatInline(line));
    }
  }
  flushList();
  return output.join('<br>');
}

function stripLegacyCitationMarkup(value) {
  let text = String(value || '');
  const citationStart = text.search(/<span\b[^>]*rag-source-citation|<a\b[^>]*rag-source-link|(?:&lt;|-)a\s+class\s*=\s*["'][^"']*rag-source-link/i);
  if (citationStart >= 0) {
    text = text.slice(0, citationStart);
  }
  text = text.replace(/(?:\([^()\n]{1,200}[،,]\s*[^()\n]{1,200}\)\s*)+$/u, '');
  text = text.replace(/(?:\[[^\]]+\]\(https?:\/\/[^)]+\)\s*)+$/i, '');
  return text
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/(?:&lt;|-)a\s+class\s*=\s*["'][^"']*rag-source-link[^>]*>[\s\S]*$/i, '')
    .trim();
}

function normalizeSources(sources) {
  if (!Array.isArray(sources)) return [];
  const seen = new Set();
  return sources.map((source) => ({
    title: String(source?.title || '').trim(),
    source_name: String(source?.source_name || source?.source || '').trim(),
    url: String(source?.url || '').trim(),
  })).filter((source) => {
    const key = `${source.url.toLowerCase()}|${source.title.toLowerCase()}|${source.source_name.toLowerCase()}`;
    if ((!source.title && !source.source_name && !source.url) || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function safeHttpUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.href : '';
  } catch {
    return '';
  }
}

export function renderSources(sources) {
  return normalizeSources(sources).map((source) => {
    const title = escapeHtml(source.title || source.source_name || 'منبع');
    const site = escapeHtml(source.source_name || source.url || 'منبع نامشخص');
    const url = safeHttpUrl(source.url);
    const linkedTitle = url
      ? `<a class="rag-source-link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${title}</a>`
      : title;
    return `<span class="rag-source-citation" dir="rtl">(${linkedTitle}<span class="rag-source-separator">،</span> <bdi class="rag-source-site" dir="auto">${site}</bdi>)</span>`;
  }).join(' | ');
}

export function renderMessage(value, sources = []) {
  const body = stripLegacyCitationMarkup(value);
  const renderedSources = renderSources(sources);
  return `${renderMarkdown(body)} ${renderedSources}`.trim();
}

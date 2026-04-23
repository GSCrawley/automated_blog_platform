/**
 * Utilities for converting HTML content ↔ editable block structures.
 * Blocks are the internal representation used by the preview editor.
 */

let _counter = 0;
function genId() {
  return `blk-${Date.now()}-${++_counter}`;
}

/**
 * Parse an HTML string into an array of content blocks.
 * @param {string} html
 * @returns {Array<Block>}
 */
export function parseHtmlToBlocks(html) {
  if (!html || !html.trim()) {
    return [{ id: genId(), type: 'paragraph', html: '', styles: {} }];
  }

  // Wrap in a container so DOMParser gives a clean body
  const parser = new DOMParser();
  const doc = parser.parseFromString(`<div id="root">${html}</div>`, 'text/html');
  const root = doc.getElementById('root');

  const blocks = [];

  function processNode(node) {
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    const tag = node.tagName.toLowerCase();

    // Headings
    if (/^h[1-6]$/.test(tag)) {
      blocks.push({
        id: genId(),
        type: 'heading',
        level: parseInt(tag[1], 10),
        text: node.textContent,
        styles: {},
      });
      return;
    }

    // Paragraph — check for embedded image
    if (tag === 'p') {
      const img = node.querySelector('img');
      if (img && node.textContent.trim() === '') {
        blocks.push({
          id: genId(),
          type: 'image',
          src: img.getAttribute('src') || '',
          alt: img.getAttribute('alt') || '',
          caption: '',
          styles: {},
        });
      } else if (node.innerHTML.trim()) {
        blocks.push({
          id: genId(),
          type: 'paragraph',
          html: node.innerHTML,
          styles: {},
        });
      }
      return;
    }

    // Standalone image
    if (tag === 'img') {
      blocks.push({
        id: genId(),
        type: 'image',
        src: node.getAttribute('src') || '',
        alt: node.getAttribute('alt') || '',
        caption: '',
        styles: {},
      });
      return;
    }

    // Figure with image
    if (tag === 'figure') {
      const img = node.querySelector('img');
      const caption = node.querySelector('figcaption');
      if (img) {
        blocks.push({
          id: genId(),
          type: 'image',
          src: img.getAttribute('src') || '',
          alt: img.getAttribute('alt') || '',
          caption: caption ? caption.textContent : '',
          styles: {},
        });
      }
      return;
    }

    // Lists
    if (tag === 'ul' || tag === 'ol') {
      const items = Array.from(node.querySelectorAll('li')).map(li => li.innerHTML);
      if (items.length) {
        blocks.push({
          id: genId(),
          type: 'list',
          ordered: tag === 'ol',
          items,
          styles: {},
        });
      }
      return;
    }

    // Blockquote
    if (tag === 'blockquote') {
      const cite = node.querySelector('cite');
      const text = cite
        ? node.innerHTML.replace(cite.outerHTML, '').trim()
        : node.innerHTML.trim();
      blocks.push({
        id: genId(),
        type: 'quote',
        text,
        cite: cite ? cite.textContent : '',
        styles: {},
      });
      return;
    }

    // Horizontal rule
    if (tag === 'hr') {
      blocks.push({ id: genId(), type: 'divider', styles: {} });
      return;
    }

    // Ad blocks (marked with data-ad or class="ad*")
    if (
      node.dataset.adType ||
      node.classList.contains('ad') ||
      node.classList.contains('ad-block') ||
      node.classList.contains('advertisement')
    ) {
      blocks.push({
        id: genId(),
        type: 'ad',
        adType: node.dataset.adType || 'banner',
        label: node.textContent.trim() || 'Advertisement',
        styles: {},
      });
      return;
    }

    // CTA link buttons
    if (
      tag === 'a' &&
      (node.classList.contains('cta') || node.classList.contains('cta-button'))
    ) {
      blocks.push({
        id: genId(),
        type: 'cta',
        text: node.textContent,
        href: node.getAttribute('href') || '#',
        styles: {},
      });
      return;
    }

    // Recurse into generic containers
    if (['div', 'section', 'article', 'main', 'aside'].includes(tag)) {
      Array.from(node.childNodes).forEach(processNode);
      return;
    }

    // Anything else: treat as raw HTML paragraph
    if (node.outerHTML.trim()) {
      blocks.push({
        id: genId(),
        type: 'paragraph',
        html: node.outerHTML,
        styles: {},
      });
    }
  }

  Array.from(root.childNodes).forEach(processNode);

  // Fallback: plain text was passed with no recognized tags
  if (blocks.length === 0) {
    blocks.push({ id: genId(), type: 'paragraph', html: html, styles: {} });
  }

  return blocks;
}

/**
 * Serialize an array of blocks back to an HTML string.
 * @param {Array<Block>} blocks
 * @returns {string}
 */
export function blocksToHtml(blocks) {
  return blocks
    .map(block => {
      const styleStr = stylesToCss(block.styles);
      const sa = styleStr ? ` style="${styleStr}"` : '';

      switch (block.type) {
        case 'heading':
          return `<h${block.level}${sa}>${escapeHtml(block.text)}</h${block.level}>`;

        case 'paragraph':
          return `<p${sa}>${block.html}</p>`;

        case 'image': {
          const caption = block.caption
            ? `<figcaption>${escapeHtml(block.caption)}</figcaption>`
            : '';
          return `<figure${sa}><img src="${escapeAttr(block.src)}" alt="${escapeAttr(block.alt)}" />${caption}</figure>`;
        }

        case 'list': {
          const tag = block.ordered ? 'ol' : 'ul';
          const items = (block.items || []).map(i => `<li>${i}</li>`).join('');
          return `<${tag}${sa}>${items}</${tag}>`;
        }

        case 'quote':
          return `<blockquote${sa}>${block.text}${block.cite ? `<cite>${escapeHtml(block.cite)}</cite>` : ''}</blockquote>`;

        case 'divider':
          return '<hr />';

        case 'ad':
          return `<div class="ad-block" data-ad-type="${escapeAttr(block.adType)}"${sa}>${escapeHtml(block.label || 'Advertisement')}</div>`;

        case 'cta':
          return `<a href="${escapeAttr(block.href || '#')}" class="cta-button"${sa}>${escapeHtml(block.text)}</a>`;

        default:
          return '';
      }
    })
    .filter(Boolean)
    .join('\n');
}

/**
 * Convert a styles object {camelCase: value} → CSS string.
 */
export function stylesToCss(styles = {}) {
  return Object.entries(styles)
    .map(([k, v]) => `${camelToKebab(k)}:${v}`)
    .join(';');
}

/**
 * Create a blank block of the given type with a fresh ID.
 */
export function createBlock(type) {
  const base = { id: genId(), type, styles: {} };
  switch (type) {
    case 'heading':
      return { ...base, level: 2, text: 'New Heading' };
    case 'paragraph':
      return { ...base, html: 'New paragraph text.' };
    case 'image':
      return { ...base, src: '', alt: '', caption: '' };
    case 'list':
      return { ...base, ordered: false, items: ['Item 1', 'Item 2'] };
    case 'quote':
      return { ...base, text: 'Quote text here.', cite: '' };
    case 'divider':
      return base;
    case 'ad':
      return { ...base, adType: 'banner', label: 'Advertisement' };
    case 'cta':
      return { ...base, text: 'Click Here', href: '#' };
    default:
      return { ...base, type: 'paragraph', html: '' };
  }
}

// ── helpers ─────────────────────────────────────────────────────────────────

function camelToKebab(str) {
  return str.replace(/([A-Z])/g, m => `-${m.toLowerCase()}`);
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function escapeAttr(str) {
  return String(str).replace(/"/g, '&quot;');
}

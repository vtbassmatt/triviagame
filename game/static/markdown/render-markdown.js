// copy of cleanUrl from marked's helpers.ts
const cleanUrl = function(href) {
  try {
    href = encodeURI(href).replace(/%25/g, '%');
  } catch {
    return null;
  }
  return href;
}

const renderer = {
  link({ href, title, tokens }) {
    const text = this.parser.parseInline(tokens);
    const cleanHref = cleanUrl(href);
    if (cleanHref === null) {
      return text;
    }
    href = cleanHref;
    let out = '<a href="' + href + '"';
    if (href.length >= 4 && href.substring(0, 4) == 'http') {
      out += ' target="_blank" rel="noopener noreferrer"';
    }
    if (title) {
      out += ' title="' + title + '"';
    }
    out += '>' + text + '</a>';
    return out;
  }
}

marked.use({ renderer });

function renderMarkdown(root) {
  htmx.findAll(root || document, ".markdown-needed").forEach(elm => {
    elm.innerHTML = DOMPurify.sanitize(
      marked.parseInline(elm.innerHTML),
      {ADD_ATTR: ['target']}
    );
    elm.classList.remove("markdown-needed");
  });
}

// htmx stuff
htmx.on("htmx:afterSwap", (e) => {
  renderMarkdown(e.detail.target);
})

// pageload
renderMarkdown();
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
  // closing </p> tag which we'll hunt for in the Markdown output
  const slashP = /<\/p>/;

  // BUG: findAll with a root doesn't seem to work reliably
  htmx.findAll(root || document, ".markdown-needed").forEach(elm => {
    // marked seems to add a trailing newline, which makes the math below less obvious
    const initialHtml = marked.parse(elm.innerHTML).trimEnd();

    // if the final </p> is the only </p>, drop the leading <p> and trailing </p>
    const finalHtml =
      initialHtml.search(slashP) == initialHtml.length - 4
      ? initialHtml.slice(3, -4)
      : initialHtml;

    elm.innerHTML = DOMPurify.sanitize(
      finalHtml,
      {ADD_ATTR: ['target']}
    );
    elm.classList.remove("markdown-needed");
  });
}

// htmx stuff
htmx.on("htmx:afterSwap", (e) => {
  renderMarkdown(/*e.detail.target*/);
})

// pageload
renderMarkdown();
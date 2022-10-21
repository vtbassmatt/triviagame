function renderMarkdown(root) {
  htmx.findAll(root || document, ".markdown-needed").forEach(elm => {
    elm.innerHTML = DOMPurify.sanitize(marked.parseInline(elm.innerHTML));
    elm.classList.remove("markdown-needed");
  });
}

// htmx stuff
htmx.on("htmx:afterSwap", (e) => {
  renderMarkdown(e.detail.target);
})

// pageload
renderMarkdown();
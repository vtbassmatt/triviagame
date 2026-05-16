function createMessage(message) {
  // clone template
  const elem = document.querySelector("[data-msg-template]").content.cloneNode(true);

  // update contents
  const wrapper = elem.querySelector("[data-msg-wrapper]");
  wrapper.className += " alert-" + message.tags;
  const body = elem.querySelector("[data-msg-body]");
  body.innerText = message.message;

  // add to page
  document.querySelector("[data-msg-container]").appendChild(elem);
}

htmx.on("messages", (e) => {
  e.detail.forEach(createMessage);
})
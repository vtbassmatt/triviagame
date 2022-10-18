function createMessage(message) {
  // clone template
  const elem = htmx.find("[data-msg-template").content.cloneNode(true);

  // update contents
  const wrapper = htmx.find(elem, "[data-msg-wrapper]");
  wrapper.className += " alert-" + message.tags;
  const body = htmx.find(elem, "[data-msg-body]");
  body.innerText = message.message;

  // add to page
  htmx.find("[data-msg-container]").appendChild(elem);
}

htmx.on("messages", (e) => {
  e.detail.value.forEach(createMessage);
})
const monacoWidgets = new Map();
window.addEventListener("message", ({ data }) => {
    switch(data.type) {
      case "change": {
        if (monacoWidgets.has(data.context)) {
          document.querySelector(`input[name='${data.context}']`).value = data.value;
        } else {
          console.log(`did not find a Monaco iframe for ${data.context}`);
        }
        break;
      }
    }
});
function wireUpMonaco(context, iframe) {
  if (!iframe) { throw new Error(`iframe ${iFrameID} not found`); }
  monacoWidgets.set(context, iframe);
  // turn off tab-trapping
  iframe.contentWindow.postMessage({ type: "change-options", options: {'tabFocusMode': true} }, "*");
}

const monacoWidgets = new Map();
window.addEventListener("message", ({ data }) => {
    switch(data.type) {
      case "change": {
        if (monacoWidgets.has(data.context)) {
          // console.log('has context!');
          document.querySelector(`input[name='${data.context}']`).value = data.value;
        }
        break;
      }
    }
});
function wireUpMonaco(context, iframe) {
  if (!iframe) { throw new Error(`iframe ${iFrameID} not found`); }
  monacoWidgets.set(context, iframe);
}

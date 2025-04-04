window.onload = function() {
    const editor = ace.edit("editor");
    editor.getSession().setMode("ace/mode/python");
    editor.setTheme("ace/theme/dracula");
    const template = document.getElementById("editor").dataset.template;
    if (template) editor.setValue(template, -1);
    editor.setOptions({
        fontSize: "14px",
        showPrintMargin: false,
        wrap: true,
        minLines: 15,
        maxLines: 15,
    });
};

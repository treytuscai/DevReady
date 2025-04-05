document.addEventListener("DOMContentLoaded", function() {
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

    const languageSelect = document.getElementById("language-select");

    editor.session.setValue(templates.python || "");
    editor.session.setMode("ace/mode/python");

    languageSelect.addEventListener("change", function(e) {
        const lang = e.target.value;
        editor.session.setValue(templates[lang] || "");

        let aceMode;
        switch (lang) {
            case "go":
                aceMode = "ace/mode/golang";
                break;
            case "js":
                aceMode = "ace/mode/javascript";
                break;
            case "ts":
                aceMode = "ace/mode/typescript";
                break;
            default:
                aceMode = "ace/mode/python";
        }
        editor.session.setMode(aceMode);
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const editor = ace.edit("editor");
    editor.getSession().setMode("ace/mode/python");
    editor.setTheme("ace/theme/vibrant_ink");

    const template = document.getElementById("editor").dataset.template;
    editor.setValue(template, -1);

    editor.setOptions({
        fontSize: "14px",
        showPrintMargin: false,
        wrap: true,
        minLines: 15,
        maxLines: 15,
    });

    const languageSelect = document.getElementById("language-select");

    languageSelect.addEventListener("change", function (e) {
        const lang = e.target.value;
        editor.session.setMode(getAceMode(lang));
    
        if (lang === "python" && template) {
            editor.setValue(template, -1); // use the one from dataset to prevent &gt
        } else {
            editor.setValue(templates[lang], -1);
        }
    });

    function getAceMode(lang) {
        switch (lang) {
            case "go": return "ace/mode/golang";
            case "js": return "ace/mode/javascript";
            case "ts": return "ace/mode/typescript";
            default: return "ace/mode/python";
        }
    }
});

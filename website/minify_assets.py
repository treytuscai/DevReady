"""Minifies .css and .js for the website."""
import os
from csscompressor import compress as compress_css
from jsmin import jsmin

def minify_css_file(file_path):
    with open(file_path, "r") as f:
        original = f.read()
    minified = compress_css(original)
    out_path = file_path.replace(".css", ".min.css")
    with open(out_path, "w") as f:
        f.write(minified)
    print(f"✅ Minified CSS: {out_path}")

def minify_js_file(file_path):
    with open(file_path, "r") as f:
        original = f.read()
    minified = jsmin(original)
    out_path = file_path.replace(".js", ".min.js")
    with open(out_path, "w") as f:
        f.write(minified)
    print(f"✅ Minified JS: {out_path}")

def walk_and_minify(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".css") and not file.endswith(".min.css"):
                minify_css_file(os.path.join(root, file))
            elif file.endswith(".js") and not file.endswith(".min.js"):
                minify_js_file(os.path.join(root, file))

if __name__ == "__main__":
    print("Minifying...")
    walk_and_minify("website/static")

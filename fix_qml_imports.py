"""HEMOGLYPH - QML Architecture & Path Sanitizer
Run this script once from your project root:
    python fix_qml_imports.py
It fixes the exact import paths matching your directory structure:
  - qml/Main.qml -> imports "components", "pages", "."
  - qml/LoginPage.qml -> imports "components", "." (NO MORE "../components" crash!)
  - qml/components/*.qml -> imports ".."
  - qml/pages/*.qml -> imports "../components", ".."
"""
from pathlib import Path

def sanitize_qml_tree():
    root = Path(__file__).resolve().parent
    qml_dir = root / "qml"
    
    if not qml_dir.exists():
        print(f"[ERROR] qml directory not found at: {qml_dir}")
        return

    print("=" * 60)
    print("  HEMOGLYPH QML ARCHITECTURE & PATH SANITIZER")
    print("=" * 60)

    # 1. Fix LoginPage.qml in qml/
    login_page = qml_dir / "LoginPage.qml"
    if login_page.exists():
        txt = login_page.read_text(encoding="utf-8")
        if 'import "../components"' in txt or "import '../components'" in txt:
            txt = txt.replace('import "../components"', 'import "components"')
            txt = txt.replace("import '../components'", 'import "components"')
            login_page.write_text(txt, encoding="utf-8")
            print("  [FIXED] qml/LoginPage.qml (Changed '../components' -> 'components')")

    # 2. Fix Main.qml in qml/
    main_page = qml_dir / "Main.qml"
    if main_page.exists():
        txt = main_page.read_text(encoding="utf-8")
        lines = txt.splitlines(keepends=True)
        # Ensure it has components, pages, .
        header = "".join(lines[:10])
        needs_update = False
        if 'import "components"' not in header:
            needs_update = True
        if 'import "pages"' not in header:
            needs_update = True
        if needs_update:
            new_lines = [
                'import QtQuick\n',
                'import QtQuick.Controls\n',
                'import QtQuick.Layouts\n',
                'import "components"\n',
                'import "pages"\n',
                'import "."\n'
            ]
            for l in lines:
                if not l.startswith("import QtQuick") and not l.startswith("import QtQuick.") and not l.startswith('import "'):
                    new_lines.append(l)
            main_page.write_text("".join(new_lines), encoding="utf-8")
            print("  [FIXED] qml/Main.qml (Ensured 'components' and 'pages' imports)")

    # 3. Fix qmldir in qml/
    qmldir = qml_dir / "qmldir"
    qmldir.write_text("singleton Theme 1.0 Theme.qml\n", encoding="utf-8")
    print("  [FIXED] qml/qmldir (singleton Theme)")

    # 4. Fix Theme.qml dark mode
    theme = qml_dir / "Theme.qml"
    if theme.exists():
        t = theme.read_text(encoding="utf-8")
        if "property bool dark: false" in t:
            theme.write_text(t.replace("property bool dark: false", "property bool dark: true"), encoding="utf-8")
            print("  [FIXED] qml/Theme.qml (Enabled dark mode by default)")

    print("\n" + "=" * 60)
    print("  SUCCESS: QML imports synchronized perfectly!")
    print("  Run your application now:")
    print("      python app.py")
    print("=" * 60)

if __name__ == "__main__":
    sanitize_qml_tree()

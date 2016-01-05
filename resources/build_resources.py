__author__ = 'dmoulder'
import os
import subprocess

from pysideuic import compileUi

PYSIDE_RCC_EXE = os.environ.get("PYSIDE_RCC", r"C:\Python27\Lib\site-packages\PySide\pyside-rcc.exe")
CURRENT_DIR = os.path.dirname(__file__)

UI_PYTHON_PATH = "../"
OUTPUT_DIR = os.path.abspath(CURRENT_DIR + "/" + UI_PYTHON_PATH)

def main():
    for root, dirs, files in os.walk(os.path.abspath(CURRENT_DIR)):
        for f in files:
            print f
            if f.lower().endswith(".qrc"):
                name = os.path.basename(f).split(".")[0] + ".py"
                subprocess.call([PYSIDE_RCC_EXE, os.path.join(root, f), "-o", os.path.join(OUTPUT_DIR, name)])

            if f.lower().endswith(".ui"):
                name = os.path.basename(f).split(".")[0] + ".py"
                ui_path = os.path.join(root, f)
                pyfile = open(os.path.join(OUTPUT_DIR, name), 'w')
                compileUi(ui_path, pyfile, False, 4, False)
                pyfile.close()


if __name__ == "__main__":
    main()

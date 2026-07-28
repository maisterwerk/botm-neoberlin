#!/usr/bin/env python3
"""Re-hides helper columns after the LibreOffice recalculation pass.

The pipeline is: build.py writes formulas -> LibreOffice recalculates and bakes cached values
(without which Apple Numbers shows a blank grid) -> this restores the hidden flags, which that
round-trip drops. Doing it in the XML keeps the cached values that re-saving through openpyxl
would throw away. A review caught the drift: build.py hid three helper columns and the shipped
file exposed two of them.
"""
import re, shutil, sys, zipfile
from xml.etree import ElementTree as ET

HIDE = {"Submissions": ["K", "L", "M"], "Leaderboard": ["N", "O"], "Next Best Move": ["N", "O", "P"]}
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R  = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
def idx(c):
    n = 0
    for ch in c: n = n*26 + (ord(ch)-64)
    return n

def patch(path):
    zin = zipfile.ZipFile(path)
    wb  = ET.fromstring(zin.read("xl/workbook.xml"))
    rels= ET.fromstring(zin.read("xl/_rels/workbook.xml.rels"))
    tgt = {r.get("Id"): r.get("Target") for r in rels}
    sheet_file = {}
    for sh in wb.iter(NS+"sheet"):
        t = tgt[sh.get(R+"id")]
        sheet_file[sh.get("name")] = "xl/" + t.lstrip("/").replace("worksheets/", "worksheets/")
    out = {}
    for name, cols in HIDE.items():
        f = sheet_file.get(name)
        if not f: continue
        xml = zin.read(f).decode("utf-8")
        for c in cols:
            i = idx(c)
            # widen an existing <col> definition that covers this column, else add one
            pat = re.compile(r'<col ([^>]*?)min="(\d+)"([^>]*?)max="(\d+)"([^>]*?)/>')
            done = False
            def repl(m):
                nonlocal done
                if done: return m.group(0)
                lo, hi = int(m.group(2)), int(m.group(4))
                if lo <= i <= hi and 'hidden="1"' not in m.group(0):
                    done = True
                    return m.group(0)[:-2] + ' hidden="1"/>'
                return m.group(0)
            xml2 = pat.sub(repl, xml)
            if not done:
                add = f'<col min="{i}" max="{i}" width="9" customWidth="1" hidden="1"/>'
                if "<cols>" in xml2:
                    xml2 = xml2.replace("<cols>", "<cols>"+add, 1)
                else:
                    xml2 = re.sub(r'(<sheetData)', "<cols>"+add+"</cols>"+r"\1", xml2, count=1)
            xml = xml2
        out[f] = xml.encode("utf-8")
    tmp = path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zin.infolist():
            zo.writestr(it, out.get(it.filename, zin.read(it.filename)))
    zin.close(); shutil.move(tmp, path)
    print("re-hid:", ", ".join(f"{k}!{'/'.join(v)}" for k,v in HIDE.items()))

if __name__ == "__main__":
    patch(sys.argv[1] if len(sys.argv)>1 else "BattleOfTheMinds_Scoreboard.xlsx")

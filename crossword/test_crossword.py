import json, sys
from playwright.sync_api import sync_playwright
URL = sys.argv[1] if len(sys.argv)>1 else "file:///Users/claude/Neo%202.0/projects/botm-artifacts/crossword/index.html"
P=[]
def t(name, ok, detail=""):
    P.append((name, ok, detail)); print(("PASS " if ok else "FAIL ")+name+("  "+detail if detail else ""))
with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(viewport={"width":1280,"height":720})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console."+m.type+": "+m.text) if m.type=="error" else None)
    pg.goto(URL); pg.wait_for_timeout(400)

    st = pg.evaluate("__selftest()")
    print(json.dumps(st["entries"], indent=1))
    t("1. grid built, 10 entries", len(st["entries"])==10, str(len(st["entries"])))
    t("2. every across & down entry is a DISTINCT word", st["distinct"] is True)
    t("3. every white square is checked both ways", st["unchecked"]==[], str(st["unchecked"]))
    t("4. clue list matches entry list exactly", st["errors"]==[], str(st["errors"]))
    exp={"1A":"MAP","4A":"ERROR","7A":"SCORE","8A":"SHOAL","9A":"FLY",
         "1D":"MESS","2D":"ARCH","3D":"PROOF","5D":"ORAL","6D":"RELY"}
    got={k:v["answer"] for k,v in st["entries"].items()}
    t("5. numbering + answers as designed", got==exp, str(got))

    # typing a real answer through the UI
    pg.evaluate("document.querySelector('[data-r=\"1\"][data-c=\"0\"]').dispatchEvent(new MouseEvent('mousedown',{bubbles:true}))")
    for ch in "ERROR": pg.keyboard.press(ch)
    row=pg.evaluate("__state().user[1]")
    t("6. typing fills the across entry left-to-right", row=="ERROR", row)

    # space toggles direction
    pg.evaluate("document.querySelector('[data-r=\"0\"][data-c=\"2\"]').dispatchEvent(new MouseEvent('mousedown',{bubbles:true}))")
    pg.keyboard.press(" ")
    bar=pg.inner_text("#cluebar")
    t("7. Space switches Across/Down", "Down" in bar, bar.replace("\n"," ")[:70])

    # wrong grid must be rejected
    ok=pg.evaluate("__autofill([2,0])")   # break the S of SCORE
    stt=pg.evaluate("__state()")
    t("8. one wrong square => rejected, marked red", ok is False and "wrong" in stt["status"], stt["status"])
    t("9. reveal banner stays hidden while wrong", stt["reveal"]!="block")

    # correct grid must be accepted
    pg.click("#bClear")
    ok=pg.evaluate("__autofill(null)")
    stt=pg.evaluate("__state()")
    t("10. correct grid => Solved", ok is True and "Solved" in stt["status"], stt["status"])
    t("11. theme reveal fires on solve", stt["reveal"]=="block")
    rv=pg.inner_text("#reveal")
    t("12. reveal names all three themers", all(w in rv for w in ("ERROR","SCORE","PROOF")))

    # reveal-word button
    pg.click("#bClear")
    pg.evaluate("document.querySelector('[data-r=\"0\"][data-c=\"2\"]').dispatchEvent(new MouseEvent('mousedown',{bubbles:true}))")
    pg.keyboard.press(" "); pg.click("#bWord")
    col="".join(pg.evaluate("__state().user")[r][2] for r in range(5))
    t("13. Reveal word fills the whole down entry", col=="PROOF", col)

    # clear
    pg.click("#bClear")
    rows=pg.evaluate("__state().user")
    t("14. Clear empties the grid", rows==["MAP##","ERROR","SCORE","SHOAL","##FLY"]
      .__class__(["...##",".....",".....",".....","##..."]), str(rows))

    t("15. no JS errors during the whole run", errs==[], "; ".join(errs[:3]))

    pg.click("#bClear"); pg.evaluate("__autofill(null)"); pg.wait_for_timeout(1400)
    pg.screenshot(path="solved.png")
    b.close()
n=sum(1 for _,o,_ in P if o)
print(f"\n{n}/{len(P)} passed")
sys.exit(0 if n==len(P) else 1)

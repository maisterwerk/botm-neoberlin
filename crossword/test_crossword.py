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
    exp={"1A":"TOP","4A":"EARNS","7A":"STOOL","8A":"THOSE","9A":"FED",
         "1D":"TEST","2D":"OATH","3D":"PROOF","5D":"NOSE","6D":"SLED"}
    got={k:v["answer"] for k,v in st["entries"].items()}
    t("5. numbering + answers as designed", got==exp, str(got))

    # typing a real answer through the UI
    pg.evaluate("document.querySelector('[data-r=\"1\"][data-c=\"0\"]').dispatchEvent(new MouseEvent('mousedown',{bubbles:true}))")
    for ch in "EARNS": pg.keyboard.press(ch)
    row=pg.evaluate("__state().user[1]")
    t("6. typing fills the across entry left-to-right", row=="EARNS", row)

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
    t("12. reveal names all three themers", all(w in rv for w in ("TEST","OATH","PROOF")))

    # reveal-word button
    pg.click("#bClear")
    pg.evaluate("document.querySelector('[data-r=\"0\"][data-c=\"2\"]').dispatchEvent(new MouseEvent('mousedown',{bubbles:true}))")
    pg.keyboard.press(" "); pg.click("#bWord")
    col="".join(pg.evaluate("__state().user")[r][2] for r in range(5))
    t("13. Reveal word fills the whole down entry", col=="PROOF", col)

    # clear
    pg.click("#bClear")
    rows=pg.evaluate("__state().user")
    t("14. Clear empties the grid", rows==["TOP##","EARNS","STOOL","THOSE","##FED"]
      .__class__(["...##",".....",".....",".....","##..."]), str(rows))


    # ---- regressions for defects a review found in the previous build ----
    pg.click("#bClear")
    pg.evaluate("__autofill([2,0])")            # break one square, mark it red
    pg.keyboard.press("ArrowRight")             # any redraw
    red=pg.eval_on_selector_all(".cell.wrong","els=>els.length")
    t("16. red mark survives a redraw", red==1, str(red))
    pg.evaluate("document.querySelector('[data-r=\"2\"][data-c=\"0\"]').dispatchEvent(new MouseEvent('mousedown',{bubbles:true}))")
    pg.keyboard.press("S")
    red=pg.eval_on_selector_all(".cell.wrong","els=>els.length")
    t("17. red mark clears when that square is edited", red==0, str(red))

    pg.click("#bClear"); pg.evaluate("__autofill(null)")
    t("18a. solved => theme panel open", pg.evaluate("__state().reveal")=="block")
    pg.evaluate("document.querySelector('[data-r=\"2\"][data-c=\"0\"]').dispatchEvent(new MouseEvent('mousedown',{bubbles:true}))")
    pg.keyboard.press("Backspace"); pg.keyboard.press("Q"); pg.click("#bCheck")
    t("18b. breaking a solved grid closes the theme panel again",
      pg.evaluate("__state().reveal")!="block", pg.evaluate("__state().reveal"))

    pg.click("#bClear")
    dots=pg.eval_on_selector_all(".cell.themer","els=>els.length")
    t("19a. themed squares NOT marked before the solve (no spoiler)", dots==0, str(dots))
    pg.evaluate("__autofill(null)")
    dots=pg.eval_on_selector_all(".cell.themer","els=>els.length")
    t("19b. themed squares marked after the solve", dots==13, str(dots))

    # mobile: no soft keyboard can appear without a focusable input
    pg.click("#bClear")
    has=pg.evaluate("!!document.getElementById('mob')")
    t("20a. an input exists so phones can raise a keyboard", has)
    pg.eval_on_selector('[data-r="0"][data-c="0"]', "el=>el.dispatchEvent(new MouseEvent('mousedown',{bubbles:true}))")
    t("20b. tapping a square focuses that input", pg.evaluate("document.activeElement.id")=="mob",
      pg.evaluate("document.activeElement.id"))
    if "Down" in pg.inner_text("#cluebar"): pg.keyboard.press(" ")   # aim at 1-Across
    for ch in "TOP":
        pg.evaluate("(c)=>{const m=document.getElementById('mob');m.value=c;m.dispatchEvent(new Event('input',{bubbles:true}))}", ch)
    t("20c. typing through that input fills the grid (phone path)",
      pg.evaluate("__state().user[0]")=="TOP##", pg.evaluate("__state().user[0]"))

    pg.click("#bClear")
    pg.focus("#bCheck"); pg.keyboard.press("Tab")
    t("21. Tab reaches the buttons instead of being swallowed",
      pg.evaluate("document.activeElement.tagName")=="BUTTON", pg.evaluate("document.activeElement.id"))

    # real-event coverage for the interactions the write-up claims
    pg.click("#bClear")
    pg.eval_on_selector('[data-r="1"][data-c="0"]', "el=>el.dispatchEvent(new MouseEvent('mousedown',{bubbles:true}))")
    if "Down" in pg.inner_text("#cluebar"): pg.keyboard.press(" ")   # aim at 4-Across
    for ch in "EARNS": pg.keyboard.press(ch)
    pg.keyboard.press("Backspace")
    a1=pg.evaluate("__state().user[1]")
    pg.keyboard.press("Backspace")
    b1=pg.evaluate("__state().user[1]")
    t("22. Backspace deletes, then steps back and deletes again", a1=="EARN." and b1=="EAR..", a1+" then "+b1)
    pg.click("#bClear")
    pg.evaluate("document.querySelector('[data-r=\"0\"][data-c=\"0\"]').dispatchEvent(new MouseEvent('mousedown',{bubbles:true}))")
    pg.click("#bLetter")
    t("23. Reveal letter fills exactly one correct square",
      pg.evaluate("__state().user[0]")=="T..##", pg.evaluate("__state().user[0]"))

    # a solved grid that is then EDITED (not re-Checked) must drop the theme panel and the dots
    pg.click("#bClear"); pg.evaluate("__autofill(null)")
    pg.evaluate("document.querySelector('[data-r=\"1\"][data-c=\"0\"]').dispatchEvent(new MouseEvent('mousedown',{bubbles:true}))")
    pg.keyboard.press("Backspace")
    st=pg.evaluate("__state()")
    dots=pg.eval_on_selector_all(".cell.themer","els=>els.length")
    t("25. Backspace on a solved grid closes the panel and hides the dots",
      st["reveal"]!="block" and st["done"] is False and dots==0,
      f'reveal={st["reveal"]} done={st["done"]} dots={dots}')

    # paste / swipe-typing delivers several characters in ONE input event
    pg.click("#bClear")
    pg.eval_on_selector('[data-r="1"][data-c="0"]',
        "el=>el.dispatchEvent(new MouseEvent('mousedown',{bubbles:true}))")
    if "Down" in pg.inner_text("#cluebar"): pg.keyboard.press(" ")   # aim at 4-Across
    assert "Across" in pg.inner_text("#cluebar")
    pg.eval_on_selector("#mob",
        "m=>{m.value='EARNS';m.dispatchEvent(new Event('input',{bubbles:true}))}")
    row=pg.evaluate("__state().user[1]")
    t("26. a multi-letter input event fills the whole entry, not just its last letter",
      row=="EARNS", row)

    # the opening cursor is a default, so the first click must select Across, not toggle to Down
    pg.reload(); pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('[data-r=\"0\"][data-c=\"0\"]').dispatchEvent(new MouseEvent('mousedown',{bubbles:true}))")
    t("27. the very first click selects Across, not Down",
      "Across" in pg.inner_text("#cluebar"), pg.inner_text("#cluebar").replace("\n"," ")[:40])

    # a focused button must be operable by keyboard, not just reachable
    pg.click("#bClear"); pg.focus("#bCheck")
    before=pg.inner_text("#cluebar")
    pg.keyboard.press(" ")
    t("29. Space on a focused button does not hijack the grid direction",
      pg.inner_text("#cluebar")==before, "cluebar changed")
    # the themed clue numbers must not be coloured before the puzzle is solved
    pg.reload(); pg.wait_for_timeout(300)
    hot=pg.eval_on_selector_all("li.themeclue .n",
      "els=>els.filter(e=>getComputedStyle(e).color.indexOf('163')>=0).length")
    t("30a. themed clue numbers not highlighted before the solve", hot==0, str(hot))
    pg.evaluate("__autofill(null)")
    hot=pg.eval_on_selector_all("li.themeclue .n",
      "els=>els.filter(e=>getComputedStyle(e).color.indexOf('163')>=0).length")
    t("30b. themed clue numbers highlighted after the solve", hot==3, str(hot))

    t("31. no JS errors during the whole run", errs==[], "; ".join(errs[:3]))

    pg.click("#bClear"); pg.evaluate("__autofill(null)"); pg.wait_for_timeout(1400)
    pg.screenshot(path="solved.png")
    b.close()
n=sum(1 for _,o,_ in P if o)
print(f"\n{n}/{len(P)} passed")
sys.exit(0 if n==len(P) else 1)

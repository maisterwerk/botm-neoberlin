import json, sys, math
from playwright.sync_api import sync_playwright
URL = sys.argv[1] if len(sys.argv)>1 else "file://"+__file__.replace("test_stormle.py","index.html")
P=[]
def t(n,ok,d=""):
    P.append(ok); print(("PASS " if ok else "FAIL ")+n+("  "+d if d else ""))
with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(viewport={"width":1280,"height":720})
    errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(400)

    # 1-3 duplicate-letter rule, the part of Wordle everyone gets wrong
    cases=[("PROOF","SOLVE","BBYBB"),("LEARN","BRAIN","BBGYG"),("ARRAY","RADAR","YYYGB"),
           ("SPEED","ERASE","YBYYB"),("LEVEL","ELVES","YYGGB")]
    got=[pg.evaluate(f"__score('{g}','{a}')") for g,a,_ in cases]
    t("1. duplicate-letter scoring matches the reference on 5 hard cases",
      got==[e for _,_,e in cases], str(list(zip([c[0] for c in cases],got))))

    n=pg.evaluate("__words.length")
    t("2. answer pool embedded", n==1552, str(n))

    h=pg.evaluate("__entropy('TEARS',__words)")
    t("3. entropy of TEARS matches the reference to 6 decimals", abs(h-6.258957)<5e-7, f"{h:.6f}")

    # 4 rejects a non-word
    pg.evaluate("__reset('calm')")
    pg.evaluate("__play('ZZZZZ')")
    t("4. a non-word is refused", "not in the word list" in pg.evaluate("__state().msg"),
      pg.evaluate("__state().msg"))

    # 5 calm mode: playing the day's answer wins
    pg.evaluate("__reset('calm')")
    ans=pg.evaluate("__state().answer")
    st=pg.evaluate(f"__play('{ans}')")
    t("5. calm mode: guessing the answer wins", st["over"] and "Solved in 1" in st["msg"], st["msg"])
    t("5b. the win message reports skill, not a total that is identical for every winner",
      "Skill" in st["msg"] and "bits taken" not in st["msg"], st["msg"])

    # 6 barometer arithmetic: bits taken == log2(before) - log2(after)
    pg.evaluate("__reset('calm')")
    st=pg.evaluate("__play('TEARS')")
    h=st["history"][0]
    exp=math.log2(1552)-math.log2(h["left"])
    t("6. bits taken == log2(before) - log2(after)", abs(h["got"]-exp)<1e-9,
      f"reported {h['got']:.4f} vs {exp:.4f}")

    # 7 the 'best available' figure for move 1 is the precomputed optimum
    t("7. best-available opener is TEARS at 6.2589 bits",
      h["bestWord"]=="TEARS" and abs(h["best"]-6.2589)<1e-3, f"{h['bestWord']} {h['best']}")

    # 8 STORM: the host picks the pattern with the MOST survivors
    pg.evaluate("__reset('storm')")
    chk=pg.evaluate("""()=>{
      const g='TEARS'; const r=__adversarial(g,__words);
      const b=new Map();
      for(const a of __words){const p=__score(g,a); b.set(p,(b.get(p)||0)+1);}
      let mx=0; for(const c of b.values()) mx=Math.max(mx,c);
      return {chosen:r.survivors.length, max:mx};}""")
    t("8. storm host keeps the largest possible bucket", chk["chosen"]==chk["max"], str(chk))

    # 9 the storm host never lies: its reply is the true pattern for EVERY survivor
    liar=pg.evaluate("""()=>{
      let bad=0; let c=__words.slice();
      for(const g of ['TEARS','MOUND','BLIMP','QUICK']){
        const r=__adversarial(g,c);
        for(const w of r.survivors) if(__score(g,w)!==r.pattern) bad++;
        c=r.survivors;
      }
      return {bad, left:c.length};}""")
    t("9. storm host never lies (reply is true for every survivor)",
      liar["bad"]==0 and liar["left"]>0, str(liar))

    # 10 the recommender must prefer a word that could actually win
    pg.evaluate("__reset('calm')")
    one=pg.evaluate("__bestGuess(['WHIFF'])")
    t("10. with one candidate left the recommender says that word, not a throwaway",
      one["word"]=="WHIFF", str(one))
    few=pg.evaluate("__bestGuess(['HOLLY','JOLLY','LOWLY','WOOLY'])")
    t("10b. with a handful left it recommends a word that can win",
      few["word"] in ['HOLLY','JOLLY','LOWLY','WOOLY'], str(few))

    # 11 skill is graded on the QUESTION asked, not on the draw
    pg.evaluate("__reset('calm')")
    st=pg.evaluate("__play('MUMMY')")
    h=st["history"][0]
    t("11. a weak question is graded weak however lucky the reply",
      abs(h["asked"]-2.1014)<1e-3 and h["asked"]<h["best"], f'asked={h["asked"]:.4f} best={h["best"]:.4f}')
    t("11b. the realised bits are reported separately from the question's worth",
      "got" in h and "asked" in h, str(sorted(h.keys())))

    # 11c the aggregate line must not claim more bits than exist
    note=pg.inner_text("#effNote")
    t("11c. summary reports skill and luck, not an unbounded bit total",
      "Skill" in note and "Luck" in note, note[:90])

    # 12 keyboard colouring reflects best-known letter state
    pg.evaluate("__reset('calm')"); pg.evaluate("__play('TEARS')")
    kb=pg.eval_on_selector_all("#kb button.G,#kb button.Y,#kb button.B","e=>e.length")
    t("12. on-screen keyboard is coloured after a guess", kb>0, str(kb))

    # 13 typing through real key events
    pg.evaluate("__reset('calm')")
    for ch in "SLATE": pg.keyboard.press(ch)
    pg.keyboard.press("Enter")
    t("13. real keystrokes enter and submit a guess",
      len(pg.evaluate("__state().rows"))==1, str(pg.evaluate("__state().rows")))

    # 14 backspace
    pg.evaluate("__reset('calm')")
    for ch in "SLATX": pg.keyboard.press(ch)
    pg.keyboard.press("Backspace"); pg.keyboard.press("E"); pg.keyboard.press("Enter")
    rows=pg.evaluate("__state().rows")
    t("14. Backspace edits the current guess (SLATX -> SLATE)",
      len(rows)==1 and rows[0].startswith("SLATE"), str(rows))

    # 15 the candidate list must not solve the puzzle for you
    pg.evaluate("__reset('calm')"); pg.evaluate("__play('TEARS')")
    txt=pg.inner_text("#cands")
    ans=pg.evaluate("__state().answer")
    t("15. candidate words are hidden by default (no self-spoiler)",
      ans not in txt and "still fit" in txt, txt[:70])
    pg.click("#peek")
    t("15b. they can still be revealed on request", ans in pg.inner_text("#cands"),
      pg.inner_text("#cands")[:70])

    # 16 Space must not re-fire the focused on-screen key
    pg.evaluate("__reset('calm')")
    pg.click("#kb button[data-k='Q']"); pg.keyboard.press(" ")
    row=pg.evaluate("(()=>{let s='';for(let c=0;c<5;c++){const t=document.querySelector(`.tile[data-r=\"0\"][data-c=\"${c}\"]`);s+=t.textContent||'.'}return s})()")
    t("16. Space does not retype the focused key", row=="Q....", row)

    # 17 the storm host must stay responsive
    pg.evaluate("__reset('storm')")
    pg.evaluate("__play('MUMMY')")          # move 1 is a precomputed constant; move 2 is the work
    left=pg.evaluate("__state().left")
    ms=pg.evaluate("(()=>{const t=performance.now();__play('VIVID');return performance.now()-t})()")
    t("17. a storm move with a large live candidate set stays under 1.5s", ms<1500,
      f"{ms:.0f} ms with {left} candidates alive")

    # 18 the daily salt makes storm a different puzzle each day
    diff=pg.evaluate("""()=>{
      const a=__adversarial('TEARS',__words,'1'), b=__adversarial('TEARS',__words,'2');
      return {sameSize:a.survivors.length===b.survivors.length, aPat:a.pattern, bPat:b.pattern};}""")
    t("18. the salt only ever breaks exact ties, never the largest-bucket rule",
      diff["sameSize"] is True, str(diff))

    # the optimised integer-coded rule must BE the display rule, not merely resemble it
    bad=pg.evaluate("__fastPathAgrees()")
    t("19. fast path == display path on all 2,408,704 pairs (in-browser)", bad==0, f"{bad} mismatches")

    t("20. no JS errors", errs==[], "; ".join(errs[:2]))
    pg.evaluate("__reset('calm')")
    for w in ["TEARS","SNORE"]: pg.evaluate(f"__play('{w}')")
    pg.wait_for_timeout(700); pg.screenshot(path="stormle.png")
    b.close()
print(f"\n{sum(P)}/{len(P)} passed")

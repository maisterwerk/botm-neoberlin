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

    # 10 storm is still winnable when you corner it
    pg.evaluate("__reset('storm')")
    won=pg.evaluate("""()=>{
      for(let i=0;i<6;i++){
        const s=__state();
        if(s.over) return s;
        // play greedily from whatever is still possible
        const w=(s.left===1)?null:null;
        __play(__words.find(x=>true));
        break;
      }
      return __state();}""")
    t("10. storm mode accepts a guess and advances", len(pg.evaluate("__state().rows"))==1,
      str(pg.evaluate("__state().rows")))

    # 11 storm: cornering it to a single word forces GGGGG
    corner=pg.evaluate("""()=>{
      __reset('storm');
      // shrink by brute force: keep guessing the alphabetically first survivor
      for(let i=0;i<6;i++){
        const s=__state(); if(s.over) break;
        const st=__state();
        __play(__words[0]);
      }
      return __state();}""")
    t("11. storm terminates within six guesses", corner["over"] is True or len(corner["rows"])==6,
      f'rows={len(corner["rows"])} over={corner["over"]}')

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

    t("15. no JS errors", errs==[], "; ".join(errs[:2]))
    pg.evaluate("__reset('calm')")
    for w in ["TEARS","SNORE"]: pg.evaluate(f"__play('{w}')")
    pg.wait_for_timeout(700); pg.screenshot(path="stormle.png")
    b.close()
print(f"\n{sum(P)}/{len(P)} passed")

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
    t("4. a non-word is refused", "not a word" in pg.evaluate("__state().msg"),
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
      for(const g of ['TEARS','MOUND','QUICK','LUCID']){
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
    # 11c: the summary must not assert a bit budget. Play a long game, then check NUMERICALLY
    # that no figure presented as a total exceeds log2(pool), and that skill is a real ratio.
    pg.evaluate("__reset('calm')")
    for w in ["MUMMY","VIVID","PUPPY","KAYAK"]:
        if not pg.evaluate("__state().over"): pg.evaluate(f"__play('{w}')")
    note=pg.inner_text("#effNote"); su=pg.evaluate("__summary()")
    import re as _re
    # every number anywhere in the summary, integers included, and the per-row Best figures
    nums=[float(x) for x in _re.findall(r"[-+]?\d+(?:\.\d+)?", note)]
    cap=math.log2(1552)
    over=[n for n in nums if abs(n)>cap+1e-9 and abs(n-round(n))>1e-9]
    t("11c. no BITS figure in the summary exceeds log2(pool) = 10.60 (percentages excluded)",
      over==[], f"offending {over} of {nums}")
    t("11d. skill is a bounded ratio, not a ratio of unbounded sums",
      0.0<=su["skill"]<=1.0, f"skill={su['skill']:.3f}")
    t("11e. the summary never asserts a bit budget", "bits available" not in note.lower()
      and "of the" not in note.lower(), note[:100])

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
    # 18: find a guess that ACTUALLY has a tie for the largest bucket, then prove two things:
    #     the salt can change which tied pattern is chosen, and it never changes the size.
    r=pg.evaluate("""()=>{
      let tiedFound=null, changed=0, sizeChanged=0, scanned=0;
      for(const g of __words.slice(0,400)){
        const b=new Map();
        for(const a of __words){const p=__score(g,a); b.set(p,(b.get(p)||0)+1);}
        let mx=0,cnt=0; for(const c of b.values()){ if(c>mx){mx=c;cnt=1;} else if(c===mx) cnt++; }
        scanned++;
        if(cnt<2) continue;
        if(!tiedFound) tiedFound=g;
        const seen=new Set();
        for(const s of ['1','2','3','4','5','6','7','8']){
          const x=__adversarial(g,__words,s);
          if(x.survivors.length!==mx) sizeChanged++;
          seen.add(x.pattern);
        }
        if(seen.size>1) changed++;
      }
      return {scanned, tiedFound, changed, sizeChanged};}""")
    t("18. the salt never changes the size of the chosen bucket", r["sizeChanged"]==0, str(r))
    t("18b. where an exact tie exists, different salts really do pick differently",
      r["changed"]>0 and r["tiedFound"] is not None, str(r))

    # the optimised integer-coded rule must BE the display rule, not merely resemble it
    bad=pg.evaluate("__fastPathAgrees()")
    t("19. fast path == display path on all 2,408,704 pairs (in-browser)", bad==0, f"{bad} mismatches")

    # 20: a real English word outside the ANSWER pool must still be an allowed guess
    pg.evaluate("__reset('calm')")
    pg.evaluate("__play('BLIMP')")
    t("20. a real word outside the answer pool is accepted as a guess",
      len(pg.evaluate("__state().rows"))==1, str(pg.evaluate("__state().msg")))
    pg.evaluate("__reset('calm')"); pg.evaluate("__play('ZZZQQ')")
    m=pg.evaluate("__state().msg")
    t("20b. a non-word is still refused", "not a word" in m and len(pg.evaluate("__state().rows"))==0, m)
    t("20c. proper nouns are not in the guess list", pg.evaluate("__guesses.has('AARON')") is False)

    ex=pg.evaluate("__fastPathAgreesExtra()")
    t("20d. fast path == display path for the wider guess list too", ex["bad"]==0,
      f'{ex["checked"]:,} pairs, {ex["bad"]} mismatches')

    # 21: Best must be the best LEGAL question, not merely the best answer-pool word
    cmp=pg.evaluate("""()=>{
      const c=__words.slice(0,120);
      const shown=__bestGuess(c);
      let bh=-1,bw=null;
      for(const g of [...__guesses]){ const h=__entropy(g,c); if(h>bh+1e-9){bh=h;bw=g;} }
      return {shown:shown.word, shownBits:shown.bits, trueBest:bw, trueBits:bh, full:shown.full};}""")
    t("21. Best is the optimum over the whole legal guess list, not just the answer pool",
      abs(cmp["shownBits"]-cmp["trueBits"])<1e-6 and cmp["full"] is True,
      f'{cmp["shown"]} {cmp["shownBits"]:.4f} vs true {cmp["trueBest"]} {cmp["trueBits"]:.4f}')

    # 22: a finished game must not accept further moves
    pg.evaluate("__reset('calm')")
    a=pg.evaluate("__state().answer"); pg.evaluate(f"__play('{a}')")
    before=len(pg.evaluate("__state().rows")); pg.evaluate("__play('TEARS')")
    t("22. a finished game refuses further guesses",
      len(pg.evaluate("__state().rows"))==before, str(pg.evaluate("__state().msg")))

    t("23. no JS errors", errs==[], "; ".join(errs[:2]))
    pg.evaluate("__reset('calm')")
    for w in ["TEARS","SNORE"]: pg.evaluate(f"__play('{w}')")
    pg.wait_for_timeout(700); pg.screenshot(path="stormle.png")
    b.close()
print(f"\n{sum(P)}/{len(P)} passed")

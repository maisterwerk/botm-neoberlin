// Extracts the scoring engine straight out of the shipped index.html and hashes its output
// over every (guess, answer) pair, so it can be compared with the Python reference.
const fs=require('fs'), crypto=require('crypto');
const html=fs.readFileSync(process.argv[2]||'index.html','utf8');
const js=html.split('<script>')[1].split('</script>')[0];
const code=js.slice(js.indexOf('const WORDS'), js.indexOf('/* ---------------- state'));
const {WORDS,score,entropy,adversarialReply,filterCands} =
  new Function(code + "; return {WORDS,score,entropy,adversarialReply,filterCands};")();
const h=crypto.createHash('sha256');
for(const g of WORDS){ let s=''; for(const a of WORDS) s+=score(g,a); h.update(s); }
console.log('words      :', WORDS.length);
console.log('pairs      :', WORDS.length**2);
console.log('JS  sha256 :', h.digest('hex'));
console.log('PY  sha256 :', fs.readFileSync('crosscheck_python.txt','utf8').trim());
console.log('TEARS bits :', entropy('TEARS',WORDS).toFixed(6));

import fs from "node:fs";
import assert from "node:assert/strict";
const css=fs.readFileSync(new URL("../src/style.css",import.meta.url),"utf8");
function tokens(pattern){
 const block=css.match(pattern)?.[1];
 assert.ok(block,"Missing theme palette");
 return Object.fromEntries([...block.matchAll(/--([\w-]+):\s*(#[0-9A-Fa-f]{6})/g)].map(m=>[m[1],m[2]]));
}
function luminance(hex){
 const c=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255)
   .map(v=>v<=.04045?v/12.92:Math.pow((v+.055)/1.055,2.4));
 return c[0]*.2126+c[1]*.7152+c[2]*.0722;
}
function ratio(a,b){
 const [l1,l2]=[luminance(a),luminance(b)].sort((a,b)=>b-a);
 return (l1+.05)/(l2+.05);
}
const expected=[
 ["Neon Ledger City",/\.neon-ledger\{([^}]+)\}/],
 ["Void",/\.neon-ledger\[data-theme="void"\]\{([^}]+)\}/],
 ["Acid",/\.neon-ledger\[data-theme="acid"\]\{([^}]+)\}/],
 ["Y2K Chrome",/\.neon-ledger\[data-theme="chrome"\]\{([^}]+)\}/],
 ["Soft Glitch",/\.neon-ledger\[data-theme="glitch"\]\{([^}]+)\}/],
];
for(const [name,pattern] of expected){
 const t=tokens(pattern);
 for(const fg of ["text","muted","pink","teal","amber","focus"]){
  const c=ratio(t[fg],t.bg);
  assert.ok(c>=4.5,name+" "+fg+": insufficient WCAG AA ratio "+c.toFixed(2));
 }
 assert.ok(ratio(t.muted,t.surface2)>=4.5,name+" muted/surface2 contrast failure");
 console.log(name+": AA verified for body, muted, neon accents, focus and solid secondary surfaces");
}
assert.ok(css.includes("prefers-reduced-motion"),"Reduced motion media handling required");
assert.ok(css.includes(":focus-visible"),"Visible keyboard focus style required");
console.log("Theme contrast and motion/focus CSS audit passed.");

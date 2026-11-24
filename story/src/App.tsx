import React,{useEffect,useRef,useState} from "react";
import {motion,useScroll,useSpring,useTransform,useReducedMotion} from "framer-motion";
import {Activity,ArrowDown,ArrowRight,BookOpen,ChevronDown,ChevronRight,ExternalLink,
 Gamepad2,Headphones,Info,Menu,Radio,Search,ShieldAlert,Smartphone,
 Sparkles,Volume2,VolumeX,X} from "lucide-react";
import {data} from "./data/data";
import {Entrance,OneTransaction,TheNetwork,TheUplift,ItDepends,AnalystQueue,PlotTwist} from "./ActOne";
import {WhyBreak,RetrainingLoop,StressTests,AnalystBudgets,Workbench,Takeaway} from "./ActTwo";
import {count,sourceUrl} from "./components/Common";

type Theme="neon"|"void"|"acid"|"chrome"|"glitch";
const STATIONS:{id:Theme;name:string;frequency:string}[]=[
 {id:"neon",name:"Neon Ledger City",frequency:"CITY FM"},
 {id:"void",name:"Void",frequency:"DARKWAVE"},
 {id:"acid",name:"Acid",frequency:"TERMINAL"},
 {id:"chrome",name:"Y2K Chrome",frequency:"FUTURE"},
 {id:"glitch",name:"Soft Glitch",frequency:"LATE NITE"},
];
const TIPS=[
 "Unknown labels are not negative examples.",
 "An Average Precision score is not classification accuracy.",
 "Transactions are nodes. Observed relationships are directed edges.",
 "All reported graph snapshots are taken at time-bucket close.",
 "A high risk score is not a probability of criminal guilt.",
 "The temporal failure is a measured finding—not a missing slide.",
 "Later adaptive replays use previously inspected periods.",
 "No new fraud outcomes are simulated in play mode.",
];
const KONAMI=["ArrowUp","ArrowUp","ArrowDown","ArrowDown","ArrowLeft","ArrowRight","ArrowLeft","ArrowRight","b","a"];
function goto(id:number){document.getElementById("chapter-"+id)?.scrollIntoView({behavior:window.matchMedia("(prefers-reduced-motion: reduce)").matches?"instant":"smooth",block:"start"});}
function PlayTone({active}:{active:boolean}){return null}
function Vortex({reduce}:{reduce:boolean}){
 const {scrollYProgress}=useScroll();
 const rotation=useTransform(scrollYProgress,[0,1],[0,160]);
 const scale=useTransform(scrollYProgress,[0,1],[1,1.8]);
 return <motion.svg aria-hidden className="vortex-background" viewBox="0 0 1000 1000" style={reduce?{}:{rotate:rotation,scale}}>
  {Array.from({length:8},(_,i)=><ellipse key={i} cx="500" cy="500" rx={100+i*65} ry={63+i*65} fill="none" stroke="currentColor" strokeWidth={i===0?2:1} strokeDasharray={i%2?"12 12":"7 25"} opacity={.2-i*.017} transform={"rotate("+(i*17)+" 500 500)"}/>)}
 </motion.svg>;
}
function TipCard({active}:{active:boolean}){
 const [tip,setTip]=useState(0);
 useEffect(()=>{if(!active)return;const timer=window.setInterval(()=>setTip(v=>(v+1)%TIPS.length),6000);return()=>clearInterval(timer);},[active]);
 return <div className="tip-card" role="status" aria-live="polite"><span>LEDGER TIP</span><p>{TIPS[tip]}</p></div>;
}
function Phone({close}:{close:()=>void}){
 const first=useRef<HTMLButtonElement>(null);
 useEffect(()=>{first.current?.focus();const onKey=(e:KeyboardEvent)=>{if(e.key==="Escape")close();};document.addEventListener("keydown",onKey);return()=>document.removeEventListener("keydown",onKey)},[close]);
 return <div className="overlay" role="presentation" onMouseDown={close}><div role="dialog" aria-modal="true" aria-label="FraudGraph researcher phone" className="research-phone" onMouseDown={e=>e.stopPropagation()}>
  <div className="phone-toolbar"><span>THE LEDGER / LINKS</span><button ref={first} aria-label="Close research phone" onClick={close}><X size={19}/></button></div><div className="phone-screen-head"><Smartphone size={27}/><h2>Research hotline</h2><p>All roads lead back to source evidence.</p></div>
  <a href={data.repository} target="_blank" rel="noreferrer">GitHub repository <ExternalLink size={16}/></a>
  <a href={data.repository+"/tree/main/notebooks"} target="_blank" rel="noreferrer">Research notebooks <ExternalLink size={16}/></a>
  <a href={data.repository+"/tree/main/app"} target="_blank" rel="noreferrer">Original Investigator <ExternalLink size={16}/></a>
  <a href="https://github.com/git-disl/EllipticPlusPlus" target="_blank" rel="noreferrer">Original Elliptic++ source <ExternalLink size={16}/></a>
  <div className="phone-disclaimer">No wallet lookup. No criminality verdict. A research case file, with receipts.</div>
 </div></div>;
}
function EvidenceVault({close}:{close:()=>void}){
 const closeRef=useRef<HTMLButtonElement>(null);
 useEffect(()=>{closeRef.current?.focus();const onKey=(e:KeyboardEvent)=>{if(e.key==="Escape")close();};document.addEventListener("keydown",onKey);return()=>document.removeEventListener("keydown",onKey)},[close]);
 const items=[
  {name:"Raw data, SHA hashes, class imbalance",path:data.evidenceIndex.dataIntegrity,detail:"Source files checked; missing attributes retained. Original Elliptic++ labels are only selectively known."},
  {name:"Chronological split + leakage audit",path:data.evidenceIndex.leakageAudit,detail:"Preprocessing fit on training data, labels stay unknown, graph features frozen at bucket close."},
  {name:"Graph properties and cohort signatures",path:data.evidenceIndex.graphTopology,detail:"All edges inside a time bucket; component size and density can encode the period."},
  {name:"Original model comparisons",path:"reports/results.csv",detail:"All named and extended, logistic and XGBoost transaction-only / graph comparisons."},
  {name:"Paired bootstrap uncertainty",path:"reports/paired_comparison.json",detail:"Paired by test time bucket; limited independent periods."},
  {name:"Permutation reliance / TreeSHAP",path:"reports/permutation_importance.csv",detail:"Models rely heavily on transaction size; contributions aren't causal."},
  {name:"Shuffled-label negative control",path:"reports/negative_control.json",detail:"A post-hoc diagnostic, not proof of no leakage."},
  {name:"Duplicate and complete-case sensitivity",path:"reports/robustness.csv",detail:"Main AP is similar after these exclusions; not a guarantee of transfer."},
  {name:"Risk-band thresholds vs top-K",path:data.evidenceIndex.decisionFramework,detail:"Fixed score thresholds are distinct from true analyst-capacity constraints."},
  {name:"Original step-by-step failure",path:"reports/test_by_time.csv",detail:"Deterioration around step 43 across multiple models."},
  {name:"Temporal drift, ablations and replay",path:data.evidenceIndex.temporalProtocol,detail:"PSI, Wasserstein, score drift, label prevalence, and exploratory adaptive replay."},
  {name:"Model complexity and delay sensitivity",path:data.evidenceIndex.regularizationProtocol,detail:"Under/overfit diagnostics, fixed validation criteria, scenario label lags, review budgets."},
  {name:"Reproducibility and SQL parity",path:"reports/EXECUTION_NOTES.md",detail:"Original executed notebooks and SQL graph-degree parity; research artifact provenance."},
  {name:"Existing Investigator prototype vs future roadmap",path:data.evidenceIndex.analystRoadmap,detail:"Retrospective React investigator built; live wallet lookup and service deployment remain roadmap."},
 ];
 return <div className="overlay" role="presentation" onMouseDown={close}><div className="evidence-vault" role="dialog" aria-modal="true" aria-label="Evidence vault" onMouseDown={e=>e.stopPropagation()}>
  <div className="vault-head"><div><span className="eyebrow">SOURCE TRANSPARENCY / AUDIT</span><h2>Evidence vault</h2><p>Click through to the underlying project artifacts. Unobserved outcomes are never invented.</p></div><button ref={closeRef} onClick={close} aria-label="Close evidence vault"><X size={20}/></button></div>
  <div className="vault-list">{items.map((item,i)=><a key={item.path} href={sourceUrl(item.path)} target="_blank" rel="noreferrer"><span className="vault-index">{String(i+1).padStart(2,"0")}</span><div><strong>{item.name}</strong><p>{item.detail}</p></div><ExternalLink size={15}/></a>)}</div>
  <div className="vault-footer">All numeric research results are generated from original source reports and completed experimental artifacts into a single typed data.ts file.</div>
 </div></div>;
}
export default function App(){
 const [theme,setTheme]=useState<Theme>("neon");
 const [play,setPlay]=useState(true);
 const [active,setActive]=useState(0);
 const [radioOpen,setRadioOpen]=useState(false);
 const [phone,setPhone]=useState(false);
 const [vault,setVault]=useState(false);
 const [navOpen,setNavOpen]=useState(false);
 const [chaos,setChaos]=useState(false);
 const [sound,setSound]=useState(false);
 const [logoClicks,setLogoClicks]=useState(0);
 const [tipOpen,setTipOpen]=useState(true);
 const reduce=Boolean(useReducedMotion());
 const {scrollYProgress}=useScroll();
 const progress=useSpring(scrollYProgress,{stiffness:110,damping:27});
 const soundCtx=useRef<AudioContext|null>(null);
 const seq=useRef<string[]>([]);
 useEffect(()=>{
  const sections=[...document.querySelectorAll<HTMLElement>("[data-chapter]")];
  const observer=new IntersectionObserver(entries=>{
   const visible=entries.filter(x=>x.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];
   if(visible)setActive(Number((visible.target as HTMLElement).dataset.chapter));
  },{rootMargin:"-26% 0px -34% 0px",threshold:[0,.2,.4,.7]});
  sections.forEach(el=>observer.observe(el));
  return()=>observer.disconnect();
 },[]);
 useEffect(()=>{
  const listener=(event:KeyboardEvent)=>{
   seq.current=[...seq.current,event.key].slice(-KONAMI.length);
   if(seq.current.join("|").toLowerCase()===KONAMI.join("|").toLowerCase()){setChaos(v=>!v);seq.current=[];}
   if(event.key==="Escape"){setRadioOpen(false);setPhone(false);setVault(false);setNavOpen(false);}
  };
  window.addEventListener("keydown",listener);return()=>window.removeEventListener("keydown",listener);
 },[]);
 useEffect(()=>{
  const handler=(event:PointerEvent)=>{
   if(event.pointerType!=="mouse")return;
   document.documentElement.style.setProperty("--cursor-x",event.clientX+"px");
   document.documentElement.style.setProperty("--cursor-y",event.clientY+"px");
  };
  window.addEventListener("pointermove",handler,{passive:true});
  return()=>window.removeEventListener("pointermove",handler);
 },[]);
 const tone=()=>{
  if(!sound)return;
  try{
   const ctx=soundCtx.current||new AudioContext();soundCtx.current=ctx;
   const oscillator=ctx.createOscillator(),gain=ctx.createGain();
   oscillator.type="sine";oscillator.frequency.value=440;
   gain.gain.setValueAtTime(.03,ctx.currentTime);
   gain.gain.exponentialRampToValueAtTime(.001,ctx.currentTime+.09);
   oscillator.connect(gain).connect(ctx.destination);
   oscillator.start();oscillator.stop(ctx.currentTime+.095);
  }catch{}
 };
 const navigate=(id:number)=>{goto(id);setNavOpen(false);tone();};
 const clickLogo=()=>{setLogoClicks(v=>{if(v+1>=5){setChaos(x=>!x);return 0;}return v+1;});};
 const chapters=[
  <Entrance onEnter={()=>navigate(1)} play={play}/>,<OneTransaction/>,<TheNetwork/>,<TheUplift/>,
  <ItDepends/>,<AnalystQueue/>,<PlotTwist play={play}/>,<WhyBreak/>,<RetrainingLoop play={play}/>,
  <StressTests play={play}/>,<AnalystBudgets play={play}/>,<Workbench/>,<Takeaway/>
 ];
 return <div className={"neon-ledger "+(play?"mode-play":"mode-read")+(chaos?" chaos-mode":"")} data-theme={theme}>
   <Vortex reduce={reduce}/><div className="scanline-layer" aria-hidden/><div className="cursor-glow" aria-hidden/>
   <motion.div className="top-progress" style={{scaleX:progress}}/>
   <header className="hud"><button className="brand-button" onClick={clickLogo} aria-label="FraudGraph logo. Click repeatedly for hidden theme." title="FraudGraph">
      <span className="brand-icon">◈</span><span>FRAUD<span>GRAPH</span></span></button>
      <div className="hud-center"><span>CASE FILE</span><strong>{String(active).padStart(2,"0")} / {String(data.chapters.length-1).padStart(2,"0")}</strong><span className="hud-divider"/> <span>{data.chapters[active]?.name}</span></div>
      <div className="hud-tools"><button className="hud-icon" aria-label="Show evidence vault" onClick={()=>setVault(true)} title="Evidence"><BookOpen size={18}/></button>
       <button className="hud-icon" aria-label="Open research phone" onClick={()=>setPhone(true)} title="Research links"><Smartphone size={18}/></button>
       <div className="radio-wrapper"><button className="radio-button" aria-expanded={radioOpen} onClick={()=>setRadioOpen(v=>!v)}><Radio size={16}/> {STATIONS.find(s=>s.id===theme)?.frequency} <ChevronDown size={14}/></button>
       {radioOpen&&<div className="radio-popup"><span>THEME RADIO / NO TRACKING</span>{STATIONS.map(s=><button key={s.id} aria-pressed={theme===s.id} onClick={()=>{setTheme(s.id);setRadioOpen(false);tone();}}><i className={"station-dot "+s.id}/><b>{s.name}</b><small>{s.frequency}</small></button>)}<button onClick={()=>setSound(x=>!x)}><span>{sound?<Volume2 size={16}/>:<VolumeX size={16}/>}</span><b>UI tones</b><small>{sound?"ON":"OFF"}</small></button></div>}</div>
       <button className="hud-icon mobile-menu" aria-label="Open chapter navigation" onClick={()=>setNavOpen(true)}><Menu size={21}/></button>
      </div>
   </header>
   <aside className={"chapter-nav "+(navOpen?"open":"")} aria-label="Chapter navigation">
      <div className="nav-heading"><span>THE DESCENT</span><button onClick={()=>setNavOpen(false)} className="nav-close" aria-label="Close chapters"><X size={17}/></button></div>
      <div className="nav-scroll">{data.chapters.map(ch=><button key={ch.id} onClick={()=>navigate(ch.id)} className={"nav-chapter "+(active===ch.id?"active":"")} aria-current={active===ch.id?"step":undefined}><span className="nav-bullet"/><span>{String(ch.id).padStart(2,"0")}</span><strong>{ch.name}</strong></button>)}</div>
      <div className="nav-settings"><button aria-pressed={play} onClick={()=>setPlay(v=>!v)}><Gamepad2 size={16}/> {play?"Play mode":"Read mode"} <span>SWITCH</span></button><button onClick={()=>navigate(Math.min(active+1,data.chapters.length-1))}>Skip ahead <ArrowRight size={14}/></button></div>
   </aside>
   <div className="corner-minimap" role="img" aria-label={"Current chapter "+String(active)+": "+data.chapters[active]?.name}><div className="minimap-rings"><span/><span/><span/><i/></div><small>DEPTH {String(active).padStart(2,"0")}</small></div>
   <main id="story-main">{data.chapters.map((chapter,index)=><section key={chapter.id} id={"chapter-"+chapter.id} data-chapter={chapter.id} className={"chapter chapter-"+chapter.id+(chapter.id===0?" hero-chapter":"")} aria-label={"Chapter "+chapter.id+": "+chapter.name}>
      {chapters[index]}{index>0&&index<data.chapters.length-1&&<div className="chapter-end"><span>{play?"MISSION FILE":"RESEARCH CHAPTER"} {String(index).padStart(2,"0")} / {chapter.name}</span><button onClick={()=>navigate(index+1)}>DESCEND DEEPER <ArrowDown size={14}/></button></div>}
   </section>)}</main>
   {tipOpen&&active===0&&<div className="tip-wrapper"><TipCard active={active===0}/><button aria-label="Dismiss loading tip" onClick={()=>setTipOpen(false)}><X size={15}/></button></div>}
   <footer className="site-footer"><span>FraudGraph / Neon Ledger City</span><span>Historical ML study. No live wallet checker or guilt verdicts.</span><a href={data.repository} target="_blank" rel="noreferrer">View source <ExternalLink size={13}/></a></footer>
   {phone&&<Phone close={()=>setPhone(false)}/>}
   {vault&&<EvidenceVault close={()=>setVault(false)}/>}
  </div>;
}

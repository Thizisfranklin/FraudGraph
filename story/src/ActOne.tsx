import React,{useState} from "react";
import {motion} from "framer-motion";
import {ArrowDown,ArrowDownRight,ScanEye,ShieldAlert} from "lucide-react";
import {data} from "./data/data";
import {NetworkMap} from "./components/NetworkMap";
import {DepthCard,Fact,ResearchNote,SceneHint,SectionTitle,SelectChips,m,count,pct,EMPTY} from "./components/Common";

function example(){
 const original=data.originalCases.find(c=>c.case==="graph_uplift");
 return data.investigator.find(c=>c.id===String(original?.txId))||data.investigator[0];
}
export function Entrance({onEnter,play}:{onEnter:()=>void;play:boolean}){
 return <div className="entrance-scene">
 <div className="sky-art" aria-hidden="true"><div className="grain-sun"/><div className="sky-cloud cloud-1"/><div className="sky-cloud cloud-2"/>
 <svg className="skyline" viewBox="0 0 1000 350" preserveAspectRatio="xMidYMax slice"><path fill="#1c1742" d="M0 230h42V130h33v90h23V80h30v140h31v-40h32V90h31v140h36V145h30v80h20V60h28v170h37V120h34v110h24V165h35V98h25v130h33V80h35v140h20V160h31v65h25V112h40v113h28V65h38v160h25V120h37v105h20V180h30V88h42v150h26V150h24v80h25V120h37v110h25V174h38v180H0Z"/><path fill="#120f29" d="M0 290h65v-60h45v40h40v-80h33v100h50V235h35v75h60v-84h35v65h37v-42h35v60h42v-80h40v75h35v-95h49v85h30v-62h35v90h56v-100h35v70h52v-42h30v60h60v-130h35v110h35v-70h45v100h30v-48h48v90H0Z"/></svg>
 <svg className="palm palm-left" viewBox="0 0 160 300"><path d="M82 290Q70 154 83 76" stroke="#080c20" strokeWidth="12" fill="none"/><g fill="none" stroke="#080c20" strokeWidth="18" strokeLinecap="round"><path d="M81 76Q30 36 8 80"/><path d="M81 76Q12 5 6 22"/><path d="M81 76Q70 0 44 7"/><path d="M81 76Q129 8 151 29"/><path d="M81 76Q139 56 152 102"/><path d="M81 76Q103 22 89 6"/></g></svg>
 <svg className="palm palm-right" viewBox="0 0 160 300"><path d="M82 290Q92 160 78 76" stroke="#080c20" strokeWidth="12" fill="none"/><g fill="none" stroke="#080c20" strokeWidth="18" strokeLinecap="round"><path d="M78 76Q22 30 10 78"/><path d="M78 76Q5 8 6 29"/><path d="M78 76Q63 0 40 6"/><path d="M78 76Q140 10 152 25"/><path d="M78 76Q151 60 153 106"/><path d="M78 76Q103 20 93 6"/></g></svg><div className="rain-road"/><div className="road-stripe"/></div>
 <div className="entrance-copy"><div className="eyebrow"><span className="pulse-dot"/> A DATA SCIENCE STORY / ELLIPTIC++</div>
 <motion.h1 initial={{opacity:0,y:35}} animate={{opacity:1,y:0}} transition={{duration:1}}><span className="chrome">FRAUD</span><span className="neon">GRAPH.</span></motion.h1>
 <p className="hero-subtitle">One Bitcoin transaction can look ordinary on its own.<br/><strong>But what changes when you follow the connections?</strong></p>
 <div className="hero-buttons"><button className="hero-action" onClick={onEnter}>ENTER THE LEDGER <ArrowDown size={19}/></button><span className="microcopy">{play?"Investigation unlocked. No fictional outcomes.":"Follow the evidence. Not the hype."}</span></div></div>
 <div className="entrance-bottom"><span>AN ANALYST'S INTERACTIVE CASE FILE</span><span>SCROLL TO DESCEND ↓</span></div></div>;
}
export function OneTransaction(){
 const record=example(),[view,setView]=useState<"row"|"label"|"timing">("row");
 const attrs=Object.entries(record.features||{}).filter(([,v])=>v!==null).slice(0,7), sum=data.dataset.class_counts;
 return <><SectionTitle eyebrow="CHAPTER 01 / THE ROW" title="At first, it's just a row.">Amounts. Fees. Size. A handful of numbers. No context and certainly no verdict.</SectionTitle>
 <DepthCard className="one-transaction"><div className="transaction-phone"><div className="phone-speaker"/><div className="phone-header"><ScanEye size={20}/><span>LEDGER / TRANSACTION</span><span className="phone-status">RECORD</span></div>
 <div className="phone-tx">TX {record.id}</div><div className="phone-meta">REPRODUCED SOURCE RECORD · TIME STEP {record.timeStep}</div>
 <SelectChips label="Inspect the record" values={["row","label","timing"] as const} value={view} onChange={setView} format={v=>({row:"Attributes",label:"Known label",timing:"When?"}[v])}/>
 {view==="row"?<div className="ledger-lines">{attrs.map(([key,value])=><div key={key}><span>{key.replaceAll("_"," ")}</span><strong>{typeof value==="number"?String(value):EMPTY}</strong></div>)}</div>:
 view==="label"?<div className="phone-info"><span className="phone-alert">RETROSPECTIVE LABEL</span><strong>{record.retrospectiveClass===1?"Dataset illicit":record.retrospectiveClass===2?"Dataset licit":"Unknown"}</strong><p>These labels belong to transactions, not people. Most observed transactions have unknown outcomes.</p><div>Unknown: {count(sum["3"])} transactions</div></div>:
 <div className="phone-info"><span className="phone-alert">PREDICTION-TIME CONTRACT</span><strong>Batch close, not instant.</strong><p>Relationships within a time bucket are assumed observable at its end. This is not a live payment interruption tool.</p></div>}
 </div><div className="transaction-aside"><span className="eyebrow">WHAT A ROW CAN'T TELL YOU</span><h3>The neighborhood changes the question.</h3><p>Transaction characteristics alone cannot describe where an observed transfer sits among connected transactions.</p>
 <div className="mini-counter"><span>Transactions</span><strong>{count(data.dataset.nodes)}</strong></div><div className="mini-counter"><span>Retrospectively labeled</span><strong>{count(sum["1"]+sum["2"])}</strong></div><div className="mini-counter"><span>Unknown label</span><strong>{count(sum["3"])}</strong></div>
 <ResearchNote source="reports/LEAKAGE_AUDIT.md">Unknown ≠ innocent. Unknown outcomes remain unlabeled during supervised fitting and AP evaluation.</ResearchNote></div></DepthCard><SceneHint>One row is only the beginning.</SceneHint></>;
}
export function TheNetwork(){
 const record=example(),[view,setView]=useState<"graph"|"structure">("graph");
 return <><SectionTitle eyebrow="CHAPTER 02 / FOLLOW THE EDGES" title="The network has receipts.">Each node is a transaction, not a wallet owner. Arrows show observed directed relationships, not accusations.</SectionTitle>
 <DepthCard><div className="stage-top"><div><span className="eyebrow">SOURCE-BACKED NEIGHBORHOOD</span><h3>TX {record.id}</h3></div><SelectChips label="Explore network" values={["graph","structure"] as const} value={view} onChange={setView} format={v=>v==="graph"?"Connections":"Network facts"}/></div>
 {view==="graph"?<NetworkMap record={record}/>:<div className="network-factwall"><Fact label="Total directed links" value={count(data.graph.edges)}/><Fact label="Weak components" value={count(data.graph.weak_components)}/><Fact label="Largest component" value={count(data.graph.largest_component)}/><Fact label="Same-bucket links" value={count(data.dataset.same_step_edges)}/></div>}
 <div className="network-stats"><Fact label="Displayed neighbors" value={count(record.network.visibleNeighbors)}/><Fact label="Full graph nodes" value={count(data.graph.nodes)}/><Fact label="Observed time buckets" value={count(data.classByTime.length)}/></div>
 <ResearchNote source="reports/FEATURE_DICTIONARY.md">All released transaction edges are within a time bucket. Components can act like cohort signatures; same-bucket graph context is only valid under the stated batch-close assumption.</ResearchNote></DepthCard></>;
}
export function TheUplift(){
 const [graph,setGraph]=useState(false),original=data.originalCases.find(c=>c.case==="graph_uplift");
 if(!original)return <p>{EMPTY}</p>;
 const score=graph?original.score:original.baseline_score;
 return <><SectionTitle eyebrow="CHAPTER 03 / THE REVEAL" title="Same transaction. Different context.">One illustrative case from the original experiment—not proof that every transaction benefits.</SectionTitle>
 <DepthCard className="uplift-stage"><div className="uplift-display"><span className="eyebrow">CASE FILE / TX {original.txId}</span><p>{graph?"WITH GRAPH CONTEXT":"TRANSACTION ATTRIBUTES ONLY"}</p>
 <motion.div key={graph?"graph":"row"} className="huge-score" initial={{filter:"blur(12px)",scale:.91,opacity:.1}} animate={{filter:"blur(0px)",scale:1,opacity:1}}>{m(score,3)}</motion.div><span className="score-caption">MODEL SCORE · UNCALIBRATED</span>
 <div className="toggle-area"><span>ROW</span><button className={"neon-toggle "+(graph?"on":"")} aria-pressed={graph} aria-label="Toggle graph features" onClick={()=>setGraph(g=>!g)}><span/></button><span>NETWORK</span></div></div>
 <div className="uplift-detail"><span className="eyebrow">ONE REAL EXAMPLE</span><h3>Connections changed the ranking.</h3><p>The graph-enhanced model gave this retrospectively labeled illicit transaction a higher score. The label is not a claim of criminal behavior by any person.</p>
 <Fact label="Difference in score" value={(original.score-original.baseline_score>=0?"+":"")+m(original.score-original.baseline_score,3)}/>
 <ResearchNote source="reports/cases.csv">The exact displayed scores come from the original saved experiment. Reproduced scores can differ slightly; we keep the sources distinct.</ResearchNote></div></DepthCard></>;
}
export function ItDepends(){
 const [family,setFamily]=useState<"named"|"extended">("named"),[learner,setLearner]=useState<"xgboost"|"logistic">("xgboost"),stem=family+"_"+learner;
 const a=data.originalResults.find(r=>r.experiment_id===stem+"_tx"&&r.split==="test"),b=data.originalResults.find(r=>r.experiment_id===stem+"_graph"&&r.split==="test"),paired=data.pairedComparisons[stem];
 return <><SectionTitle eyebrow="CHAPTER 04 / MODEL COMPARISON" title="It depends. A lot.">The graph isn't a magic upgrade. Different learners and richer transaction features tell different stories.</SectionTitle>
 <DepthCard><div className="config-row"><SelectChips label="Feature family" values={["named","extended"] as const} value={family} onChange={setFamily} format={x=>x==="named"?"Named attributes":"Extended attributes"}/><SelectChips label="Learner" values={["xgboost","logistic"] as const} value={learner} onChange={setLearner} format={x=>x==="xgboost"?"XGBoost":"Logistic"}/></div>
 <div className="comparison-stage"><div className="comparison-cell"><span>TRANSACTION ONLY</span><strong>{a?m(a.pr_auc_ap,4):EMPTY}</strong><div className="neon-bar"><i style={{width:String((a?.pr_auc_ap||0)*100)+"%"}}/></div></div><div className="comparison-vs">VS</div><div className="comparison-cell glowing"><span>TRANSACTION + GRAPH</span><strong>{b?m(b.pr_auc_ap,4):EMPTY}</strong><div className="neon-bar"><i style={{width:String((b?.pr_auc_ap||0)*100)+"%"}}/></div></div></div>
 <div className="outcome-bar"><span>Original test AP</span><span>{paired?"ΔAP "+m(paired.delta_ap,4)+" · paired time-bucket interval "+m(paired.ci_95_low,3)+" to "+m(paired.ci_95_high,3):EMPTY}</span></div>
 <ResearchNote source="reports/paired_comparison.json">Average Precision is ranking quality on known labels, not accuracy or recovered money. The paired time-bucket bootstrap describes limited test periods, not independent markets.</ResearchNote>
 <details className="evidence-details"><summary>See all original held-out model comparisons</summary><div className="table-scroll"><table><thead><tr><th>Model</th><th>AP</th></tr></thead><tbody>{data.originalResults.filter(r=>r.split==="test").map(r=><tr key={r.experiment_id}><td>{r.experiment_id}</td><td>{m(r.pr_auc_ap,4)}</td></tr>)}</tbody></table></div></details></DepthCard></>;
}
export function AnalystQueue(){
 const points=data.originalReviewCapacity.filter(x=>x.experiment_id==="named_xgboost_graph"&&x.scope==="all_transactions"&&x.split==="test").sort((a,b)=>a.capacity_fraction-b.capacity_fraction);
 const capacities=[...new Set(points.map(x=>x.capacity_fraction))],[fraction,setFraction]=useState(capacities[Math.floor(capacities.length/2)]||capacities[0]),row=points.find(x=>Math.abs(x.capacity_fraction-fraction)<1e-9);
 const total=data.splitCounts.find(x=>x.split==="test"&&x.class===1)?.count;
 return <><SectionTitle eyebrow="CHAPTER 05 / THE REVIEW QUEUE" title="Your analysts have a limit.">Review capacity applies to all traffic. Unknown outcomes take up real space in the queue.</SectionTitle><DepthCard>
 <SelectChips label="Select a recorded test review budget" values={capacities} value={fraction} onChange={setFraction} format={pct}/>
 {row?<><div className="queue-head"><Fact label="Transactions queued" value={count(row.reviewed)}/><Fact label="Known illicit selected" value={count(row.known_illicit)}/><Fact label="Known-illicit capture" value={total?pct(row.known_illicit/total):EMPTY}/></div>
 <div className="queue-strip" role="img" aria-label={String(row.known_illicit)+" known illicit, "+String(row.known_licit)+" known licit, "+String(row.unknown)+" unknown"}><span className="illicit" style={{flex:row.known_illicit}}/><span className="licit" style={{flex:row.known_licit}}/><span className="unknown" style={{flex:row.unknown}}/></div>
 <div className="queue-legend"><span><i className="illicit"/> {count(row.known_illicit)} dataset illicit</span><span><i className="licit"/> {count(row.known_licit)} dataset licit</span><span><i className="unknown"/> {count(row.unknown)} unknown</span></div></>:<p>{EMPTY}</p>}
 <ResearchNote source="reports/DECISION_FRAMEWORK.md">Per-bucket top-K limits workload. It differs from the fixed-score LOW/REVIEW/HIGH policy. These are known-label counts, not a verified fraud detection rate for all transactions.</ResearchNote></DepthCard></>;
}
export function PlotTwist({play}:{play:boolean}){
 const series=[...data.primaryTimeline].sort((a,b)=>a.time_step-b.time_step),[step,setStep]=useState(series[0]?.time_step||0),current=series.find(x=>x.time_step===step)||series[0];
 const early=data.originalRobustness.find(r=>r.cohort==="early_test_steps_40_43"&&r.experiment_id==="named_xgboost_graph"),late=data.originalRobustness.find(r=>r.cohort==="late_test_steps_44_49"&&r.experiment_id==="named_xgboost_graph");
 const collapseStep=series.reduce((best,r,i)=>i>0&&(series[i-1].ap-r.ap)>best.drop?{step:r.time_step,drop:series[i-1].ap-r.ap}:best,{step:series[0]?.time_step||0,drop:-Infinity}).step;const broken=step>=collapseStep;
 return <div className={"collapse-scene "+(broken?"crisis":"")}><SectionTitle eyebrow="CHAPTER 06 / THE PLOT TWIST" title="And then the model fumbled.">The pooled result couldn't hide what happened next. Scrub through the actual test buckets.</SectionTitle>
 <DepthCard className="collapse-content"><div className="collapse-main"><span className="eyebrow">NAMED XGBOOST + GRAPH / ORIGINAL TEST</span><motion.div key={step} className="huge-score" initial={{x:broken?-15:0,opacity:.15,filter:"blur(7px)"}} animate={{x:0,opacity:1,filter:"blur(0px)"}}>{current?m(current.ap,4):EMPTY}</motion.div><span className="score-caption">AVERAGE PRECISION / STEP {step}</span>{broken&&<p className="glitch-headline">{play?"MISSION OUTCOME: RANKING FAILURE":"A documented loss of ranking quality."}</p>}</div>
 <div className="scrubber"><label htmlFor="time-scrub">TIME-STEP SCRUBBER</label><input id="time-scrub" type="range" min={series[0]?.time_step||0} max={series.at(-1)?.time_step||0} step="1" value={step} onChange={e=>setStep(Number(e.target.value))}/>
 <div className="time-bars">{series.map(r=><button key={r.time_step} className={r.time_step===step?"active":""} onClick={()=>setStep(r.time_step)} title={"Step "+r.time_step+": AP "+r.ap} aria-label={"Select time step "+r.time_step}><span style={{height:String(Math.max(4,r.ap*100))+"%"}}/><small>{r.time_step}</small></button>)}</div></div>
 <div className="failure-stats"><Fact label="Known illicit" value={current?count(current.illicit):EMPTY}/><Fact label="Known-label prevalence" value={current?pct(current.illicit/current.labeled,2):EMPTY}/><Fact label="Labeled cases" value={current?count(current.labeled):EMPTY}/></div>
 <div className="comparison-footer"><span>Early cohort pooled AP <strong>{early?m(early.ap,4):EMPTY}</strong></span><span>Later cohort pooled AP <strong>{late?m(late.ap,4):EMPTY}</strong></span></div>
 <ResearchNote source="docs/BASELINE_TEMPORAL_FINDINGS.md">The abrupt decline begins at step 43. Early/later figures are pooled cohort AP, not averages of step AP. Known-label prevalence and tiny positive counts complicate comparisons; concept drift is not confirmed.</ResearchNote></DepthCard></div>;
}

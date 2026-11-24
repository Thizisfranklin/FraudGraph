import React,{useMemo,useState} from "react";
import {motion} from "framer-motion";
import {Activity,ArrowRight,BookOpen,ClipboardCheck,Copy,Download,ExternalLink,Info,Network,ShieldCheck,Zap} from "lucide-react";
import {data} from "./data/data";
import {NetworkMap} from "./components/NetworkMap";
import {DepthCard,EMPTY,Fact,ResearchNote,Receipts,SectionTitle,SelectChips,count,m,pct,sourceUrl} from "./components/Common";

export function WhyBreak(){
 const options=[...new Set(data.temporal.drift.map(r=>r.feature))];
 const defaults=options.includes("size")?"size":options[0];
 const [feature,setFeature]=useState(defaults);
 const all=data.temporal.drift.filter(r=>r.feature===feature).sort((a,b)=>a.time_step-b.time_step);
 const [step,setStep]=useState(data.primaryTimeline.find(r=>r.time_step===43)?.time_step||all.at(-1)?.time_step||0);
 const row=all.find(r=>r.time_step===step),labels=data.temporal.labelScore.find(r=>r.time_step===step);
 const summary=data.permutationImportance.find(x=>x.feature===feature);
 const mark=data.temporal.drift.filter(r=>r.feature===feature);
 const max=Math.max(0.1,...mark.map(x=>x.psi??0));
 return <><SectionTitle eyebrow="CHAPTER 07 / DIAGNOSIS" title="The data shifted. But why?">Input distributions, score distributions and the observed mix of labels changed. That's evidence to investigate—not an identified causal mechanism.</SectionTitle>
 <DepthCard><div className="config-row"><div className="field-stack"><label htmlFor="drift-feature" className="field-caption">Choose a feature</label><select id="drift-feature" className="neon-select" value={feature} onChange={e=>setFeature(e.target.value)}>{options.map(x=><option key={x} value={x}>{x.replaceAll("_"," ")}</option>)}</select></div>
 <div className="field-stack"><label htmlFor="drift-step" className="field-caption">Time period</label><select id="drift-step" className="neon-select" value={step} onChange={e=>setStep(Number(e.target.value))}>{[...new Set(data.temporal.drift.map(r=>r.time_step))].sort((a,b)=>a-b).map(x=><option key={x} value={x}>Step {x}</option>)}</select></div></div>
 <div className="drift-display"><div><span className="eyebrow">POPULATION STABILITY INDEX / HISTORICAL REFERENCE</span><div className="large-highlight">{row?m(row.psi,3):EMPTY}</div><p>PSI measures feature-distribution shift; no single cutoff proves concept drift.</p></div>
 <div className="drift-ticks" role="img" aria-label="Observed feature population stability index by time step">{all.map(r=><button type="button" key={r.time_step} onClick={()=>setStep(r.time_step)} className={r.time_step===step?"active":""} aria-label={"Inspect time step "+r.time_step}><i style={{height:String(Math.max(3,100*(r.psi??0)/max))+"%"}}/><span>{r.time_step}</span></button>)}</div></div>
 <div className="network-factwall">
 <Fact label="Historical median" value={row?m(row.reference_median,6):EMPTY}/>
 <Fact label="Current median" value={row?m(row.current_median,6):EMPTY}/>
 <Fact label="Feature missingness now" value={row?pct(row.current_missing_rate,2):EMPTY}/>
 <Fact label="Known-illicit prevalence" value={labels?pct(labels.known_illicit_prevalence,2):EMPTY}/>
 </div>
 {summary&&<p className="supporting-line">Existing validation permutation-importance AP drop for this feature: <strong>{m(summary.mean_ap_drop,4)}</strong>. Permutation importance is model reliance, not a causal explanation.</p>}
 <ResearchNote source="docs/TEMPORAL_DRIFT_STUDY.md">Changes in P(X), known-label prevalence and prediction scores can coexist. The available evidence does not confirm a change in P(Y|X). Actual label-maturation timestamps are unavailable.</ResearchNote></DepthCard></>;
}

export function RetrainingLoop({play}:{play:boolean}){
 const board=data.temporal.leaderboard;
 const strategies=[...new Set(board.map(x=>x.strategy))];
 const [strategy,setStrategy]=useState(strategies[0]);
 const availableSteps=[...new Set(data.temporal.validationFolds.map(x=>x.time_step).concat(data.temporal.posthocReplay.map(x=>x.time_step)))].sort((a,b)=>a-b);
 const [step,setStep]=useState(availableSteps[0]);
 const [budget,setBudget]=useState(data.robustness.capacity[0]?.capacity_fraction||0);
 const selected=board.filter(x=>x.strategy===strategy).sort((a,b)=>b.mean_validation_ap-a.mean_validation_ap)[0];
 const original=data.temporal.validationFolds.find(x=>x.spec===selected?.spec&&x.time_step===step);
 const posthoc=data.temporal.posthocReplay.find(x=>x.spec===selected?.spec&&x.time_step===step);
 const result=original||posthoc;
 const isPosthoc=Boolean(posthoc);
 // Budget outcomes were measured only for validation-selected candidates in
 // robustness experiments; all unsupported combinations remain unavailable.
 const robustSelected=data.robustness.selected.find(x=>x.label_lag===2&&x.strategy===strategy);
 const review=data.robustness.capacity.find(x=>x.label_lag===2&&x.candidate===robustSelected?.candidate&&x.time_step===step&&x.capacity_fraction===budget);
 const budgets=[...new Set(data.robustness.capacity.map(x=>x.capacity_fraction))];
 return <><SectionTitle eyebrow="CHAPTER 08 / ADAPTATION" title="You can retrain. Can you generalize?">A forward replay compares frozen, expanding, rolling, and recency-weighted XGBoost. Choose one recorded experiment and face the result.</SectionTitle>
 <DepthCard><div className="game-panel"><span className="eyebrow">{play?"ANALYST SIMULATION / REAL RESULTS":"FORWARD-REPLAY RESEARCH / RECORDED RESULTS"}</span>
 <div className="config-row"><SelectChips label="Training strategy" values={strategies} value={strategy} onChange={setStrategy} format={s=>({frozen:"Frozen",expanding:"Expanding",rolling:"Rolling",recency:"Recency-weighted"}[s]||s)}/>
 <div className="field-stack"><label className="field-caption" htmlFor="retrain-step">Choose time step</label><select id="retrain-step" className="neon-select" value={step} onChange={e=>setStep(Number(e.target.value))}>{availableSteps.map(x=><option value={x} key={x}>Step {x}</option>)}</select></div></div>
 <div className="config-row"><SelectChips label="Analyst review budget" values={budgets} value={budget} onChange={setBudget} format={pct}/></div>
 <div className="game-output"><span>{selected?.spec||EMPTY}</span><strong>{result?m(result.ap,4):EMPTY}</strong><span>AVERAGE PRECISION {isPosthoc?"· POST-HOC REPLAY":"· VALIDATION FOLD"}</span></div>
 {result?<div className="network-factwall"><Fact label="Known illicit" value={count(result.known_illicit)}/><Fact label="Known-label prevalence" value={pct(result.prevalence,2)}/><Fact label="Review queue, selected budget" value={review?count(review.reviewed):EMPTY}/><Fact label="Known illicit in queue" value={review?count(review.known_illicit):EMPTY}/></div>:<p className="missing-outcome">-- awaiting data -- · No saved replay for this strategy and period. Outcomes are not simulated.</p>}
 </div><ResearchNote source="docs/TEMPORAL_DRIFT_STUDY.md">The strategy and hyperparameters were selected using earlier validation, not test results. Later replay on previously inspected test steps is exploratory; it is not a fresh independent holdout. Label-delay assumptions are not measured availability dates.</ResearchNote></DepthCard></>;
}

export function StressTests({play}:{play:boolean}){
 const delays=[...new Set(data.robustness.selected.map(x=>x.label_lag))];
 const [lag,setLag]=useState(delays[0]);
 const candidates=data.robustness.leaderboard.filter(x=>x.label_lag===lag);
 const [preset,setPreset]=useState(candidates[0]?.candidate||"");
 const chosen=candidates.find(x=>x.candidate===preset)||candidates[0];
 const steps=[...new Set(data.robustness.validationFolds.map(x=>x.time_step))].sort((a,b)=>a-b);
 const [step,setStep]=useState(steps[0]);
 const fold=data.robustness.validationFolds.find(x=>x.candidate===chosen?.candidate&&x.label_lag===lag&&x.time_step===step);
 const selected=data.robustness.selected.find(x=>x.label_lag===lag);
 return <><SectionTitle eyebrow="CHAPTER 09 / MODEL CAPACITY" title="It's giving overfit... maybe.">Try model complexity and hypothetical label delays. Training-versus-validation gaps are a clue, not proof that overfitting alone caused the collapse.</SectionTitle>
 <DepthCard><SelectChips label="Assumed delay before labels become available" values={delays} value={lag} onChange={l=>{setLag(l);const next=data.robustness.selected.find(x=>x.label_lag===l);if(next)setPreset(next.candidate)}} format={x=>x+" steps"}/>
 <div className="config-row"><div className="field-stack"><label className="field-caption" htmlFor="capacity-preset">Recorded model candidate</label><select className="neon-select" id="capacity-preset" value={chosen?.candidate||""} onChange={e=>setPreset(e.target.value)}>{candidates.map(x=><option key={x.candidate} value={x.candidate}>{x.candidate.replaceAll("_"," ")}</option>)}</select></div>
 <SelectChips label="Validation period" values={steps} value={step} onChange={setStep} format={x=>"Step "+x}/></div>
 <div className="train-compare"><div className="comparison-cell"><span>TRAIN AP / IN SAMPLE</span><strong>{fold?m(fold.train_ap_in_sample,4):EMPTY}</strong></div><div className="comparison-vs">→</div><div className="comparison-cell glowing"><span>FUTURE VALIDATION AP</span><strong>{fold?m(fold.forward_ap,4):EMPTY}</strong></div></div>
 <div className="network-factwall"><Fact label="This candidate, mean validation AP" value={chosen?m(chosen.mean_forward_ap,4):EMPTY}/><Fact label="Worst-period validation AP" value={chosen?m(chosen.worst_forward_ap,4):EMPTY}/><Fact label="Chosen in this lag scenario" value={chosen?.candidate===selected?.candidate?"Yes":"No"}/><Fact label="Excess AP gap" value={fold?m(fold.excess_ap_gap,4):EMPTY}/></div>
 <p className="supporting-line">{play?"Recorded mission result, not a simulated win. ":""}A stronger training result can fail to generalize under distribution shift and selective labeling. Simpler models can underfit, too.</p>
 <ResearchNote source="docs/ROBUSTNESS_AND_ANALYST_EVALUATION.md">Candidate selection maximized the worst forward-validation bucket, then mean AP. Each assumed label delay was evaluated separately and is not an accuracy hyperparameter. These folds are dependent and limited.</ResearchNote></DepthCard></>;
}

export function AnalystBudgets({play}:{play:boolean}){
 const lags=[...new Set(data.robustness.capacity.map(x=>x.label_lag))];
 const [lag,setLag]=useState(lags[0]);
 const steps=[...new Set(data.robustness.capacity.map(x=>x.time_step))].sort((a,b)=>a-b);
 const [step,setStep]=useState(steps[0]);
 const budgets=[...new Set(data.robustness.capacity.map(x=>x.capacity_fraction))].sort((a,b)=>a-b);
 const [budget,setBudget]=useState(budgets.find(x=>x===.05)||budgets[0]);
 const selected=data.robustness.selected.find(x=>x.label_lag===lag);
 const row=data.robustness.capacity.find(x=>x.label_lag===lag&&x.candidate===selected?.candidate&&x.time_step===step&&x.capacity_fraction===budget);
 return <><SectionTitle eyebrow="CHAPTER 10 / REAL REVIEW BUDGETS" title="Unknown still fills the queue.">An analyst's time is limited. Select a recorded period and budget—never an imagined outcome.</SectionTitle><DepthCard>
 <div className="config-row"><SelectChips label="Hypothetical label delay" values={lags} value={lag} onChange={setLag} format={x=>x+" steps"}/><SelectChips label="Validation period" values={steps} value={step} onChange={setStep} format={x=>"Step "+x}/></div><SelectChips label="Percentage of ALL traffic sent for review" values={budgets} value={budget} onChange={setBudget} format={pct}/>
 {row?<><div className="queue-head"><Fact label="Total review slots" value={count(row.reviewed)}/><Fact label="Known illicit found" value={count(row.known_illicit)}/><Fact label="Known illicit capture" value={pct(row.known_illicit_capture)}/></div>
 <div className="queue-strip" role="img" aria-label={String(row.known_illicit)+" known illicit; "+String(row.known_licit)+" known licit; "+String(row.unknown)+" unknown"}><span className="illicit" style={{flex:row.known_illicit}}/><span className="licit" style={{flex:row.known_licit}}/><span className="unknown" style={{flex:row.unknown}}/></div>
 <div className="queue-legend"><span><i className="illicit"/> {count(row.known_illicit)} known illicit</span><span><i className="licit"/> {count(row.known_licit)} known licit</span><span><i className="unknown"/> {count(row.unknown)} unknown</span></div>
 <div className="game-footer">{play?"QUEUE INSIGHT: ":"VALIDATION OBSERVATION: "}Unknown cases consume review capacity even though their outcomes are not known.</div></>:<p className="missing-outcome">{EMPTY}</p>}
 <ResearchNote source="docs/ROBUSTNESS_AND_ANALYST_EVALUATION.md">Only the selected candidate for each label-lag scenario has review-budget rows. Known illicit capture is not true recall among all illicit transactions; no population-wide accuracy claim follows.</ResearchNote></DepthCard></>;
}

export function Workbench(){
 const [idx,setIdx]=useState(0);
 const examples=data.investigator;
 const record=examples[idx]||examples[0];
 const limit=Math.min(examples.length,20);
 return <><SectionTitle eyebrow="CHAPTER 11 / HUMAN IN THE LOOP" title="Meet the Investigator.">This part isn't just a roadmap anymore. There's a working retrospective React prototype. Live wallet checking and production decisions remain future work.</SectionTitle>
 <DepthCard><div className="stage-top"><div><span className="eyebrow">REAL SAVED DATASET CASES</span><h3>{record?"TX "+record.id:EMPTY}</h3></div><div className="field-stack"><label className="field-caption" htmlFor="sample-selector">Choose an investigation</label><select className="neon-select" id="sample-selector" value={idx} onChange={e=>setIdx(Number(e.target.value))}>{examples.slice(0,limit).map((r,i)=><option key={r.id} value={i}>Transaction {r.id}</option>)}</select></div></div>
 {record?<><NetworkMap record={record} compact/><div className="network-factwall"><Fact label="Historical graph score" value={m(record.scores.graph,4)}/><Fact label="Transaction-only score" value={m(record.scores.transaction,4)}/><Fact label="Dataset label" value={record.retrospectiveClass===1?"Illicit":record.retrospectiveClass===2?"Licit":"Unknown"}/><Fact label="Case pool" value={count(examples.length)}/></div></>:<div>{EMPTY}</div>}
 <div className="source-links"><a href={data.repository+"/tree/main/app"} target="_blank" rel="noreferrer">Open the existing React Investigator <ExternalLink size={15}/></a><a href={data.repository+"/blob/main/docs/ANALYST_WORKBENCH_ROADMAP.md"} target="_blank" rel="noreferrer">Read the live-system roadmap <ExternalLink size={15}/></a></div>
 <ResearchNote source="app/README.md">This existing app explores historical cases and stores analyst notes in the browser. It does not establish transaction guilt, recognize wallet ownership, or score an arbitrary live Bitcoin transaction.</ResearchNote></DepthCard></>;
}

export function Takeaway(){
 const [copied,setCopied]=useState(false);
 const named=data.originalResults.find(x=>x.experiment_id==="named_xgboost_graph"&&x.split==="test");
 const base=data.originalResults.find(x=>x.experiment_id==="named_xgboost_tx"&&x.split==="test");
 const early=data.originalRobustness.find(x=>x.cohort==="early_test_steps_40_43"&&x.experiment_id==="named_xgboost_graph");
 const late=data.originalRobustness.find(x=>x.cohort==="late_test_steps_44_49"&&x.experiment_id==="named_xgboost_graph");
 const text="FraudGraph | Elliptic++ Bitcoin transaction research. Original named XGBoost AP: "+(base?m(base.pr_auc_ap,4):EMPTY)+" without graph vs "+(named?m(named.pr_auc_ap,4):EMPTY)+" with graph. Early/later pooled AP: "+(early?m(early.ap,4):EMPTY)+" → "+(late?m(late.ap,4):EMPTY)+". Observed degradation; cause unresolved. No prospective claims. "+data.repository;
 async function copy(){try{await navigator.clipboard.writeText(text);setCopied(true);}catch{const blob=new Blob([text],{type:"text/plain"});const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="fraudgraph-research-summary.txt";a.click();URL.revokeObjectURL(url);setCopied(true);}}
 return <><SectionTitle eyebrow="CHAPTER 12 / FINAL RECEIPT" title="The failure is the finding.">Graph context helped one model—until the future looked different. That tension is the most useful result.</SectionTitle>
 <DepthCard className="ending-card"><span className="eyebrow">STORY COMPLETE / RESEARCH CONTINUES</span><h3>Better questions &gt; bigger claims.</h3>
 <div className="network-factwall"><Fact label="Original graph-model AP" value={named?m(named.pr_auc_ap,4):EMPTY}/><Fact label="Late-period pooled AP" value={late?m(late.ap,4):EMPTY}/><Fact label="Fresh prospective confirmation" value={EMPTY}/><Fact label="Source-backed cases in prototype" value={count(data.investigator.length)}/></div>
 <button className="hero-action share-action" onClick={copy}>{copied?"SUMMARY COPIED":"COPY MY RESEARCH RECEIPT"} <Copy size={16}/></button><p className="supporting-line">This share card uses the actual original reports. It never claims money recovered, guilt established, or a reliable production model.</p>
 <div className="supporting-research"><h4>What's inside the project</h4><div className="receipt-grid">
 <span><ShieldCheck size={17}/> Source SHA checks + temporal leakage tests</span>
 <span><Activity size={17}/> Shuffled-label and duplicate-fingerprint diagnostics</span>
 <span><Network size={17}/> Graph features and degree/SQL parity</span>
 <span><BookOpen size={17}/> Notebook results and later exploratory study</span></div></div>
 <div className="notebook-list"><h4>Research notebooks</h4>{data.notebooks.map(x=><a key={x.name} href={sourceUrl("notebooks/"+x.name)} target="_blank" rel="noreferrer"><span>{x.name}</span><span>{x.status} <ExternalLink size={13}/></span></a>)}</div>
 <div className="source-links"><a href={data.repository} target="_blank" rel="noreferrer">Full GitHub repository <ExternalLink size={15}/></a><a href="https://github.com/git-disl/EllipticPlusPlus" target="_blank" rel="noreferrer">Elliptic++ dataset credit <ExternalLink size={15}/></a></div>
 <ResearchNote source="reports/LEAKAGE_AUDIT.md">The research uses an end-of-time-bucket snapshot. Many outcomes are unknown; model scores are uncalibrated. The cause of the temporal collapse is not established, and the later adaptations were motivated by already-inspected results.</ResearchNote></DepthCard></>;
}

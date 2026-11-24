import React, { useEffect, useMemo, useState } from "react";
import { ReactFlow, Background, Controls, MiniMap, MarkerType } from "@xyflow/react";
import {
  Activity, ArrowDownRight, ArrowRight, ArrowUpRight, BarChart3, CheckCircle2,
  ChevronRight, CircleHelp, ClipboardCheck, Copy, Download, ExternalLink,
  Filter, GitBranch, Info, LayoutDashboard, Network, Search, ShieldAlert,
  ShieldCheck, SlidersHorizontal, Wallet, X
} from "lucide-react";
import {
  ResponsiveContainer, CartesianGrid, Tooltip, LineChart, Line,
  XAxis, YAxis, Legend, BarChart, Bar, ReferenceLine
} from "recharts";

const LABELS = {1:"Known illicit",2:"Known licit",3:"Unknown"};
const COLORS = {1:"#f38b87",2:"#67a9ff",3:"#96a7bf"};
const ORIGINAL_CASES = [
  {id:"12662327",timeStep:41,retrospectiveClass:1,caseType:"high_score_illicit",
   scores:{graph:.9839068651,transaction:.8936192989},
   shapLogOdds:{size:3.2971811,fees:1.0242406,num_output_addresses:.40705994,g_component_size:.32483447,in_BTC_min:.25663382,g_pagerank_scaled:.2097045},
   features:{},network:{nodes:[],edges:[],totalNeighbors:2,visibleNeighbors:2}},
  {id:"72687354",timeStep:42,retrospectiveClass:2,caseType:"high_score_licit",
   scores:{graph:.9558525681,transaction:.9068122506},
   shapLogOdds:{size:3.648304,fees:.58394766,num_output_addresses:.48968026,out_BTC_min:-.2301272,g_component_size:-.12142443},
   features:{},network:{nodes:[],edges:[],totalNeighbors:2,visibleNeighbors:2}},
  {id:"12661223",timeStep:41,retrospectiveClass:1,caseType:"graph_uplift",
   scores:{graph:.6889969707,transaction:.2992019355},
   shapLogOdds:{size:2.5335047,fees:.77255577,in_BTC_min:-1.0861012,g_component_size:.39900517},
   features:{},network:{nodes:[],edges:[],totalNeighbors:2,visibleNeighbors:2}}
];
const CASE_NAMES={
  high_score_illicit:"High-scoring, labeled illicit",
  high_score_licit:"High-scoring, labeled licit",
  graph_uplift:"Graph context changed the score",
  sampled_review_queue:"Historical review-queue sample"
};
const STEP_METRICS=[
  {step:40,ap:.5552,prevalence:.0925,positives:112},
  {step:41,ap:.8412,prevalence:.1025,positives:116},
  {step:42,ap:.8142,prevalence:.1110,positives:239},
  {step:43,ap:.0265,prevalence:.0175,positives:24},
  {step:44,ap:.0257,prevalence:.0151,positives:24},
  {step:45,ap:.0092,prevalence:.0041,positives:5},
  {step:46,ap:.0235,prevalence:.0028,positives:2},
  {step:47,ap:.0245,prevalence:.0260,positives:22},
  {step:48,ap:.1101,prevalence:.0764,positives:36},
  {step:49,ap:.1048,prevalence:.1176,positives:56}
];
const LAG_RESULTS=[
  {lag:"2 steps",mean:.8140,worst:.7503,strategy:"Expanding history"},
  {lag:"4 steps",mean:.8158,worst:.7231,strategy:"Frozen / higher capacity"},
  {lag:"6 steps",mean:.8158,worst:.7231,strategy:"Frozen / higher capacity"}
];
const CAPACITY={
  "1":{reviewed:118,illicit:51,licit:0,unknown:67},
  "5":{reviewed:580,illicit:184,licit:2,unknown:394},
  "10":{reviewed:1158,illicit:229,licit:38,unknown:891}
};
const featNames={
 size:"Transaction size",fees:"Fee amount",total_BTC:"BTC amount",
 num_input_addresses:"Input addresses",num_output_addresses:"Output addresses",
 g_in_degree:"Incoming edges",g_out_degree:"Outgoing edges",
 g_component_size:"Graph component size",g_pagerank_scaled:"PageRank",
 g_neighbor_degree_mean:"Mean neighbor degree",
 in_BTC_min:"Minimum input BTC",out_BTC_min:"Minimum output BTC"
};
const fmt=(n,d=3)=>Number.isFinite(Number(n))?Number(n).toFixed(d):"—";
function fileNoteKey(id){return "fraudgraph-investigator.case."+id;}
function restoreNote(id){try{return JSON.parse(localStorage.getItem(fileNoteKey(id)))||{};}catch{return {};}}
function downloadJSON(name,obj){const blob=new Blob([JSON.stringify(obj,null,2)],{type:"application/json"});const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);}
function Badge({kind,children}){return <span className={"badge "+(kind||"")}>{children}</span>;}
function ScoreBar({label,value,secondary=false}){return <div className="score-bar"><div className="between small"><span>{label}</span><strong>{fmt(value)}</strong></div><div className="bar-track"><div className={"bar-fill "+(secondary?"secondary":"")} style={{width:Math.max(0,Math.min(100,value*100))+"%"}}/></div></div>;}
function Metric({label,value,description,emphasis=false}){return <div className="metric"><div className="muted tiny">{label}</div><strong className={emphasis?"emphasis":""}>{value}</strong>{description&&<div className="muted tiny">{description}</div>}</div>;}
function EmptyNetwork({record}){const figures={high_score_illicit:"case_high_score_illicit.png",high_score_licit:"case_high_score_licit.png",graph_uplift:"case_graph_uplift.png"};const pic=figures[record.caseType];return <div className="empty-network">{pic?<><img alt={"Recorded one-hop transaction neighborhood for "+record.id} src={"https://raw.githubusercontent.com/Thizisfranklin/FraudGraph/main/reports/figures/"+pic}/><span>Source-backed network snapshot · Pan/zoom available once the case dataset is exported</span></>:<div className="empty-state"><Network size={28}/><p>Graph context was not packaged for this sample.</p></div>}</div>;}
function NetworkView({record,onInspect}) {
  const graph=record.network||{nodes:[],edges:[]};
  const elements=useMemo(()=>{
    const entries=graph.nodes||[];
    const center=entries.find(n=>n.focus)||entries.find(n=>n.id===record.id);
    const others=entries.filter(n=>n.id!==record.id);
    const nodes=(center?[center]:[]).concat(others).map((n,i)=>{
      const r=others.length<=8?155:270;
      const angle=-Math.PI/2+2*Math.PI*((i-1)/Math.max(others.length,1));
      const focus=n.id===record.id;
      return {id:String(n.id),position:focus?{x:400,y:270}:{x:400+r*Math.cos(angle),y:270+r*Math.sin(angle)},
        data:{label:focus?"FOCUS · "+n.id:n.id,source:n},draggable:false,selectable:true,
        style:{border:"1px solid "+(focus?"#8ab9ff":COLORS[n.retrospectiveClass]||COLORS[3]),
          borderRadius:focus?18:12,background:focus?"#3558b1":"#15243b",
          color:"#f1f6ff",fontWeight:focus?800:500,fontSize:focus?13:11,
          padding:focus?14:9,width:focus?163:120,boxShadow:focus?"0 8px 28px #274dd955":"none"}};
    });
    const edges=(graph.edges||[]).map((edge,i)=>({id:"edge-"+i,source:String(edge.source),target:String(edge.target),
      type:"smoothstep",style:{stroke:"#8bb0d5",strokeWidth:1.5},markerEnd:{type:MarkerType.ArrowClosed,color:"#8bb0d5"}}));
    return {nodes,edges};
  },[record.id,graph]);
  if(elements.nodes.length<=1)return <EmptyNetwork record={record}/>;
  return <div className="flow" role="region" aria-label={"Actual directed transaction neighborhood of "+record.id}><ReactFlow key={record.id} nodes={elements.nodes} edges={elements.edges} fitView fitViewOptions={{padding:.22}}
     minZoom={.22} maxZoom={1.8} nodesConnectable={false} elementsSelectable={true}
     onNodeClick={(_,node)=>onInspect(node.data.source)} proOptions={{hideAttribution:true}}>
      <Background color="#263d5f" gap={23} size={1}/><Controls showInteractive={false}/>
      <MiniMap pannable zoomable nodeColor={n=>n.id===record.id?"#5886ed":"#2d4568"} maskColor="#101c2abe"/>
    </ReactFlow></div>;
}
function Explanation({record}){
  const entries=Object.entries(record.shapLogOdds||{}).filter(([,v])=>Number.isFinite(v))
      .sort((a,b)=>Math.abs(b[1])-Math.abs(a[1])).slice(0,8);
  const stats=Object.entries(record.features||{}).filter(([,v])=>v!==null&&Number.isFinite(v)).slice(0,8);
  const max=Math.max(1,...entries.map(([,v])=>Math.abs(v)));
  return <div><div className="section-heading"><h3>{entries.length?"Why the historical score changed":"Transaction attributes"}</h3><Badge>Evidence</Badge></div>
    {entries.length?<><p className="muted small">Saved TreeSHAP contributions to the original graph model's log-odds. Positive values push the score up, negative values push it down. These are <strong>not</strong> causal explanations.</p>
      <div className="shap-list">{entries.map(([name,value])=><div className="shap-row" key={name}>
      <span title={name}>{featNames[name]||name}</span><div className="shap-track"><div className={value>=0?"pos":"neg"} style={{width:Math.abs(value)/max*100+"%"}}/></div>
      <b className={value>=0?"up":"down"}>{value>0?"+":""}{fmt(value,2)}</b></div>)}</div></>:<><p className="muted small">This sampled case has no precomputed SHAP explanation. These are observed feature values, <strong>not reasons for wrongdoing</strong>.</p>
      <div className="features">{stats.map(([name,value])=><div className="feature-row" key={name}><span>{featNames[name]||name}</span><b>{fmt(value,4)}</b></div>)}</div></>}
  </div>;
}
function App(){
  const [tab,setTab]=useState("investigate");
  const [records,setRecords]=useState(ORIGINAL_CASES);
  const [dataStatus,setDataStatus]=useState("Loading real transaction examples…");
  const [selectedId,setSelectedId]=useState(ORIGINAL_CASES[0].id);
  const [search,setSearch]=useState("");
  const [labelFilter,setLabelFilter]=useState("all");
  const [stepFilter,setStepFilter]=useState("all");
  const [showAll,setShowAll]=useState(false);
  const [inspected,setInspected]=useState(null);
  const [note,setNote]=useState({});
  const [savedNotice,setSavedNotice]=useState("");
  const [capacity,setCapacity]=useState("5");
  const selected=records.find(r=>r.id===selectedId)||records[0];
  useEffect(()=>{
    let active=true;
    fetch(import.meta.env.BASE_URL+"investigations.json",{cache:"no-store"})
      .then(r=>{if(!r.ok)throw new Error("Export not present");return r.json();})
      .then(data=>{if(!active)return;const list=(data.transactions||[]).filter(r=>r.id&&r.scores&&r.network);
        if(!list.length)throw new Error("No valid records in export");
        setRecords(list);setDataStatus(list.length+" verified source transactions loaded");})
      .catch(()=>{if(active)setDataStatus("Three documented examples loaded · complete case export not available");});
    return()=>{active=false;};
  },[]);
  useEffect(()=>{if(selected){setNote(restoreNote(selected.id));setInspected(null);setSavedNotice("");}},[selected?.id]);
  const filtered=useMemo(()=>{
    const q=search.trim().toLowerCase();
    return records.filter(r=>(!q||String(r.id).includes(q)||String(CASE_NAMES[r.caseType]||"").toLowerCase().includes(q))
       &&(labelFilter==="all"||String(r.retrospectiveClass)===labelFilter)
       &&(stepFilter==="all"||String(r.timeStep)===stepFilter))
      .sort((a,b)=>{const pinned={high_score_illicit:0,high_score_licit:1,graph_uplift:2};const ap=pinned[a.caseType]??99,bp=pinned[b.caseType]??99;return ap-bp||b.scores.graph-a.scores.graph||String(a.id).localeCompare(String(b.id));});
  },[records,search,labelFilter,stepFilter]);
  const visible=showAll?filtered:filtered.slice(0,30);
  const allSteps=useMemo(()=>[...new Set(records.map(r=>r.timeStep))].sort((a,b)=>a-b),[records]);
  function choose(r){setSelectedId(r.id);setTab("investigate");}
  function saveNote(){if(!selected)return;const data={...note,updatedAt:new Date().toISOString()};try{localStorage.setItem(fileNoteKey(selected.id),JSON.stringify(data));setNote(data);setSavedNotice("Saved in this browser.");}catch{setSavedNotice("Local storage unavailable. Export your case to save it.");}}
  function exportCase(){if(!selected)return;downloadJSON("fraudgraph-case-"+selected.id+".json",{
    caseId:selected.id,dataset:"Elliptic++",timeStep:selected.timeStep,
    retrospectiveClass:LABELS[selected.retrospectiveClass],model:"Original frozen named-feature XGBoost graph model",
    graphScore:selected.scores.graph,transactionScore:selected.scores.transaction,
    featureValues:selected.features||{},graphSnapshot:selected.network,
    reviewerDisposition:note.disposition||"Needs more information",reviewerNotes:note.notes||"",
    exportedAt:new Date().toISOString(),limitations:"Not a legal fraud verdict. Dataset IDs are not live Bitcoin TXIDs. Scores are uncalibrated. Labels are retrospectively known; many remain unknown."
  });setSavedNotice("Case JSON downloaded.");}
  return <div className="app">
    <header className="topbar"><div className="brand"><div className="brand-mark"><Network size={23}/></div><div><strong>FraudGraph</strong><span>INVESTIGATOR</span></div></div>
      <div className="top-right"><span className="live-dot"/><span>Historical research data</span><a href="https://github.com/Thizisfranklin/FraudGraph" target="_blank" rel="noreferrer" className="repo-link">View source <ExternalLink size={13}/></a></div>
    </header>
    <div className="shell"><aside className="nav">
      <div className="nav-top"><p className="nav-group">WORKSPACE</p>
       <button type="button" className={"nav-item "+(tab==="investigate"?"active":"")} onClick={()=>setTab("investigate")}><Network size={18}/> Transaction review <ChevronRight size={15}/></button>
       <button type="button" className={"nav-item "+(tab==="model"?"active":"")} onClick={()=>setTab("model")}><Activity size={18}/> Model reliability <ChevronRight size={15}/></button>
       <button type="button" className={"nav-item "+(tab==="about"?"active":"")} onClick={()=>setTab("about")}><CircleHelp size={18}/> About this project <ChevronRight size={15}/></button>
       <div className="nav-divider"/><div className="nav-footnote"><ShieldAlert size={18}/><p><strong>Analyst decision support</strong><br/>This app does not detect crime or identify wallet owners.</p></div></div>
      <div className="nav-bottom">Built with React + directed network evidence<br/><small>Elliptic++ research prototype</small></div>
    </aside><main className="main">
      {tab==="investigate"&&<><div className="page-heading"><div><div className="eyebrow">INVESTIGATION WORKSPACE / CASE REVIEW</div><h1>Investigate transaction patterns</h1><p>Explore real saved Bitcoin transaction examples and graph context. Every score is historical evidence, not a fraud verdict.</p></div><Badge kind="blue"><CheckCircle2 size={13}/> Source-backed examples</Badge></div>
      <div className="caution"><ShieldAlert size={19}/><span><strong>Research-only transaction review.</strong> IDs below are Elliptic++ dataset IDs, not arbitrary Bitcoin wallet addresses or live Bitcoin TXIDs. Known labels are retrospective; scores are uncalibrated.</span></div>
      <div className="case-layout"><section className="panel case-browser"><div className="section-heading"><h2>Review queue</h2><Badge>{records.length} cases</Badge></div><p className="muted small">{dataStatus}</p>
        <div className="search-wrap"><Search size={16}/><input aria-label="Search dataset transaction IDs" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search transaction ID…"/></div>
        <div className="filters"><label><Filter size={14}/> Label<select value={labelFilter} onChange={e=>setLabelFilter(e.target.value)}><option value="all">All labels</option><option value="1">Known illicit</option><option value="2">Known licit</option><option value="3">Unknown</option></select></label>
          <label>Step<select value={stepFilter} onChange={e=>setStepFilter(e.target.value)}><option value="all">All steps</option>{allSteps.map(t=><option key={t} value={t}>{t}</option>)}</select></label></div>
        <div className="case-list">{visible.length?visible.map(r=><button type="button" key={r.id} className={"case-row "+(selected?.id===r.id?"chosen":"")} onClick={()=>choose(r)}><div className="between"><span className="txmono">TX {r.id}</span><Badge kind={r.retrospectiveClass===1?"danger":r.retrospectiveClass===2?"blue":"neutral"}>{LABELS[r.retrospectiveClass]}</Badge></div><div className="between small muted"><span>Time step {r.timeStep}</span><span>Score {fmt(r.scores.graph)}</span></div><div className="mini-meter"><span style={{width:Math.max(0,Math.min(100,r.scores.graph*100))+"%"}}/></div></button>):<div className="empty-queue">No matching dataset transaction IDs.</div>}</div>
        {filtered.length>30&&<button className="text-button" onClick={()=>setShowAll(!showAll)}>{showAll?"Show fewer":"Show all "+filtered.length+" cases"}</button>}
      </section>
      {selected&&<div className="case-content"><div className="panel case-details"><div className="between wrap"><div><div className="eyebrow">SELECTED CASE / TIME STEP {selected.timeStep}</div><h2 className="case-title">Transaction <span>{selected.id}</span></h2><p className="muted">{CASE_NAMES[selected.caseType]||"Observed transaction from the saved dataset"}</p></div><Badge kind={selected.retrospectiveClass===1?"danger":selected.retrospectiveClass===2?"blue":"neutral"}>{LABELS[selected.retrospectiveClass]} · dataset</Badge></div>
        <div className="metric-grid"><Metric label="Graph model score" value={fmt(selected.scores.graph)} description="Not a calibrated probability" emphasis/><Metric label="Transaction-only score" value={fmt(selected.scores.transaction)} description="Same saved comparison"/><Metric label="Graph score difference" value={(selected.scores.graph-selected.scores.transaction>=0?"+":"")+fmt(selected.scores.graph-selected.scores.transaction)} description="Graph minus transaction"/></div>
        <div className="compare"><ScoreBar label="Original XGBoost with graph attributes" value={selected.scores.graph}/><ScoreBar label="Original transaction-only XGBoost" value={selected.scores.transaction} secondary/></div></div>
        <div className="panel network-panel"><div className="between wrap"><div><h3>Transaction neighborhood</h3><p className="muted small">Actual directed links from the dataset, visible at the end of time step {selected.timeStep}.</p></div><Badge><GitBranch size={12}/> {selected.network?.visibleNeighbors||0} of {selected.network?.totalNeighbors||0} neighbors</Badge></div>
          <div className="graph-shell"><NetworkView record={selected} onInspect={setInspected}/></div>
          <div className="legend"><span><i className="legend-circle focus"/> Selected</span><span><i className="legend-circle illicit"/> Known illicit</span><span><i className="legend-circle licit"/> Known licit</span><span><i className="legend-circle unknown"/> Unknown</span></div>
          {inspected&&<div className="node-inspector"><div className="between"><strong>Neighbor {inspected.id}</strong><button aria-label="Close neighbor details" onClick={()=>setInspected(null)} className="icon-button"><X size={16}/></button></div><span className="muted small">Step {inspected.timeStep} · {LABELS[inspected.retrospectiveClass]||"Unknown"} (retrospective label)</span>{records.some(r=>r.id===inspected.id)&&<button className="text-button" onClick={()=>setSelectedId(inspected.id)}>Open its case <ArrowRight size={14}/></button>}</div>}
        </div>
        <div className="lower-grid"><div className="panel"><Explanation record={selected}/></div><div className="panel decision-panel"><div className="section-heading"><h3>Analyst decision</h3><ClipboardCheck size={18}/></div><p className="muted small">Record what the evidence warrants. Case notes stay in this browser; never enter customer secrets.</p>
          <label className="field-label">Disposition<select value={note.disposition||"Needs more information"} onChange={e=>setNote({...note,disposition:e.target.value})}><option>Needs more information</option><option>Escalate for human investigation</option><option>No further action on current evidence</option></select></label>
          <label className="field-label">Review notes<textarea rows={4} value={note.notes||""} onChange={e=>setNote({...note,notes:e.target.value})} placeholder="Which transaction features or connections deserve closer review? What information is missing?"/></label>
          <div className="button-row"><button className="outline-btn" onClick={saveNote}><CheckCircle2 size={15}/> Save note</button><button className="primary-btn" onClick={exportCase}><Download size={15}/> Export case</button></div><p className="muted tiny" role="status">{savedNotice||"Save locally or export a JSON case report."}</p></div></div>
      </div>}</div></>}
      {tab==="model"&&<><div className="page-heading"><div><div className="eyebrow">MODEL RESEARCH / RELIABILITY</div><h1>When a fraud model stops working</h1><p>Why time-aware validation matters more than a single impressive score.</p></div><Badge kind="amber">Post-hoc research · no live predictions</Badge></div>
       <div className="caution"><Info size={19}/><span>Performance around time step 43 motivated this research. Later periods were already inspected, so adaptive test replay is exploratory—not independent proof of generalization.</span></div>
       <div className="three-card-grid"><div className="panel"><div className="eyebrow">RESEARCH-SELECTED CANDIDATE · LAG 2</div><h2>Expanding-history XGBoost</h2><p className="muted small">Depth 3 · 150 trees · learning rate 0.05. Retrains with more history as labels are assumed to mature.</p><Metric label="Mean forward validation AP" value="0.8140" description="Steps 35, 37, 39" emphasis/></div>
         <div className="panel"><div className="eyebrow">LATER-PERIOD WARNING</div><h2>Sharp ranking collapse</h2><Metric label="Original-model AP · step 42" value="0.8142" description="→ 0.0265 at step 43"/><p className="muted small">The observed known-illicit rate also changed. This is not automatically proof of concept drift.</p></div>
         <div className="panel"><div className="eyebrow">WHAT THE APP SCORES SHOW</div><h2>Historical frozen model</h2><p className="muted small">The case-review scores are from the saved named-feature transaction-versus-graph comparison. The adaptive research candidate is <strong>not</strong> silently substituted into them.</p><Badge kind="blue">Source-linked</Badge></div></div>
       <div className="panel chart-panel"><div className="section-heading"><h3>Generalization: original frozen model</h3><Badge>Known-label AP</Badge></div><p className="muted small">Average Precision and known-illicit prevalence by time step, from the project's recorded evaluation.</p><div className="chart-box"><ResponsiveContainer width="100%" height="100%"><LineChart data={STEP_METRICS} margin={{top:18,right:16,bottom:6,left:-20}}><CartesianGrid stroke="#253957" strokeDasharray="3 3"/><XAxis dataKey="step" stroke="#a5bdd4"/><YAxis domain={[0,1]} stroke="#a5bdd4"/><Tooltip contentStyle={{background:"#142238",border:"1px solid #3d5875",borderRadius:12,color:"white"}}/><Legend/><ReferenceLine x={43} stroke="#f6c176" strokeDasharray="6 4"/><Line type="monotone" dataKey="ap" stroke="#7ca7ff" name="Average Precision" strokeWidth={3} dot={{r:4}}/><Line type="monotone" dataKey="prevalence" stroke="#f2b16f" name="Known illicit proportion" strokeWidth={2} strokeDasharray="4 4" dot={{r:3}}/></LineChart></ResponsiveContainer></div>
       <p className="muted small">At step 46 only <strong>two</strong> known illicit cases exist; don't overinterpret single-period AP changes. Outcomes are incomplete, and unknown does not mean legitimate.</p></div>
       <div className="panel chart-panel"><h3>Regularization and label-delay scenarios</h3><p className="muted small">Validation-selected model for each hypothetical label delay. These are scenarios, not measured label arrival times.</p>
         <div className="chart-box compact"><ResponsiveContainer width="100%" height="100%"><BarChart data={LAG_RESULTS} margin={{left:-20,right:10}}><CartesianGrid stroke="#253957" strokeDasharray="3 3"/><XAxis dataKey="lag" stroke="#a5bdd4"/><YAxis domain={[0,1]} stroke="#a5bdd4"/><Tooltip contentStyle={{background:"#142238",border:"1px solid #3d5875",borderRadius:12}}/><Legend/><Bar dataKey="mean" name="Mean validation AP" fill="#7ca7ff" radius={[6,6,0,0]}/><Bar dataKey="worst" name="Worst period AP" fill="#f0af72" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></div>
        <div className="lag-notes">{LAG_RESULTS.map(x=><div key={x.lag}><strong>{x.lag}</strong><span className="muted small">{x.strategy}</span></div>)}</div>
       </div>
       <div className="panel"><div className="section-heading"><h3>What can an analyst review?</h3><Badge>Realistic queue limits</Badge></div><p className="muted small">Recorded validation results for the expanding-history, two-step-delay candidate across steps 35, 37 and 39. Unknown-label transactions also consume analyst review capacity.</p><div className="capacity-row"><label htmlFor="capacity">Review capacity</label><select id="capacity" value={capacity} onChange={e=>setCapacity(e.target.value)}><option value="1">Top 1% of all traffic</option><option value="5">Top 5% of all traffic</option><option value="10">Top 10% of all traffic</option></select></div><div className="metric-grid"><Metric label="Queued for review" value={CAPACITY[capacity].reviewed.toLocaleString()}/><Metric label="Known illicit captured" value={CAPACITY[capacity].illicit+" / 303"} description="Across these three validation buckets" emphasis/><Metric label="Unknown outcomes queued" value={CAPACITY[capacity].unknown.toLocaleString()} description={CAPACITY[capacity].licit+" known licit also selected"}/></div><p className="muted small">Recall here refers only to cases with known labels. True population recall cannot be established.</p></div></>}
      {tab==="about"&&<><div className="page-heading"><div><div className="eyebrow">ABOUT THE PROJECT</div><h1>FraudGraph, explained simply</h1><p>Bitcoin transfers form a network. FraudGraph asks whether those relationships can help analysts prioritize which transactions deserve closer inspection.</p></div></div>
        <div className="panel prose"><h2>What does the model do?</h2><p>Every node represents a Bitcoin <strong>transaction</strong>, and a directed link indicates a documented transaction-to-transaction connection in Elliptic++. Our model combines transaction-level attributes (like size, fees and BTC amounts) with graph characteristics (like number of connections and PageRank).</p><h2>What did the project find?</h2><p>On the original held-out time steps, graph features improved named-feature XGBoost AP from <strong>0.4239 to 0.5240</strong>. Adding anonymized local features increased pooled AP but did not prevent the later collapse. Subsequent experiments found that updating training history can help retrospectively, but performance remains unstable.</p><h2>Why isn't this a fraud-verdict machine?</h2><p>Most real dataset transactions have unknown outcomes. We don't know who owns the underlying wallets, and dataset transaction identifiers are not public Bitcoin transaction hashes. Scores can rank cases for review but cannot establish legal guilt, losses avoided, or what a new live transaction would do without a new validated data pipeline.</p><h2>What can you do in this app?</h2><p>Select real transaction examples, view source-backed predecessor/successor networks, compare model scores, inspect the few recorded SHAP explanations, save a review note in your browser, or export a case as JSON. All decisions remain with a human.</p><div className="source-links"><a href="https://github.com/Thizisfranklin/FraudGraph/blob/main/reports/cases.csv" target="_blank" rel="noreferrer">Saved case evidence <ExternalLink size={14}/></a><a href="https://github.com/Thizisfranklin/FraudGraph/blob/main/docs/ROBUSTNESS_AND_ANALYST_EVALUATION.md" target="_blank" rel="noreferrer">Experimental methodology <ExternalLink size={14}/></a><a href="https://github.com/git-disl/EllipticPlusPlus" target="_blank" rel="noreferrer">Original dataset <ExternalLink size={14}/></a></div></div></>}
    </main></div><footer className="footer">FraudGraph Investigator · React research application · No live blockchain lookup · Not financial, legal or law-enforcement advice</footer>
  </div>;
}
export default App;

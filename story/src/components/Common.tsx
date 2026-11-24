import React from "react";
import {motion} from "framer-motion";
import {ArrowDownRight, ArrowRight, BookOpen, Info, ExternalLink} from "lucide-react";
import type {Metric} from "../data/data";
import {data} from "../data/data";

export const m = (v:number|null|undefined, digits=3):string =>
  v===null||v===undefined||!Number.isFinite(v)?"-- awaiting data --":Number(v).toFixed(digits);
export const count = (v:number|null|undefined):string =>
  v===null||v===undefined||!Number.isFinite(v)?"-- awaiting data --":Number(v).toLocaleString("en-US");
export const pct = (v:number|null|undefined, digits=1):string =>
  v===null||v===undefined||!Number.isFinite(v)?"-- awaiting data --":(100*v).toFixed(digits)+"%";
export const statText = (metric:Metric,digits=3) => metric.status==="awaiting"?metric.display:m(metric.value,digits);
export const sourceUrl = (relative:string) => data.repository+"/blob/main/"+relative;

export function SmallTag({children,tone="pink"}:{children:React.ReactNode;tone?:"pink"|"teal"|"amber"|"quiet"}) {
 return <span className={"chip chip-"+tone}>{children}</span>;
}
export function Fact({label,value,detail,large=false}:{label:string;value:React.ReactNode;detail?:string;large?:boolean}) {
 return <div className={"fact "+(large?"fact-large":"")}><span className="fact-label">{label}</span><strong>{value}</strong>{detail&&<span className="fact-detail">{detail}</span>}</div>;
}
export function SectionTitle({eyebrow,title,children}:{eyebrow:string;title:string;children?:React.ReactNode}) {
 return <div className="section-heading"><span className="eyebrow">{eyebrow}</span><h2>{title}</h2>{children&&<p>{children}</p>}</div>;
}
export function ResearchNote({children,source}:{children:React.ReactNode;source?:string}) {
 return <div className="research-note"><Info size={16} aria-hidden/><div>{children}{source&&<a href={sourceUrl(source)} target="_blank" rel="noreferrer">Evidence <ExternalLink size={12}/></a>}</div></div>;
}
export function SourceLink({path,children}:{path:string;children:React.ReactNode}) {
 return <a className="source-link" href={sourceUrl(path)} target="_blank" rel="noreferrer">{children}<ExternalLink size={13} aria-hidden/></a>;
}
export function DepthCard({children,className=""}:{children:React.ReactNode;className?:string}) {
 return <motion.div className={"depth-card "+className} initial={{opacity:0,y:34,rotateX:5}}
 whileInView={{opacity:1,y:0,rotateX:0}} viewport={{once:true,amount:.18}}
 transition={{duration:.65,ease:[.22,1,.36,1]}}>{children}</motion.div>;
}
export function SelectChips<T extends string|number>({label,values,value,onChange,format}:{label:string;values:readonly T[];value:T;onChange:(v:T)=>void;format?:(v:T)=>string}) {
 return <div className="field-stack"><span className="field-caption">{label}</span><div className="segmented" role="group" aria-label={label}>{values.map(v=><button type="button" key={String(v)} aria-pressed={value===v} className={value===v?"selected":""} onClick={()=>onChange(v)}>{format?format(v):String(v)}</button>)}</div></div>;
}
export function Receipts({paths}:{paths:string[]}) {
 return <div className="receipts"><span><BookOpen size={14}/> Research receipts</span>{paths.map(path=><SourceLink key={path} path={path}>{path.split("/").at(-1)}</SourceLink>)}</div>;
}
export function SceneHint({children}:{children:React.ReactNode}){return <p className="scene-hint"><ArrowDownRight size={15}/>{children}</p>}
export const EMPTY="-- awaiting data --";

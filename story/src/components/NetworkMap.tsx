import React, {useMemo, useState} from "react";
import {ReactFlow, Background, Controls, MarkerType} from "@xyflow/react";
import {Network, Unplug} from "lucide-react";
import type {TransactionCase} from "../data/data";

export function NetworkMap({record,compact=false}:{record:TransactionCase;compact?:boolean}) {
 const [selected,setSelected]=useState<string|null>(null);
 const elements=useMemo(()=>{
  const network=record.network;
  const nodeList=network?.nodes||[];
  const others=nodeList.filter(n=>!n.focus&&n.id!==record.id);
  const center=nodeList.find(n=>n.focus)||nodeList.find(n=>n.id===record.id);
  const nodes=(center?[center]:[]).concat(others).map((n,i)=>{
   const focus=n.id===record.id;
   const angle=((i-1)/Math.max(others.length,1))*Math.PI*2-Math.PI/2;
   const x=focus?350:350+205*Math.cos(angle), y=focus?225:225+145*Math.sin(angle);
   const palette:Record<number,string>={1:"#ff779c",2:"#51dfcc",3:"#a4a9c0"};
   return {id:n.id,position:{x,y},draggable:false,selectable:true,data:{label:focus?"TX "+record.id:"TX "+n.id},
     style:{background:focus?"#ce3a91":"#1a233f",border:"1px solid "+(focus?"#ff9dd0":palette[n.retrospectiveClass]||palette[3]),
       color:"#fbf7ff",fontSize:compact?10:11,fontFamily:"monospace",fontWeight:focus?900:600,
       borderRadius:focus?25:12,boxShadow:focus?"0 0 30px #ff58ae8a":"0 3px 14px #0009",
       width:focus?144:117,padding:focus?15:10}};
  });
  const edges=(network?.edges||[]).map((e,i)=>({id:String(i),source:e.source,target:e.target,type:"smoothstep",animated:!compact,
    style:{stroke:"#66e8da",strokeWidth:1.6},markerEnd:{type:MarkerType.ArrowClosed,color:"#66e8da"}}));
  return {nodes,edges};
 },[record.id,record.network,compact]);
 const selectedNode=record.network?.nodes.find(n=>n.id===selected);
 if(!elements.nodes.length)return <div className="network-empty"><Unplug/><p>No source-backed neighborhood is available for this case.</p></div>;
 return <div className={"network-view "+(compact?"network-compact":"")}>
   <ReactFlow nodes={elements.nodes} edges={elements.edges} fitView fitViewOptions={{padding:.21}} nodesConnectable={false} nodesDraggable={false}
     minZoom={.25} maxZoom={1.6} zoomOnScroll={false} panOnScroll={false} panOnDrag
     onNodeClick={(_,node)=>setSelected(node.id)} proOptions={{hideAttribution:true}}>
      <Background color="#554470" gap={22} size={1}/><Controls showInteractive={false}/>
   </ReactFlow>
   <div className="map-legend"><span className="legend-selected"/> Focus <span className="legend-illicit"/> Dataset illicit <span className="legend-licit"/> Dataset licit <span className="legend-unknown"/> Unknown</div>
   {selectedNode&&<div className="node-receipt" role="status"><Network size={14}/> TX {selectedNode.id} · time step {selectedNode.timeStep} · {selectedNode.retrospectiveClass===1?"Dataset illicit":selectedNode.retrospectiveClass===2?"Dataset licit":"Unknown outcome"}</div>}
 </div>;
}

import {useEffect,useRef,useState} from "react";
import {Headphones,Music2,Pause,Play,SkipForward,Volume2,VolumeX,X} from "lucide-react";

/**
 * NEON FM — self-contained, original synthesized background loops.
 * No external streams, audio assets, cookies or analytics. Explicit user gesture required.
 * The soundtrack is decorative: it does not change any scientific data or interactions.
 */
const CHANNELS=[
 {name:"Afro Sunset",style:"Afro-inspired groove",bpm:104,root:196,scale:[0,3,5,7,10],bass:[0,0,7,5],melody:[0,7,10,7,5,3,7,5]},
 {name:"Network Pulse",style:"Afro-house pulse",bpm:118,root:164.81,scale:[0,2,5,7,10],bass:[0,7,5,7],melody:[0,5,7,12,10,7,5,2]},
 {name:"Midnight Signal",style:"Ambient / cinematic",bpm:76,root:146.83,scale:[0,3,5,7,10],bass:[0,0,5,3],melody:[0,3,7,10,7,5,3,0]},
 {name:"City After Dark",style:"Electronic / highlife-inspired",bpm:110,root:220,scale:[0,2,4,7,9],bass:[0,7,9,4],melody:[0,4,9,7,12,9,7,4]},
] as const;

const channelForChapter=(chapter:number)=>chapter<=2?0:chapter<=5?1:chapter<=8?2:3;
const pitch=(root:number,semitones:number)=>root*Math.pow(2,semitones/12);

function voice(ctx:AudioContext,frequency:number,at:number,length:number,volume:number,type:OscillatorType="sine"){
 const osc=ctx.createOscillator(),gain=ctx.createGain();
 osc.type=type;osc.frequency.setValueAtTime(frequency,at);
 gain.gain.setValueAtTime(0,at);
 gain.gain.linearRampToValueAtTime(volume,at+.012);
 gain.gain.exponentialRampToValueAtTime(.0001,at+length);
 osc.connect(gain);gain.connect(ctx.destination);
 osc.start(at);osc.stop(at+length+.02);
}

export default function NeonFM({chapter}:{chapter:number}){
 const [open,setOpen]=useState(false);
 const [mode,setMode]=useState<"adaptive"|"manual">("adaptive");
 const [manual,setManual]=useState(0);
 const [playing,setPlaying]=useState(false);
 const [volume,setVolume]=useState(.28);
 const [error,setError]=useState("");
 const ctx=useRef<AudioContext|null>(null);
 const beat=useRef(0);
 const selected=mode==="adaptive"?channelForChapter(chapter):manual;
 const selectedRef=useRef(selected);
 selectedRef.current=selected;

 // Audio can only be enabled via an intentional click; no autoplay on entry/scroll.
 const toggle=async()=>{
  if(playing){setPlaying(false);return;}
  try{
   if(!ctx.current)ctx.current=new AudioContext();
   await ctx.current.resume();
   if(ctx.current.state!=="running")throw new Error("Audio unavailable");
   setError("");setPlaying(true);
  }catch{setError("Audio is unavailable in this browser.");setPlaying(false);}
 };
 useEffect(()=>{
  if(!playing||!ctx.current)return;
  const audio=ctx.current;
  let stopped=false;
  beat.current=0;
  let next=audio.currentTime+.08;
  const tick=()=>{
   if(stopped||audio.state!=="running")return;
   const channel=CHANNELS[selectedRef.current];
   const eighth=60/channel.bpm/2;
   // Modest lookahead for steady rhythm; changes take effect on the next beat.
   while(next<audio.currentTime+.12){
    const step=beat.current%16,bar=Math.floor(beat.current/16);
    const slow=selectedRef.current===2;
    if(step%4===0){
     voice(audio,channel.root/2*(step%8===0?1:Math.pow(2,channel.bass[Math.floor(step/4)]/12)),next,slow?.36:.23,volume*.095,"sine");
    }
    if(!slow&&step%4===0)voice(audio,54,next,.14,volume*.075,"triangle");
    if(!slow&&step%4===2)voice(audio,190,next,.07,volume*.024,"triangle");
    if(!slow&&(step%2===1||step===6||step===14))voice(audio,920+(step%3)*75,next,.025,volume*.012,"sine");
    if(step%2===0&&(slow?step%4===0:true)){
     const note=channel.melody[Math.floor(step/2)%8];
     voice(audio,pitch(channel.root,note+12+(bar%2?0:0)),next,slow?.66:.22,volume*(slow?.032:.041),slow?"sine":"triangle");
    }
    beat.current++;next+=eighth;
   }
  };
  const timer=window.setInterval(tick,50);tick();
  return()=>{stopped=true;window.clearInterval(timer);};
 },[playing,selected,volume]);
 useEffect(()=>{
  const onVisibility=()=>{if(document.hidden)setPlaying(false);};
  document.addEventListener("visibilitychange",onVisibility);
  return()=>{document.removeEventListener("visibilitychange",onVisibility);ctx.current?.close().catch(()=>{});ctx.current=null;};
 },[]);
 const skip=()=>{
  setMode("manual");
  setManual((selected+1)%CHANNELS.length);
 };
 return <div className="neon-fm" aria-label="Neon FM optional soundtrack">
  <button className="neon-fm-toggle" aria-expanded={open} aria-controls="neon-fm-panel" onClick={()=>setOpen(v=>!v)}>
   <Headphones size={16}/><span>NEON FM</span><span className="neon-fm-status">{playing?"ON AIR":"OFF"}</span>
  </button>
  {open&&<div id="neon-fm-panel" className="neon-fm-panel">
   <div className="neon-fm-heading"><div><small>ORIGINAL SOUNDTRACK / NO STREAMING</small><strong>Neon FM</strong></div><button aria-label="Close Neon FM" onClick={()=>setOpen(false)}><X size={17}/></button></div>
   <p className="neon-fm-disclaimer">Optional generated instrumental loops, not commercial recordings. Audio begins only when you press Play.</p>
   <div className="neon-fm-current"><Music2 size={22}/><div><strong>{CHANNELS[selected].name}</strong><small>{CHANNELS[selected].style}</small></div></div>
   <div className="neon-fm-modes" role="group" aria-label="Music mode">
    <button aria-pressed={mode==="adaptive"} onClick={()=>setMode("adaptive")}>Follow chapters</button>
    <button aria-pressed={mode==="manual"} onClick={()=>setMode("manual")}>Manual</button>
   </div>
   <label className="neon-fm-label" htmlFor="neon-fm-channel">Channel</label>
   <select id="neon-fm-channel" value={selected} onChange={e=>{setMode("manual");setManual(Number(e.target.value));}}>
    {CHANNELS.map((channel,i)=><option key={channel.name} value={i}>{channel.name} — {channel.style}</option>)}
   </select>
   <div className="neon-fm-controls">
    <button aria-label={playing?"Pause music":"Play music"} onClick={toggle}>{playing?<Pause size={19}/>:<Play size={19}/>}</button>
    <button aria-label="Next channel" onClick={skip}><SkipForward size={19}/></button>
    <label htmlFor="neon-fm-volume">{volume===0?<VolumeX size={17}/>:<Volume2 size={17}/>}</label>
    <input id="neon-fm-volume" aria-label="Music volume" type="range" min="0" max="0.6" step="0.02" value={volume} onChange={e=>setVolume(Number(e.target.value))}/>
   </div>
   <small className="neon-fm-hint">{mode==="adaptive"?"Tracks follow the chapter you are reading.":"Track stays selected as you explore."}</small>
   {error&&<p className="neon-fm-error" role="alert">{error}</p>}
  </div>}
 </div>;
}

import React, {useEffect,useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';
type Project={id:string;name:string};
type Document={id:string;title:string;content:string};
type Review={id:string;content:string;mode:string;approved:boolean};
const API=(import.meta.env.VITE_API_URL||'').replace(/\/$/,'');
function App(){
 const [session,setSession]=useState<{token:string;user:string}|null>(null);
 const [code,setCode]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 async function login(e:React.FormEvent){
  e.preventDefault();setBusy(true);setError('');
  try{const r=await fetch(API+'/api/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({access_code:code})});const data=await r.json();if(!r.ok)throw new Error(data.detail||'Login failed');setSession(data);setCode('');}
  catch(e){setError(e instanceof Error?e.message:'Login failed')}finally{setBusy(false)}
 }
 return <main><h1>Construction scope assistant</h1><p>InQI-inspired standalone demonstration · synthetic data only · no InQI integration</p><p><strong>Public demo: FIXTURE MODE — deterministic results, not live AI.</strong></p>{session?<><p>Signed in as {session.user} <button onClick={()=>setSession(null)}>Sign out</button></p><Workspace key={session.token} token={session.token}/></>:<form onSubmit={login}><label>Private demo access code <input type="password" value={code} onChange={e=>setCode(e.target.value)} required maxLength={256} autoComplete="off"/></label><button disabled={busy}>Enter demo</button><p>Request an access code from the demo owner. Sessions expire after 30 minutes.</p>{error&&<p role="alert" className="error">{error}</p>}</form>}</main>;
}
function Workspace({token}:{token:string}){
 const [projects,setProjects]=useState<Project[]>([]),[project,setProject]=useState('');
 const [docs,setDocs]=useState<Document[]>([]),[review,setReview]=useState<Review|null>(null);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[saved,setSaved]=useState('');
 const [requestKey,setRequestKey]=useState('');
 async function api(path:string,method='GET',body?:unknown){
  const r=await fetch(API+'/api'+path,{method,headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});
  const data=await r.json();if(!r.ok)throw new Error(data.detail||'Request failed');return data;
 }
 useEffect(()=>{let live=true;api('/projects').then(p=>{if(live)setProjects(p)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[]);
 useEffect(()=>{let live=true;setDocs([]);setReview(null);setSaved('');setError('');if(project)api(`/projects/${project}/documents`).then(d=>{if(live)setDocs(d)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[project]);
 async function act(action:'generate'|'approve'|'save'){
  setBusy(true);setError('');try{
   const base=`/projects/${project}/reviews`;
   if(action==='generate'){setReview(null);setSaved('');const r=await api(base,'POST');setReview(r);setRequestKey(crypto.randomUUID());}
   else if(review&&action==='approve'){await api(`${base}/${review.id}/approve`,'POST');setReview({...review,approved:true});}
   else if(review){const report=await api(`${base}/${review.id}/save`,'POST',{request_key:requestKey});setSaved(report.id);}
  }catch(e){setError(e instanceof Error?e.message:'Request failed')}finally{setBusy(false)}
 }
 return <><label>Authorized project <select disabled={busy} value={project} onChange={e=>setProject(e.target.value)}><option value="">Select a project</option>{projects.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>{docs.map(d=><article key={d.id}><h2>{d.title}</h2><small>{d.id}</small><p>{d.content}</p></article>)}<button disabled={busy||!docs.length} onClick={()=>act('generate')}>Generate scope review</button>{busy&&<p role="status">Processing…</p>}{error&&<p role="alert" className="error">{error}</p>}{review&&<section><h2>Scope review</h2><strong>{review.mode==='fixture'?'FIXTURE MODE — not AI-generated':`AI-assisted · ${review.mode}`}</strong><pre>{review.content}</pre><p>Review the content before approving. Approval applies to this exact stored report.</p><button disabled={busy||review.approved} onClick={()=>act('approve')}>{review.approved?'Approved':'Approve report'}</button><button disabled={busy||!review.approved} onClick={()=>act('save')}>{saved?'Retry save (same request key)':'Save approved report'}</button>{saved&&<p role="status">Saved report: {saved}</p>}</section>}</>;
}
createRoot(document.getElementById('root')!).render(<App/>);

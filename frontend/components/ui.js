import {state} from '../hooks/state.js';
export const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const pct=value=>`${Math.round((value||0)*100)}%`;
export const date=value=>new Date(String(value).endsWith('Z')?value:value+'Z').toLocaleString(undefined,{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
export function toast(message,error=false){const el=document.createElement('div');el.className='toast'+(error?' error':'');el.textContent=message;document.querySelector('#toasts').append(el);setTimeout(()=>el.remove(),6500);}
export function empty(title,body='Try another filter or check back after the next data sync.'){return `<div class="empty"><span class="empty-icon">◇</span><h3>${esc(title)}</h3><p>${esc(body)}</p></div>`;}
export function heading(kicker,title,description='',actions=''){return `<header class="page-heading"><div><p class="eyebrow">${esc(kicker)}</p><h1>${esc(title)}</h1><p class="muted">${esc(description)}</p></div>${actions}</header>`;}
export function field(label,name,type='text',value='',extra=''){return `<label>${esc(label)}<input name="${esc(name)}" type="${type}" value="${esc(value)}" ${extra}></label>`;}
export function select(label,name,options,value=''){return `<label>${esc(label)}<select name="${esc(name)}">${options.map(([id,text])=>`<option value="${esc(id)}" ${String(id)===String(value)?'selected':''}>${esc(text)}</option>`).join('')}</select></label>`;}
export function formError(form,error){const el=form.querySelector('.form-error');if(el)el.textContent=error.message;toast(error.message,true);}
export function formAction(form,fn){form.addEventListener('submit',async e=>{e.preventDefault();const button=form.querySelector('[type="submit"]');button.disabled=true;const error=form.querySelector('.form-error');if(error)error.textContent='';try{await fn(Object.fromEntries(new FormData(form)));}catch(e){formError(form,e);}finally{button.disabled=false;}});}
export function dialog(title,html){document.querySelector('#dialog-content').innerHTML=`<h2 id="dialog-title">${esc(title)}</h2>${html}`;document.querySelector('#dialog').showModal();}
export async function confirmAction(title,description){
  dialog(title,`<p>${esc(description)}</p><div class="actions"><button id="confirm-yes" class="button danger">Confirm</button><button id="confirm-no" class="button secondary">Cancel</button></div>`);
  return new Promise(resolve=>{
    const d=document.querySelector('#dialog');let done=false;
    const finish=result=>{if(done)return;done=true;d.close();d.removeEventListener('close',closed);resolve(result);};
    const closed=()=>finish(false);d.addEventListener('close',closed);
    document.querySelector('#confirm-yes').onclick=()=>finish(true);document.querySelector('#confirm-no').onclick=()=>finish(false);
  });
}
export function chart(id,type,labels,values,label='Probability'){
  const canvas=document.getElementById(id);if(!canvas)return;
  if(!window.Chart){canvas.outerHTML=empty('Chart unavailable','Numerical results are shown alongside the chart.');return;}
  const isLine=type==='line';
  const chart=new window.Chart(canvas,{type,data:{labels,datasets:[{label,data:values,backgroundColor:isLine?'rgba(16,185,129,.13)':['#10b981','#e4b453','#5d8ee8'],borderColor:'#10b981',borderWidth:isLine?2:0,borderRadius:6,fill:isLine,tension:.3}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${label}: ${Number(c.raw).toFixed(1)}`}}},scales:{x:{grid:{display:false},ticks:{color:'#8d9db4'}},y:{beginAtZero:true,ticks:{color:'#8d9db4'},grid:{color:'rgba(145,165,185,.1)'}}}}});state.charts.push(chart);
}
export function formGuide(values=[]){return `<div class="form-guide" aria-label="Last five results, oldest first">${values.map(x=>`<span class="form-${x}">${x}</span>`).join('')||'<span class="muted">No previous matches</span>'}</div>`;}
export function matchCard(m){const p=m.prediction;return `<article class="match-card">
 <div class="card-meta"><span>${esc(m.league)}</span><span class="pill ${m.source==='sample'?'amber':''}">${esc(m.source==='sample'?'SYNTHETIC DEMO':m.status)}</span></div>
 <a class="match-link" href="#match/${m.id}"><div class="teams"><div><span class="team-badge">${esc(m.home.slice(0,2).toUpperCase())}</span><strong>${esc(m.home)}</strong></div><span class="versus">${m.status==='FINISHED'?`${m.home_goals} : ${m.away_goals}`:'VS'}</span><div><span class="team-badge away">${esc(m.away.slice(0,2).toUpperCase())}</span><strong>${esc(m.away)}</strong></div></div></a>
 <p class="match-time">${date(m.kickoff)}</p>
 ${p?`<div class="prob-row"><span>Home <b>${pct(p.probabilities.Home)}</b></span><span>Draw <b>${pct(p.probabilities.Draw)}</b></span><span>Away <b>${pct(p.probabilities.Away)}</b></span></div><div class="prob-strip" aria-hidden="true"><i style="width:${p.probabilities.Home*100}%"></i><i style="width:${p.probabilities.Draw*100}%"></i><i style="width:${p.probabilities.Away*100}%"></i></div><div class="card-foot"><span><i class="dot"></i> ${esc(p.outcome)} · ${esc(p.confidence)} confidence</span><a href="#match/${m.id}">Analysis ↗</a></div>`:'<p class="muted">No pre-match prediction recorded.</p>'}
 </article>`;}
export function metricsCards(metrics){const groups=Object.entries(metrics.groups);return groups.length?groups.map(([name,g])=>`<article class="stat"><span>${esc(name)}</span><strong>${pct(g.accuracy)}</strong><small>${g.correct}/${g.total} correct · Brier ${g.brier.toFixed(3)}</small></article>`).join(''):empty('Accuracy starts with results','No eligible completed matches yet. Sync results after fixtures finish.');}

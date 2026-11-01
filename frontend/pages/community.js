import {api,send} from '../services/api.js';
import {state,go} from '../hooks/state.js';
import {heading,esc,date,pct,empty,matchCard,toast,metricsCards,chart} from '../components/ui.js';
export async function historyPage(root){
 const metrics=await api('/metrics');let offset=0;
 root.innerHTML=heading('PREDICTION ARCHIVE','A model should show its work.','Frozen predictions, final scores, and honest performance measurement.')+`<div class="stats-grid">${metricsCards(metrics)}</div><section class="panel"><h2>Prospective accuracy over time</h2><div id="accuracy-content"></div><p class="fine-print">${esc(metrics.note)}</p></section><div id="history-list" class="match-grid"></div><div class="pager"><button id="prev-history" class="button secondary">← Previous</button><span id="history-page"></span><button id="next-history" class="button secondary">Next →</button></div>`;
 if(metrics.trend.length){document.querySelector('#accuracy-content').innerHTML='<div class="chart-container"><canvas id="accuracy" aria-label="Cumulative prediction accuracy" role="img"></canvas></div>';const trend=metrics.trend.filter(x=>x.source==='live');if(trend.length){let hits=0;chart('accuracy','line',trend.map(x=>x.date),trend.map((x,i)=>{hits+=x.correct;return hits/(i+1)*100;}),'Live accuracy (%)');}else document.querySelector('#accuracy-content').innerHTML=empty('No live result history','Synthetic or manual results do not establish real-world model performance.');}
 else document.querySelector('#accuracy-content').innerHTML=empty('No prospective results yet','The chart begins when a pre-kickoff prediction is evaluated after a result.');
 async function load(){const data=await api('/history?offset='+offset);document.querySelector('#history-list').innerHTML=data.items.map(matchCard).join('')||empty('No predictions');document.querySelector('#prev-history').disabled=offset===0;document.querySelector('#next-history').disabled=data.items.length<50;document.querySelector('#history-page').textContent=`Page ${offset/50+1}`;}
 document.querySelector('#prev-history').onclick=async()=>{offset=Math.max(0,offset-50);try{await load();}catch(e){toast(e.message,true);}};
 document.querySelector('#next-history').onclick=async()=>{offset+=50;try{await load();}catch(e){toast(e.message,true);}};await load();
}
export async function favoritesPage(root){
 root.innerHTML=heading('YOUR CLUBS','Keep your teams close.','Save favorite teams to your account and manage your club list.')+`<div class="team-grid">${state.catalog.teams.map(t=>`<article class="panel team-panel"><span class="team-badge">${esc(t.name.slice(0,2))}</span><h3>${esc(t.name)}</h3><button class="button ${t.favorite?'':'secondary'} favorite" data-id="${t.id}" aria-pressed="${t.favorite}">${t.favorite?'★ Favorited':'☆ Add favorite'}</button></article>`).join('')||empty('No teams available')}</div>`;
 document.querySelectorAll('.favorite').forEach(b=>b.onclick=async()=>{try{toast((await send('/favorites/'+b.dataset.id)).message);state.catalog=await api('/catalog');go('favorites');}catch(e){toast(e.message,true);}});
}
export async function leaderboardPage(root){
 const rows=await api('/leaderboard');
 root.innerHTML=heading('THE COMMUNITY','Football instincts, measured.','3 points per correct pick. Rankings reflect both participation and accuracy.')+`<section class="panel"><div class="table-wrap"><table><thead><tr><th>Rank</th><th>Player / Model</th><th>Correct</th><th>Completed picks</th><th>Accuracy</th><th>Points</th></tr></thead><tbody>${rows.map((r,i)=>`<tr><td>${i+1}</td><td><b>${esc(r.name)}</b> ${r.kind==='AI'?'<span class="pill">AI</span>':''}</td><td>${r.correct}</td><td>${r.total}</td><td>${pct(r.accuracy)}</td><td class="emerald">${r.points}</td></tr>`).join('')}</tbody></table></div>${rows.length?'':empty('The table is open','Make a pick on an upcoming match. It is scored after the result is recorded.')}<p class="fine-print">AI rows are separated by data source. Participants may choose different matches; this is a points game, not a controlled model benchmark.</p></section>`;
}
export async function notificationsPage(root){
 const rows=await api('/notifications');
 root.innerHTML=heading('FULL-TIME UPDATES','Stay in the loop.','Results for the matches you follow. Updates refresh every 60 seconds.')+`<section class="panel">${rows.map(n=>`<article class="notification ${n.read?'read':''}"><div><span class="pill">${n.read?'READ':'NEW'}</span><h3><a href="#match/${n.match_id}">${esc(n.text)}</a></h3><p class="muted">${date(n.created_at)}</p></div>${n.read?'':`<button class="button secondary mark-read" data-id="${n.id}">Mark read</button>`}</article>`).join('')||empty('All quiet for now','Follow upcoming matches to receive in-app notifications when results are synced or recorded.')}</section>`;
 document.querySelectorAll('.mark-read').forEach(b=>b.onclick=async()=>{try{await send('/notifications/'+b.dataset.id+'/read');go('notifications');}catch(e){toast(e.message,true);}});
}

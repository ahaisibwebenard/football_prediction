import {api} from '../services/api.js';
import {state} from '../hooks/state.js';
import {empty,esc,heading,pct,date} from '../components/ui.js';

const todayUtc=()=>new Date().toISOString().slice(0,10);
function shiftDay(value,amount){const day=new Date(`${value}T00:00:00Z`);day.setUTCDate(day.getUTCDate()+amount);return day.toISOString().slice(0,10);}

export async function topPredictionsPage(root){
 let selectedDate=todayUtc();
 root.innerHTML=heading('DAILY MODEL WATCHLIST','Hottest 10','The ten highest-ranked upcoming fixtures for a single day. Each row is one match, with all available result and goal markets.','<a href="#dashboard" class="button secondary">Match center</a>')+
 `<section class="hot-intro"><div><span class="pill">SYSTEM FORECASTS</span><p>Choose a UTC match date. Fixtures are ranked by their strongest model probability; each fixture appears once and shows the full market breakdown.</p></div><div class="hot-count"><strong id="hot-count">0</strong><span>fixtures today</span></div></section><form id="hot-date-form" class="hot-date-form"><button class="button secondary" type="button" id="hot-prev" aria-label="Previous day">← Previous day</button><label for="hot-date">Match date (UTC)</label><input id="hot-date" name="date" type="date" value="${selectedDate}" required><button class="button" type="submit">Show predictions</button><button class="button secondary" type="button" id="hot-next" aria-label="Next day">Next day →</button></form><p id="hot-summary" class="muted"></p><div id="hot-list"></div><p class="hot-disclaimer">Probabilities are model estimates, not certainties or betting advice. Corner predictions are not shown because the configured source does not supply historical corner counts.</p>`;

 const list=document.querySelector('#hot-list');
 const summary=document.querySelector('#hot-summary');
 const count=document.querySelector('#hot-count');
 const dateInput=document.querySelector('#hot-date');

 function renderFixture(item){
  const prediction=item.prediction||{};
  const markets=item.markets||{};
  const result=markets.result||prediction.probabilities||{};
  const goals=markets.goals||prediction.goal_lines||{};
  const btts=markets.both_teams_to_score||{yes:prediction.btts,no:1-(prediction.btts||0)};
  const line=(label,over,under)=>`<div class="hot-line"><span>${label}</span><b>Over ${pct(over)}</b><b>Under ${pct(under)}</b></div>`;
  return `<article class="hot-row"><div class="hot-rank">${String(item.rank).padStart(2,'0')}</div><div class="hot-fixture"><div class="hot-meta">${esc(item.country||'International')} · ${esc(item.league)} <span>${date(item.kickoff)}</span></div><a href="#match/${item.id}" class="hot-teams"><strong>${esc(item.home)}</strong><span>vs</span><strong>${esc(item.away)}</strong></a><p class="hot-score">Most likely score <b>${esc(prediction.scoreline||'—')}</b> (${pct(markets.most_likely_score_probability??prediction.scoreline_probability)}) · Expected goals ${Number(prediction.expected_goals?.home||0).toFixed(2)}–${Number(prediction.expected_goals?.away||0).toFixed(2)}</p><div class="hot-markets"><div class="hot-line"><span>Match result</span><b>Home ${pct(result.Home)}</b><b>Draw ${pct(result.Draw)}</b><b>Away ${pct(result.Away)}</b></div>${line('Total goals 1.5',goals.over_1_5,goals.under_1_5)}${line('Total goals 2.5',goals.over_2_5,goals.under_2_5)}${line('Total goals 3.5',goals.over_3_5,goals.under_3_5)}<div class="hot-line"><span>Both teams score</span><b>Yes ${pct(btts.yes)}</b><b>No ${pct(btts.no)}</b></div></div></div><div class="hot-pick"><small>STRONGEST MARKET</small><strong>${esc(item.best_market)}</strong><b>${pct(item.best_market_probability)}</b><div class="hot-meter"><span style="width:${Math.max(0,Math.min(100,item.best_market_probability*100))}%"></span></div><a href="#match/${item.id}">Full analysis ↗</a></div></article>`;
 }

 async function load(){
  list.innerHTML='<div class="skeleton"></div>';
  const result=await api('/predictions/top?date='+encodeURIComponent(selectedDate));
  count.textContent=String(result.items.length);
  summary.textContent=`${result.items.length} of 10 ranked · ${result.eligible_live_fixtures} eligible live fixtures on ${selectedDate} UTC`;
  list.innerHTML=result.items.length?`<div class="hot-list">${result.items.map(renderFixture).join('')}</div>`:empty('No live fixtures for this date',state.liveDataConfigured?'Choose another date with scheduled fixtures.':'Add a football-data.org API key in Admin → Site settings to load real fixtures and forecasts.');
 }

 document.querySelector('#hot-date-form').addEventListener('submit',async event=>{event.preventDefault();selectedDate=dateInput.value;try{await load();}catch(error){window.showError(error);}});
 document.querySelector('#hot-prev').onclick=async()=>{selectedDate=shiftDay(selectedDate,-1);dateInput.value=selectedDate;try{await load();}catch(error){window.showError(error);}};
 document.querySelector('#hot-next').onclick=async()=>{selectedDate=shiftDay(selectedDate,1);dateInput.value=selectedDate;try{await load();}catch(error){window.showError(error);}};
 await load();
}
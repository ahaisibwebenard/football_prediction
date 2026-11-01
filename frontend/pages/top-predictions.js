import {api} from '../services/api.js';
import {state} from '../hooks/state.js';
import {empty,esc,heading,pct,date} from '../components/ui.js';

export async function topPredictionsPage(root){
 const result=await api('/predictions/top');
 const items=result.items||[];
 root.innerHTML=heading('MODEL WATCHLIST','Hottest 10','The strongest estimated markets across upcoming, provider-sourced fixtures. Ranked by probability, not by guaranteed value.','<a href="#dashboard" class="button secondary">Match center</a>')+
 `<section class="hot-intro"><div><span class="pill">LIVE FIXTURES ONLY</span><p>Each fixture appears once, with its highest-probability result or goal market. Open a match for the full score distribution and model explanation.</p></div><div class="hot-count"><strong>${items.length}</strong><span>of 10 ranked</span></div></section>`+
 (items.length?`<div class="hot-list">${items.map(item=>{
  const prediction=item.prediction;
  const outcomes=prediction?.probabilities||{};
  const goals=prediction?.goal_lines||{};
  return `<article class="hot-row"><div class="hot-rank">${String(item.rank).padStart(2,'0')}</div><div class="hot-fixture"><div class="hot-meta">${esc(item.country||'International')} · ${esc(item.league)} <span>${date(item.kickoff)}</span></div><a href="#match/${item.id}" class="hot-teams"><strong>${esc(item.home)}</strong><span>vs</span><strong>${esc(item.away)}</strong></a><p class="hot-score">Most likely score <b>${esc(prediction?.scoreline||'—')}</b> · Expected goals ${Number(prediction?.expected_goals?.home||0).toFixed(2)}–${Number(prediction?.expected_goals?.away||0).toFixed(2)}</p><div class="hot-markets"><span>Home ${pct(outcomes.Home)}</span><span>Draw ${pct(outcomes.Draw)}</span><span>Away ${pct(outcomes.Away)}</span><span>O1.5 ${pct(goals.over_1_5)}</span><span>O2.5 ${pct(goals.over_2_5)}</span><span>BTTS ${pct(prediction?.btts)}</span></div></div><div class="hot-pick"><small>TOP MARKET</small><strong>${esc(item.best_market)}</strong><b>${pct(item.best_market_probability)}</b><div class="hot-meter"><span style="width:${Math.max(0,Math.min(100,item.best_market_probability*100))}%"></span></div><a href="#match/${item.id}">Full analysis ↗</a></div></article>`;
 }).join('')}</div>`:empty('No live predictions yet',state.liveDataConfigured?'No upcoming fixtures with saved forecasts were returned for your configured competitions.':'Add a football-data.org API key in Admin → Site settings to load real fixtures and forecasts.'))+
 `<p class="hot-disclaimer">Probabilities are model estimates, not certainties or betting advice. Corner predictions are not shown because the configured provider does not supply the historical corner data this model would need.</p>`;
}
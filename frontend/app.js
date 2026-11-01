import {api,send,token} from './services/api.js';
import {state,go,destroyCharts} from './hooks/state.js';
import {layout} from './components/layout.js';
import {toast,empty,esc} from './components/ui.js';
import {authPage} from './pages/auth.js';
import {dashboard} from './pages/dashboard.js';
import {topPredictionsPage} from './pages/top-predictions.js';
import {matchPage} from './pages/match.js';
import {historyPage,favoritesPage,notificationsPage} from './pages/community.js';
import {profilePage} from './pages/profile.js';
import {adminOverview,adminUsers,adminAudit,adminSettings,adminCatalog} from './pages/admin.js';

window.toggleTheme=()=>{const next=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=next;try{localStorage.setItem('predictpro-theme',next);}catch(e){/* Theme still changes in private storage modes. */}};
try{document.documentElement.dataset.theme=localStorage.getItem('predictpro-theme')||'light';}catch(e){/* Default theme is usable without local storage. */}
window.showError=e=>toast(e.message,true);
document.querySelector('#dialog-close').onclick=()=>document.querySelector('#dialog').close();
let rendering=false,queued=false;
async function route(){
 if(rendering){queued=true;return;}rendering=true;
 try{
  const path=location.hash.slice(1)||'dashboard';destroyCharts();document.querySelector('#dialog').close();
    const metadata=await api('/site');state.siteName=metadata.site_name;state.liveDataConfigured=metadata.live_data_configured;document.title=metadata.site_name+' · Football intelligence';
  if(['login','signup','forgot','reset'].includes(path.split('?')[0])){authPage(path);return;}
  const session=await api('/auth/me');state.user=session.user;state.impersonating=session.impersonating;
  if(state.user.must_change&&path!=='profile'){go('profile');return;}
  if(path.startsWith('admin')&&state.user.role!=='ADMIN'){go('dashboard');return;}
  document.querySelector('#app').innerHTML=layout(path);
  document.querySelector('#theme').onclick=()=>window.toggleTheme();
  document.querySelector('#menu').onclick=e=>{const open=document.querySelector('#sidebar').classList.toggle('open');e.currentTarget.setAttribute('aria-expanded',open);};
  document.querySelector('#logout').onclick=async()=>{try{await send('/auth/logout');state.user=null;token('');go('login');}catch(e){toast(e.message,true);}};
  if(state.impersonating)document.querySelector('#return-admin').onclick=async()=>{try{const s=await send('/admin/return');state.user=s.user;state.impersonating=false;go('admin');}catch(e){toast(e.message,true);}};
  const main=document.querySelector('#main');main.innerHTML='<div class="skeleton"></div><div class="match-grid"><div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div></div>';
  if(!state.user.must_change)state.catalog=await api('/catalog');
  const pages={'dashboard':dashboard,'top-predictions':topPredictionsPage,'history':historyPage,'favorites':favoritesPage,'notifications':notificationsPage,'profile':profilePage,'admin':adminOverview,'admin/users':adminUsers,'admin/audit':adminAudit,'admin/settings':adminSettings,'admin/catalog':adminCatalog};
  if(path.startsWith('match/'))await matchPage(main,Number(path.split('/')[1]));
  else if(pages[path])await pages[path](main);
  else main.innerHTML=empty('Page not found','Choose a page from the navigation.');
  main.focus({preventScroll:true});
  if(!state.user.must_change){const notifications=await api('/notifications');const unread=notifications.filter(n=>!n.read).length;document.querySelector('#notification-count').textContent=unread||'';}
 }catch(e){
  if(e.status===401){state.user=null;go('login');}
  else{const root=document.querySelector('#main')||document.querySelector('#app');root.innerHTML=empty('Unable to load this view',e.message);toast(e.message,true);}
 }finally{rendering=false;if(queued){queued=false;route();}}
}
window.addEventListener('hashchange',route);
window.addEventListener('keydown',e=>{if(e.key==='Escape'){document.querySelector('#sidebar')?.classList.remove('open');document.querySelector('#menu')?.setAttribute('aria-expanded','false');}});
setInterval(async()=>{if(!state.user||state.user.must_change||rendering)return;try{const rows=await api('/notifications');const el=document.querySelector('#notification-count');if(el)el.textContent=rows.filter(n=>!n.read).length||'';if(location.hash==='#notifications')route();}catch(e){if(e.status===401)go('login');}},60000);
route();

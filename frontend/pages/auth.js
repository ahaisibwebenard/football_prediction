import {send} from '../services/api.js';
import {state,go} from '../hooks/state.js';
import {esc,field,formAction,toast} from '../components/ui.js';
export function authPage(path){
 const mode=path.split('?')[0],signup=mode==='signup',forgot=mode==='forgot',reset=mode==='reset';
 const title=signup?'Your next insight starts here.':forgot?'Get back in the game.':reset?'Choose a new password.':'See the game differently.';
 document.querySelector('#app').innerHTML=`<div class="auth-layout"><section class="auth-story"><a class="brand" href="#login"><span class="brand-mark">P↗</span>${esc(state.siteName)}</a><div><p class="eyebrow">FOOTBALL. UNDERSTOOD.</p><h1>Less guesswork.<br>More <em>insight.</em></h1><p>Discover the numbers behind every match. Transparent models, meaningful probabilities, and your own football instincts.</p><div class="pitch-art" aria-hidden="true"><div class="pitch-circle"></div><div class="pitch-line"></div><span class="pitch-chip">1.84 <small>EXPECTED GOALS</small></span><span class="pitch-chip second">61% <small>HOME ADVANTAGE</small></span></div><small>Illustrative figures · Statistical estimates, not betting advice</small></div><p class="muted">EXPLAINABLE MODELS. BETTER QUESTIONS.</p></section><section class="auth-panel"><button id="auth-theme" class="icon-button" aria-label="Toggle theme">◐</button><div class="auth-form-wrap"><p class="eyebrow">WELCOME TO PREDICTPRO</p><h2>${title}</h2><p class="muted">${signup?'Create a free account to follow matches and challenge the model.':forgot?'We’ll send a one-time password reset link.':reset?'Use at least 10 characters.':'Sign in to your football intelligence workspace.'}</p><form id="auth-form">
 ${signup?field('Full name','name','text','','required minlength="2" maxlength="80" autocomplete="name"')+field('Email','email','email','','required autocomplete="email"')+field('Username','username','text','','required pattern="[a-zA-Z0-9_]{3,30}" autocomplete="username"'):forgot?field('Email','email','email','','required autocomplete="email"'):reset?'':field('Email or username','login','text','','required autocomplete="username"')}
 ${forgot?'':field(reset?'New password':'Password','password','password','','required '+(signup||reset?'minlength="10" autocomplete="new-password"':'autocomplete="current-password"'))}
 <p class="form-error" role="alert"></p><button class="button full" type="submit">${signup?'Create account':forgot?'Send reset link':reset?'Reset password':'Sign in'} <span>↗</span></button></form>
 <div class="auth-links">${mode==='login'?'<a href="#forgot">Forgot password?</a><p>New here? <a href="#signup">Create an account</a></p>':'<a href="#login">Back to sign in</a>'}</div><div class="auth-note">Built for understanding football. No model can guarantee an outcome.</div></div></section></div>`;
 document.querySelector('#auth-theme').onclick=()=>window.toggleTheme();
 formAction(document.querySelector('#auth-form'),async data=>{
   if(reset){data.token=new URLSearchParams(path.split('?')[1]).get('token')||'';const result=await send('/auth/reset',data);toast(result.message);go('login');return;}
   const result=await send('/auth/'+(signup?'signup':forgot?'forgot':'login'),data);
   if(forgot){toast(result.message);return;}
   state.user=result.user;state.impersonating=false;go(result.user.must_change?'profile':'dashboard');
 });
}

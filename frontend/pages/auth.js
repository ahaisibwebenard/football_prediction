import {send} from '../services/api.js';
import {state,go} from '../hooks/state.js';
import {esc,field,formAction,toast} from '../components/ui.js';
export function authPage(path){
 const mode=path.split('?')[0],signup=mode==='signup',forgot=mode==='forgot',reset=mode==='reset';
 const title=signup?'Create your account':forgot?'Reset your password':reset?'Choose a new password':'Sign in to PredictPro';
 const story=`<section class="auth-story"><a class="brand" href="#login"><span class="brand-mark">P↗</span>${esc(state.siteName)}</a><div class="auth-story-copy"><p class="eyebrow">LIVE FOOTBALL INTELLIGENCE</p><h1>Read the match.<br><em>Understand the game.</em></h1><p>Follow real fixtures, explore system-generated result and goal probabilities, and save your favorite teams.</p><div class="auth-benefits"><div><span>01</span><b>Upcoming fixtures</b></div><div><span>02</span><b>Explainable forecasts</b></div><div><span>03</span><b>Daily top-ten forecast list</b></div></div><small>Statistical estimates, not guarantees or betting advice.</small></div><p class="auth-story-footer">FOOTBALL, WITH MORE CONTEXT.</p></section>`;
 const accountFields=field('Full name','name','text','','required minlength="2" maxlength="80" autocomplete="name"')+field('Email address','email','email','','required autocomplete="email"')+field('Username','username','text','','required pattern="[a-zA-Z0-9_]{3,30}" autocomplete="username"')+'<small class="auth-help">3–30 letters, numbers, or underscores. Your username identifies your account.</small>'+field('Password','password','password','','required minlength="10" maxlength="72" autocomplete="new-password"')+field('Confirm password','confirm_password','password','','required minlength="10" maxlength="72" autocomplete="new-password"')+'<small class="auth-help">Use at least 10 characters. Passwords are limited to 72 UTF-8 bytes.</small>';
 document.querySelector('#app').innerHTML=`<div class="auth-layout">${story}<section class="auth-panel"><button id="auth-theme" class="icon-button" aria-label="Toggle theme">◐</button><div class="auth-form-wrap"><p class="eyebrow">${signup?'ACCOUNT REGISTRATION':forgot?'ACCOUNT RECOVERY':reset?'SECURE PASSWORD RESET':'WELCOME BACK'}</p><h2>${title}</h2><p class="muted">${signup?'Create an account to follow real fixtures and view system forecasts.':forgot?'We’ll send a one-time password reset link.':reset?'Choose a new password to secure your account.':'Continue to your football intelligence workspace.'}</p><form id="auth-form">
 ${signup?accountFields:forgot?field('Email address','email','email','','required autocomplete="email"'):reset?'':field('Email or username','login','text','','required autocomplete="username"')}
 ${signup||forgot?'':field(reset?'New password':'Password','password','password','','required '+(reset?'minlength="10" maxlength="72" autocomplete="new-password"':'autocomplete="current-password"'))}
 <p class="form-error" role="alert"></p><button class="button full" type="submit">${signup?'Create account':forgot?'Send reset link':reset?'Reset password':'Sign in'} <span>↗</span></button></form>
 <div class="auth-links">${signup?'<p>Already have an account? <a href="#login">Sign in</a></p>':mode==='login'?'<a href="#forgot">Forgot password?</a><p>New to PredictPro? <a href="#signup">Create an account</a></p>':'<a href="#login">Back to sign in</a>'}</div><div class="auth-note">Your account details are protected. Never share your password.</div></div></section></div>`;
 document.querySelector('#auth-theme').onclick=()=>window.toggleTheme();
 formAction(document.querySelector('#auth-form'),async data=>{
   if(reset){data.token=new URLSearchParams(path.split('?')[1]).get('token')||'';const result=await send('/auth/reset',data);toast(result.message);go('login');return;}
   if(signup){if(data.password!==data.confirm_password)throw new Error('Passwords do not match.');delete data.confirm_password;}
   const result=await send('/auth/'+(signup?'signup':forgot?'forgot':'login'),data);
   if(forgot){toast(result.message);return;}
   state.user=result.user;state.impersonating=false;go(result.user.must_change?'profile':'dashboard');
 });
}

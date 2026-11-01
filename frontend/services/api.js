let csrf='';
export function token(value){csrf=value||'';}
export async function api(path, options={}) {
  const headers={'Content-Type':'application/json',...options.headers};
  if(csrf) headers['X-CSRF-Token']=csrf;
  const response=await fetch('/api'+path,{credentials:'same-origin',...options,headers});
  const data=await response.json().catch(()=>({detail:'Server returned an unreadable response.'}));
  if(!response.ok){
    const error=new Error(Array.isArray(data.detail)?data.detail.map(x=>`${x.loc?.slice(1).join('.')}: ${x.msg}`).join('; '):data.detail||'Request failed.');
    error.status=response.status;throw error;
  }
  if(data.csrf) token(data.csrf);
  return data;
}
export const send=(path,body={},method='POST')=>api(path,{method,body:JSON.stringify(body)});

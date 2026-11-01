export const state={siteName:"PredictPro",liveDataConfigured:false,user:null,impersonating:false,catalog:{teams:[],leagues:[]},charts:[],page:0};
export function destroyCharts(){for(const chart of state.charts)chart.destroy();state.charts=[];}
export function go(path){if(location.hash==='#'+path)window.dispatchEvent(new HashChangeEvent('hashchange'));else location.hash=path;}

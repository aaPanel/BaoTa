import{u as e,v as a,bD as t,q as o,n as s,Q as r,b as i}from"./utils-lib.js?v=1758787359";import"./base-lib.js?v=1758787359";const n=i(),{forceLtd:l,payment:u,getGlobalInfo:c}=e(),d=async({isCheck:e,userInfo:s,userToken:r})=>{const i={...s};if(e.value){if(!s.code)return n.error("请输入验证码");i.token=r.value,delete i.password}else delete i.code;const l=n.load("绑定堡塔账号，请稍候 ...");try{i.username=await a(i.username),i.password=await a(i.password);const s=await t({...i});if(n.request(s),s.status)return w();if(o(s.data))return!1;if(!s.status&&"[]"===JSON.stringify(s.data))return n.request(s);-1===s.data.code&&(r.value=s.data.token,e.value=!0)}catch(u){}finally{l.close()}},w=async(e="/")=>{if(l.value)return await c(),u.value.noExceedLimit?f():u.value.authExpirationTime>-1&&u.value.userGive?window.location.reload():(n.warn("当前账号领取企业版次数已达到上线，请购买企业版，正在跳转请稍候..."),setTimeout(()=>window.location.reload(),2e3));window.location.href=e},f=()=>{s({title:!1,area:["49","38"],component:()=>r(()=>import("./ltd-recom-view.js?v=1758787359"),__vite__mapDeps([]),import.meta.url),close:()=>{window.location.href="/"}})};export{d as b,w as f};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

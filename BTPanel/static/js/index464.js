import{dp as c,_,cZ as d}from"./utils-lib.js?v=1776335489";import{c as i,r as u,w as p,a8 as l,j as m,k as f,e as v,p as b}from"./base-lib.js?v=1776335489";import{u as T,N as h}from"./useStore12.js?v=1776335489";import"./__commonjsHelpers__.js?v=1776335489";const x={class:"set-node-tabs"},E=i({__name:"index",setup(N){const{settingTabActive:e,isJump:s,setNodeInfo:o}=T(),{resetTab:r}=h(),t=u(e.value||"ssh"),{BtTabs:n}=c({type:"left-bg-card",value:t,options:[{label:"SSH",name:"ssh",lazy:!0,render:()=>_(()=>import("./index465.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)}]});return p(()=>s.value,a=>{a&&(t.value=e.value,r())}),l(()=>{o.value={}}),(a,S)=>(m(),f("div",x,[v(b(n))]))}}),O=d(E,[["__scopeId","data-v-f48b8aed"]]);export{O as default};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

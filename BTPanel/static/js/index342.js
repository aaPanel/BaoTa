import{aj as s,Q as a,_ as e}from"./utils-lib.js?v=1758787359";import{c as t,r as o,w as r,a6 as l,v as i,x as m,e as u,y as _}from"./base-lib.js?v=1758787359";import{u as n,N as p}from"./useStore9.js?v=1758787359";import"./__commonjsHelpers__.js?v=1758787359";const d={class:"set-node-tabs"},b=e(t({__name:"index",setup(e){const{settingTabActive:t,isJump:b,setNodeInfo:v}=n(),{resetTab:c}=p(),f=o(t.value||"ssh"),{BtTabs:j}=s({type:"left-bg-card",value:f,options:[{label:"SSH",name:"ssh",lazy:!0,render:()=>a(()=>import("./index343.js?v=1758787359"),__vite__mapDeps([]),import.meta.url)}]});return r(()=>b.value,s=>{s&&(f.value=t.value,c())}),l(()=>{v.value={}}),(s,a)=>(i(),m("div",d,[u(_(j))]))}}),[["__scopeId","data-v-f48b8aed"]]);export{b as default};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

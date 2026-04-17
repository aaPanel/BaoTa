import{cR as _,_ as n,cZ as d}from"./utils-lib.js?v=1776335489";import{c as i,r as f,j as b,k,e as t,p as v,Q as B,d as c}from"./base-lib.js?v=1776335489";import"./__commonjsHelpers__.js?v=1776335489";const D={class:"p-[20px] h-full"},x=i({__name:"index",props:{compData:{default:()=>[]}},setup(r){const s=c(()=>n(()=>import("./index448.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)),p=c(()=>n(()=>import("./index355.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)),a=r,e=f("routeBackup"),l=[{label:"常规备份",name:"routeBackup",lazy:!0,render:()=>t(p,{compData:a.compData},null)},{label:"增量备份",name:"incrementBackup",lazy:!0,render:()=>t(s,{compData:a.compData},null)}];return(V,o)=>{const m=_;return b(),k("div",D,[t(m,{type:"card",modelValue:v(e),"onUpdate:modelValue":o[0]||(o[0]=u=>B(e)?e.value=u:null),options:l,class:"bt-tabs bt-tabs-card"},null,8,["modelValue"])])}}}),A=d(x,[["__scopeId","data-v-ce9629be"]]);export{A as default};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

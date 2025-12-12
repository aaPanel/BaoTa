import{aC as a,H as e,_ as t}from"./utils-lib.js?v=1764728423";import{c as s,r as l,x as o,y as r,e as p,z as m,R as n,d as u}from"./base-lib.js?v=1764728423";import"./__commonjsHelpers__.js?v=1764728423";const c={class:"p-[20px] h-full"},_=t(s({__name:"index",props:{compData:{default:()=>[]}},setup(t){const s=u(()=>e(()=>import("./index457.js?v=1764728423"),__vite__mapDeps([]),import.meta.url)),_=u(()=>e(()=>import("./index458.js?v=1764728423"),__vite__mapDeps([]),import.meta.url)),d=t,i=l("routeBackup"),b=[{label:"常规备份",name:"routeBackup",lazy:!0,render:()=>p(_,{compData:d.compData},null)},{label:"增量备份",name:"incrementBackup",lazy:!0,render:()=>p(s,{compData:d.compData},null)}];return(e,t)=>{const s=a;return o(),r("div",c,[p(s,{type:"card",modelValue:m(i),"onUpdate:modelValue":t[0]||(t[0]=a=>n(i)?i.value=a:null),options:b,class:"bt-tabs bt-tabs-card"},null,8,["modelValue"])])}}}),[["__scopeId","data-v-ce9629be"]]);export{_ as default};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

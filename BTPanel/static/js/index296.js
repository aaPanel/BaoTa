import{dp as n,_ as e}from"./utils-lib.js?v=1776335489";import{c as o,r as _,j as s,C as i,p as l,e as m,d as c}from"./base-lib.js?v=1776335489";import"./__commonjsHelpers__.js?v=1776335489";const y=o({__name:"index",setup(p){const a=_("safeScan"),r=c(()=>e(()=>import("./index356.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)),{BtTabs:t}=n({type:"card",value:a,options:[{label:"安全扫描",name:"safeScan",lazy:!0,render:()=>m(r,null,null)},{label:"违规词检测",name:"wordDetection",lazy:!0,render:()=>e(()=>import("./index357.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)},{label:"动态查杀",name:"dynamicKilling",lazy:!0,render:()=>e(()=>import("./index358.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)}]});return(u,d)=>(s(),i(l(t)))}});export{y as default};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

import{dp as a,_ as e}from"./utils-lib.js?v=1776335489";import{c as n,r as s,j as _,C as l,p,e as m,d}from"./base-lib.js?v=1776335489";import"./__commonjsHelpers__.js?v=1776335489";const v=n({__name:"index",setup(i){const o=s("deployRecords"),r=d(()=>e(()=>import("./index359.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)),{BtTabs:t}=a({type:"card",value:o,options:[{label:"部署记录",name:"deployRecords",lazy:!0,render:()=>m(r,null,null)},{label:"仓库",name:"repository",lazy:!0,render:()=>e(()=>import("./index360.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)},{label:"Webhook日志",name:"webhookLogs",lazy:!0,render:()=>e(()=>import("./index361.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)}]});return(c,u)=>(_(),l(p(t)))}});export{v as default};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

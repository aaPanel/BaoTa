import{aj as a,H as e}from"./utils-lib.js?v=1764728423";import{c as r,r as s,e as l,x as t,O as n,z as i,d as m}from"./base-lib.js?v=1764728423";import"./__commonjsHelpers__.js?v=1764728423";const _=r({__name:"index",setup(r){const _=s("safeScan"),o=m(()=>e(()=>import("./index520.js?v=1764728423"),__vite__mapDeps([]),import.meta.url)),{BtTabs:p}=a({type:"card",value:_,options:[{label:"安全扫描",name:"safeScan",lazy:!0,render:()=>l(o,null,null)},{label:"违规词检测",name:"wordDetection",lazy:!0,render:()=>e(()=>import("./index521.js?v=1764728423"),__vite__mapDeps([]),import.meta.url)},{label:"动态查杀",name:"dynamicKilling",lazy:!0,render:()=>e(()=>import("./index522.js?v=1764728423"),__vite__mapDeps([]),import.meta.url)}]});return(a,e)=>(t(),n(i(p)))}});export{_ as default};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

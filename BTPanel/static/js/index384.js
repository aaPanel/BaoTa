import{dp as o,_ as e}from"./utils-lib.js?v=1776335489";import{c as _,r as m,j as i,k as l,e as n,p as u}from"./base-lib.js?v=1776335489";import"./__commonjsHelpers__.js?v=1776335489";const y=_({__name:"index",setup(p){const r=m("directory"),t=[{name:"directory",label:"站点目录",lazy:!0,render:()=>e(()=>import("./cataluge-setting.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)},{name:"file",label:"配置文件",lazy:!0,render:()=>e(()=>import("./file.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)},{name:"rewrite",label:"伪静态",lazy:!0,render:()=>e(()=>import("./rewrite.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)},{name:"redirect",label:"重定向",lazy:!0,render:()=>e(()=>import("./redirect.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)},{name:"proxy",label:"反向代理",lazy:!0,render:()=>e(()=>import("./index293.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)},{name:"traffic",label:"流量控制",lazy:!0,render:()=>e(()=>import("./traffic.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)}],{BtTabs:a}=o({type:"card",options:t,value:r});return(d,s)=>(i(),l("div",null,[n(u(a))]))}});export{y as default};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

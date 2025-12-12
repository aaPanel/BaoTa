import{aj as e,H as r}from"./utils-lib.js?v=1764728423";import{c as a,r as t,x as _,y as l,e as i,z as m}from"./base-lib.js?v=1764728423";import"./__commonjsHelpers__.js?v=1764728423";const s=a({__name:"index",setup(a){const s=t("directory"),o=[{name:"directory",label:"站点目录",lazy:!0,render:()=>r(()=>import("./cataluge-setting.js?v=1764728423"),__vite__mapDeps([]),import.meta.url)},{name:"file",label:"配置文件",lazy:!0,render:()=>r(()=>import("./file.js?v=1764728423"),__vite__mapDeps([]),import.meta.url)},{name:"rewrite",label:"伪静态",lazy:!0,render:()=>r(()=>import("./rewrite.js?v=1764728423"),__vite__mapDeps([]),import.meta.url)},{name:"redirect",label:"重定向",lazy:!0,render:()=>r(()=>import("./redirect.js?v=1764728423"),__vite__mapDeps([]),import.meta.url)},{name:"proxy",label:"反向代理",lazy:!0,render:()=>r(()=>import("./index469.js?v=1764728423"),__vite__mapDeps([]),import.meta.url)},{name:"traffic",label:"流量控制",lazy:!0,render:()=>r(()=>import("./traffic.js?v=1764728423"),__vite__mapDeps([]),import.meta.url)}],{BtTabs:n}=e({type:"card",options:o,value:s});return(e,r)=>(_(),l("div",null,[i(m(n))]))}});export{s as default};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

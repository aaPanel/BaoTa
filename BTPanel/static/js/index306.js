import{_ as t,cR as m}from"./utils-lib.js?v=1776335489";import{c as _,r,o as i,j as c,C as d,p as l,Q as f}from"./base-lib.js?v=1776335489";import"./__commonjsHelpers__.js?v=1776335489";const E=_({__name:"index",props:{compData:{default:()=>{}}},setup(n){const o=n,e=r(typeof o.compData=="string"?o.compData:"setDefaultPage"),p=r([{label:"页面模板",name:"setDefaultPage",lazy:!0,render:()=>t(()=>import("./default-page2.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)},{label:"默认站点",name:"defaultSite",lazy:!0,render:()=>t(()=>import("./defalut-site2.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)},{label:"HTTPS管理",name:"httpsOfficersSite",lazy:!0,render:()=>t(()=>import("./anti-channel-site2.js?v=1776335489"),__vite__mapDeps([]),import.meta.url)}]);return i(()=>{}),(D,a)=>{const s=m;return c(),d(s,{class:"w-full h-full",type:"left-bg-card",modelValue:l(e),"onUpdate:modelValue":a[0]||(a[0]=u=>f(e)?e.value=u:null),options:l(p)},null,8,["modelValue","options"])}}});export{E as default};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

import{e as o,_ as r}from"./utils-lib.js?v=1776335489";import"./base-lib.js?v=1776335489";const s=(t,e)=>o({isAsync:!0,title:"批量设置".concat(e==="certificate"?"证书分组":"域名分类"),area:42,component:()=>r(()=>import("./index126.js?v=1776335489"),__vite__mapDeps([]),import.meta.url),compData:{type:e,itemList:t},showFooter:!0}),l=async t=>{await o({title:"批量操作结果",area:46,component:()=>r(()=>import("./index127.js?v=1776335489"),__vite__mapDeps([]),import.meta.url),compData:{resultTitle:t.resultTitle,resultData:t.resultData,resultColumn:t.resultColumn}})},m=t=>o({isAsync:!0,title:"".concat(t.title?"证书":"域名","到期提醒配置"),area:50,compData:t,component:()=>r(()=>import("./index128.js?v=1776335489"),__vite__mapDeps([]),import.meta.url),showFooter:!0,confirmText:"保存配置",onCancel:t.cancel}),u=(t,e)=>o({isAsync:!0,title:"".concat(e&&e.length?"批量":"","配置DNS接口"),area:45,component:()=>r(()=>import("./index129.js?v=1776335489"),__vite__mapDeps([]),import.meta.url),compData:{row:t,rowList:e},showFooter:!0});export{m as a,u as d,l as r,s};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

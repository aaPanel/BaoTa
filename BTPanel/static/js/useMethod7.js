import{n as t,H as o}from"./utils-lib.js?v=1764728423";import"./base-lib.js?v=1764728423";const e=(e,a)=>t({isAsync:!0,title:"批量设置".concat("certificate"===a?"证书分组":"域名分类"),area:42,component:()=>o(()=>import("./index289.js?v=1764728423"),__vite__mapDeps([]),import.meta.url),compData:{type:a,itemList:e},showFooter:!0}),a=async e=>{await t({title:"批量操作结果",area:46,component:()=>o(()=>import("./index125.js?v=1764728423"),__vite__mapDeps([]),import.meta.url),compData:{resultTitle:e.resultTitle,resultData:e.resultData,resultColumn:e.resultColumn}})},i=e=>t({isAsync:!0,title:"".concat(e.title?"证书":"域名","到期提醒配置"),area:50,compData:e,component:()=>o(()=>import("./index290.js?v=1764728423"),__vite__mapDeps([]),import.meta.url),showFooter:!0,confirmText:"保存配置",onCancel:e.cancel}),r=(e,a)=>t({isAsync:!0,title:"".concat(a&&a.length?"批量":"","配置DNS接口"),area:45,component:()=>o(()=>import("./index291.js?v=1764728423"),__vite__mapDeps([]),import.meta.url),compData:{row:e,rowList:a},showFooter:!0});export{i as a,r as d,a as r,e as s};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

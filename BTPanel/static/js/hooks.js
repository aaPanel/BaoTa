import{_ as i}from"./utils-lib.js?v=1776335489";const u=async t=>{const{enable:o,type:e}=s();if(!o)return!1;if(e.includes("tencent")){const{default:n}=await i(()=>import("./index114.js?v=1776335489"),__vite__mapDeps([]),import.meta.url);return new n({name:"腾讯云专项版",dependencies:t})}if(e.includes("aliyun")){const{default:n}=await i(()=>import("./index115.js?v=1776335489"),__vite__mapDeps([]),import.meta.url);return new n({name:"阿里云专项版",dependencies:t})}return!1},s=()=>{const t=window.vite_public_panel_type,e=["tencent","aliyun"].find(a=>t.includes(a))||"";return{enable:!!e,type:e}};export{s as c,u};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

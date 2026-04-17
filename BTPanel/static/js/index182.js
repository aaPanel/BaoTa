var m=Object.defineProperty;var p=(i,e,t)=>e in i?m(i,e,{enumerable:!0,configurable:!0,writable:!0,value:t}):i[e]=t;var s=(i,e,t)=>(p(i,typeof e!="symbol"?e+"":e,t),t);import{_ as n}from"./utils-lib.js?v=1776335489";import{a6 as o}from"./base-lib.js?v=1776335489";class l{constructor(e){s(this,"name","");s(this,"isCompatible",!1);s(this,"version","");s(this,"updateTime","");s(this,"dependencies",{});s(this,"compatibleTips",()=>"当前面板版本过低不兼容扩展 ".concat(this.name));this.name=(e==null?void 0:e.name)||"",this.updateTime=(e==null?void 0:e.updateTime)||"",this.dependencies=e==null?void 0:e.dependencies,this.version=this.dependencies.vue.version,this.checkCompatibility(),this.isCompatible||this.compatible()}checkCompatibility(){this.dependencies.hooks,this.isCompatible=this.version.startsWith("3."),this.isCompatible}checkElement(e){return document.querySelector(e)}async compatible(){const{vue:e}=this.dependencies,{default:t}=await n(()=>import("./compatible.js?v=1776335489"),__vite__mapDeps([]),import.meta.url),a=e.defineComponent(t);o(a,{dependencies:this.dependencies,message:this.compatibleTips()}).mount("#extension")}}export{l as E};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

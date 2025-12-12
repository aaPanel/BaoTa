var e=Object.defineProperty,i=(i,t,s)=>(((i,t,s)=>{t in i?e(i,t,{enumerable:!0,configurable:!0,writable:!0,value:s}):i[t]=s})(i,"symbol"!=typeof t?t+"":t,s),s);import{H as t}from"./utils-lib.js?v=1764728423";import{a6 as s}from"./base-lib.js?v=1764728423";class n{constructor(e){i(this,"name",""),i(this,"isCompatible",!1),i(this,"version",""),i(this,"updateTime",""),i(this,"dependencies",{}),i(this,"compatibleTips",()=>"当前面板版本过低不兼容扩展 ".concat(this.name)),this.name=(null==e?void 0:e.name)||"",this.updateTime=(null==e?void 0:e.updateTime)||"",this.dependencies=null==e?void 0:e.dependencies,this.version=this.dependencies.vue.version,this.checkCompatibility(),this.isCompatible||this.compatible()}checkCompatibility(){this.dependencies.hooks,this.isCompatible=this.version.startsWith("3."),this.isCompatible}checkElement(e){return document.querySelector(e)}async compatible(){const{vue:e}=this.dependencies,{default:i}=await t(()=>import("./compatible.js?v=1764728423"),__vite__mapDeps([]),import.meta.url),n=e.defineComponent(i);s(n,{dependencies:this.dependencies,message:this.compatibleTips()}).mount("#extension")}}export{n as E};
function __vite__mapDeps(indexes) {
  if (!__vite__mapDeps.viteFileDeps) {
    __vite__mapDeps.viteFileDeps = []
  }
  return indexes.map((i) => __vite__mapDeps.viteFileDeps[i])
}

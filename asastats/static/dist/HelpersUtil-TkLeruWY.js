import{J as P,M as se,m as Oe,n as Me}from"./ApiController-CBwL3svp.js";var I=globalThis,G=I.ShadowRoot&&(I.ShadyCSS===void 0||I.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,Q=Symbol(),ae=new WeakMap,Ae=class{constructor(e,t,r){if(this._$cssResult$=!0,r!==Q)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(G&&e===void 0){const r=t!==void 0&&t.length===1;r&&(e=ae.get(t)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),r&&ae.set(t,e))}return e}toString(){return this.cssText}},g=e=>new Ae(typeof e=="string"?e:e+"",void 0,Q),y=(e,...t)=>new Ae(e.length===1?e[0]:t.reduce((r,n,o)=>r+(i=>{if(i._$cssResult$===!0)return i.cssText;if(typeof i=="number")return i;throw Error("Value passed to 'css' function must be a 'css' function result: "+i+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(n)+e[o+1],e[0]),e,Q),Fe=(e,t)=>{if(G)e.adoptedStyleSheets=t.map(r=>r instanceof CSSStyleSheet?r:r.styleSheet);else for(const r of t){const n=document.createElement("style"),o=I.litNonce;o!==void 0&&n.setAttribute("nonce",o),n.textContent=r.cssText,e.appendChild(n)}},ce=G?e=>e:e=>e instanceof CSSStyleSheet?(t=>{let r="";for(const n of t.cssRules)r+=n.cssText;return g(r)})(e):e,{is:Re,defineProperty:Ue,getOwnPropertyDescriptor:ze,getOwnPropertyNames:De,getOwnPropertySymbols:Ie,getPrototypeOf:Ke}=Object,V=globalThis,le=V.trustedTypes,We=le?le.emptyScript:"",Be=V.reactiveElementPolyfillSupport,O=(e,t)=>e,X={toAttribute(e,t){switch(t){case Boolean:e=e?We:null;break;case Object:case Array:e=e==null?e:JSON.stringify(e)}return e},fromAttribute(e,t){let r=e;switch(t){case Boolean:r=e!==null;break;case Number:r=e===null?null:Number(e);break;case Object:case Array:try{r=JSON.parse(e)}catch{r=null}}return r}},ye=(e,t)=>!Re(e,t),de={attribute:!0,type:String,converter:X,reflect:!1,useDefault:!1,hasChanged:ye};Symbol.metadata??=Symbol("metadata"),V.litPropertyMetadata??=new WeakMap;var S=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=de){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){const r=Symbol(),n=this.getPropertyDescriptor(e,r,t);n!==void 0&&Ue(this.prototype,e,n)}}static getPropertyDescriptor(e,t,r){const{get:n,set:o}=ze(this.prototype,e)??{get(){return this[t]},set(i){this[t]=i}};return{get:n,set(i){const a=n?.call(this);o?.call(this,i),this.requestUpdate(e,a,r)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??de}static _$Ei(){if(this.hasOwnProperty(O("elementProperties")))return;const e=Ke(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(O("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(O("properties"))){const t=this.properties,r=[...De(t),...Ie(t)];for(const n of r)this.createProperty(n,t[n])}const e=this[Symbol.metadata];if(e!==null){const t=litPropertyMetadata.get(e);if(t!==void 0)for(const[r,n]of t)this.elementProperties.set(r,n)}this._$Eh=new Map;for(const[t,r]of this.elementProperties){const n=this._$Eu(t,r);n!==void 0&&this._$Eh.set(n,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const r=new Set(e.flat(1/0).reverse());for(const n of r)t.unshift(ce(n))}else e!==void 0&&t.push(ce(e));return t}static _$Eu(e,t){const r=t.attribute;return r===!1?void 0:typeof r=="string"?r:typeof e=="string"?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){const e=new Map,t=this.constructor.elementProperties;for(const r of t.keys())this.hasOwnProperty(r)&&(e.set(r,this[r]),delete this[r]);e.size>0&&(this._$Ep=e)}createRenderRoot(){const e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return Fe(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,r){this._$AK(e,r)}_$ET(e,t){const r=this.constructor.elementProperties.get(e),n=this.constructor._$Eu(e,r);if(n!==void 0&&r.reflect===!0){const o=(r.converter?.toAttribute!==void 0?r.converter:X).toAttribute(t,r.type);this._$Em=e,o==null?this.removeAttribute(n):this.setAttribute(n,o),this._$Em=null}}_$AK(e,t){const r=this.constructor,n=r._$Eh.get(e);if(n!==void 0&&this._$Em!==n){const o=r.getPropertyOptions(n),i=typeof o.converter=="function"?{fromAttribute:o.converter}:o.converter?.fromAttribute!==void 0?o.converter:X;this._$Em=n;const a=i.fromAttribute(t,o.type);this[n]=a??this._$Ej?.get(n)??a,this._$Em=null}}requestUpdate(e,t,r,n=!1,o){if(e!==void 0){const i=this.constructor;if(n===!1&&(o=this[e]),r??=i.getPropertyOptions(e),!((r.hasChanged??ye)(o,t)||r.useDefault&&r.reflect&&o===this._$Ej?.get(e)&&!this.hasAttribute(i._$Eu(e,r))))return;this.C(e,t,r)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(e,t,{useDefault:r,reflect:n,wrapped:o},i){r&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,i??t??this[e]),o!==!0||i!==void 0)||(this._$AL.has(e)||(this.hasUpdated||r||(t=void 0),this._$AL.set(e,t)),n===!0&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[n,o]of this._$Ep)this[n]=o;this._$Ep=void 0}const r=this.constructor.elementProperties;if(r.size>0)for(const[n,o]of r){const{wrapped:i}=o,a=this[n];i!==!0||this._$AL.has(n)||a===void 0||this.C(n,void 0,o,a)}}let e=!1;const t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(r=>r.hostUpdate?.()),this.update(t)):this._$EM()}catch(r){throw e=!1,this._$EM(),r}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(e){}firstUpdated(e){}};S.elementStyles=[],S.shadowRootOptions={mode:"open"},S[O("elementProperties")]=new Map,S[O("finalized")]=new Map,Be?.({ReactiveElement:S}),(V.reactiveElementVersions??=[]).push("2.1.2");var ee=globalThis,ue=e=>e,W=ee.trustedTypes,pe=W?W.createPolicy("lit-html",{createHTML:e=>e}):void 0,te="$lit$",A=`lit$${Math.random().toFixed(9).slice(2)}$`,re="?"+A,Le=`<${re}>`,E=document,M=()=>E.createComment(""),F=e=>e===null||typeof e!="object"&&typeof e!="function",ne=Array.isArray,_e=e=>ne(e)||typeof e?.[Symbol.iterator]=="function",q=`[ 	
\f\r]`,H=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,he=/-->/g,ge=/>/g,_=RegExp(`>|${q}(?:([^\\s"'>=/]+)(${q}*=${q}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),me=/'/g,fe=/"/g,Ce=/^(?:script|style|textarea|title)$/i,oe=e=>(t,...r)=>({_$litType$:e,strings:t,values:r}),lt=oe(1),dt=oe(2),ut=oe(3),N=Symbol.for("lit-noChange"),p=Symbol.for("lit-nothing"),be=new WeakMap,k=E.createTreeWalker(E,129);function ke(e,t){if(!ne(e)||!e.hasOwnProperty("raw"))throw Error("invalid template strings array");return pe!==void 0?pe.createHTML(t):t}var ve=(e,t)=>{const r=e.length-1,n=[];let o,i=t===2?"<svg>":t===3?"<math>":"",a=H;for(let s=0;s<r;s++){const c=e[s];let u,d,l=-1,h=0;for(;h<c.length&&(a.lastIndex=h,d=a.exec(c),d!==null);)h=a.lastIndex,a===H?d[1]==="!--"?a=he:d[1]!==void 0?a=ge:d[2]!==void 0?(Ce.test(d[2])&&(o=RegExp("</"+d[2],"g")),a=_):d[3]!==void 0&&(a=_):a===_?d[0]===">"?(a=o??H,l=-1):d[1]===void 0?l=-2:(l=a.lastIndex-d[2].length,u=d[1],a=d[3]===void 0?_:d[3]==='"'?fe:me):a===fe||a===me?a=_:a===he||a===ge?a=H:(a=_,o=void 0);const f=a===_&&e[s+1].startsWith("/>")?" ":"";i+=a===H?c+Le:l>=0?(n.push(u),c.slice(0,l)+te+c.slice(l)+A+f):c+A+(l===-2?s:f)}return[ke(e,i+(e[r]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),n]},Z=class Ee{constructor({strings:t,_$litType$:r},n){let o;this.parts=[];let i=0,a=0;const s=t.length-1,c=this.parts,[u,d]=ve(t,r);if(this.el=Ee.createElement(u,n),k.currentNode=this.el.content,r===2||r===3){const l=this.el.content.firstChild;l.replaceWith(...l.childNodes)}for(;(o=k.nextNode())!==null&&c.length<s;){if(o.nodeType===1){if(o.hasAttributes())for(const l of o.getAttributeNames())if(l.endsWith(te)){const h=d[a++],f=o.getAttribute(l).split(A),U=/([.?@])?(.*)/.exec(h);c.push({type:1,index:i,name:U[2],strings:f,ctor:U[1]==="."?Te:U[1]==="?"?Ne:U[1]==="@"?He:R}),o.removeAttribute(l)}else l.startsWith(A)&&(c.push({type:6,index:i}),o.removeAttribute(l));if(Ce.test(o.tagName)){const l=o.textContent.split(A),h=l.length-1;if(h>0){o.textContent=W?W.emptyScript:"";for(let f=0;f<h;f++)o.append(l[f],M()),k.nextNode(),c.push({type:2,index:++i});o.append(l[h],M())}}}else if(o.nodeType===8)if(o.data===re)c.push({type:2,index:i});else{let l=-1;for(;(l=o.data.indexOf(A,l+1))!==-1;)c.push({type:7,index:i}),l+=A.length-1}i++}}static createElement(t,r){const n=E.createElement("template");return n.innerHTML=t,n}};function w(e,t,r=e,n){if(t===N)return t;let o=n!==void 0?r._$Co?.[n]:r._$Cl;const i=F(t)?void 0:t._$litDirective$;return o?.constructor!==i&&(o?._$AO?.(!1),i===void 0?o=void 0:(o=new i(e),o._$AT(e,r,n)),n!==void 0?(r._$Co??=[])[n]=o:r._$Cl=o),o!==void 0&&(t=w(e,o._$AS(e,t.values),o,n)),t}var we=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){const{el:{content:t},parts:r}=this._$AD,n=(e?.creationScope??E).importNode(t,!0);k.currentNode=n;let o=k.nextNode(),i=0,a=0,s=r[0];for(;s!==void 0;){if(i===s.index){let c;s.type===2?c=new Y(o,o.nextSibling,this,e):s.type===1?c=new s.ctor(o,s.name,s.strings,this,e):s.type===6&&(c=new Pe(o,this,e)),this._$AV.push(c),s=r[++a]}i!==s?.index&&(o=k.nextNode(),i++)}return k.currentNode=E,n}p(e){let t=0;for(const r of this._$AV)r!==void 0&&(r.strings!==void 0?(r._$AI(e,r,t),t+=r.strings.length-2):r._$AI(e[t])),t++}},Y=class Se{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,r,n,o){this.type=2,this._$AH=p,this._$AN=void 0,this._$AA=t,this._$AB=r,this._$AM=n,this.options=o,this._$Cv=o?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const r=this._$AM;return r!==void 0&&t?.nodeType===11&&(t=r.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,r=this){t=w(this,t,r),F(t)?t===p||t==null||t===""?(this._$AH!==p&&this._$AR(),this._$AH=p):t!==this._$AH&&t!==N&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):_e(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==p&&F(this._$AH)?this._$AA.nextSibling.data=t:this.T(E.createTextNode(t)),this._$AH=t}$(t){const{values:r,_$litType$:n}=t,o=typeof n=="number"?this._$AC(t):(n.el===void 0&&(n.el=Z.createElement(ke(n.h,n.h[0]),this.options)),n);if(this._$AH?._$AD===o)this._$AH.p(r);else{const i=new we(o,this),a=i.u(this.options);i.p(r),this.T(a),this._$AH=i}}_$AC(t){let r=be.get(t.strings);return r===void 0&&be.set(t.strings,r=new Z(t)),r}k(t){ne(this._$AH)||(this._$AH=[],this._$AR());const r=this._$AH;let n,o=0;for(const i of t)o===r.length?r.push(n=new Se(this.O(M()),this.O(M()),this,this.options)):n=r[o],n._$AI(i),o++;o<r.length&&(this._$AR(n&&n._$AB.nextSibling,o),r.length=o)}_$AR(t=this._$AA.nextSibling,r){for(this._$AP?.(!1,!0,r);t!==this._$AB;){const n=ue(t).nextSibling;ue(t).remove(),t=n}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},R=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,r,n,o){this.type=1,this._$AH=p,this._$AN=void 0,this.element=e,this.name=t,this._$AM=n,this.options=o,r.length>2||r[0]!==""||r[1]!==""?(this._$AH=Array(r.length-1).fill(new String),this.strings=r):this._$AH=p}_$AI(e,t=this,r,n){const o=this.strings;let i=!1;if(o===void 0)e=w(this,e,t,0),i=!F(e)||e!==this._$AH&&e!==N,i&&(this._$AH=e);else{const a=e;let s,c;for(e=o[0],s=0;s<o.length-1;s++)c=w(this,a[r+s],t,s),c===N&&(c=this._$AH[s]),i||=!F(c)||c!==this._$AH[s],c===p?e=p:e!==p&&(e+=(c??"")+o[s+1]),this._$AH[s]=c}i&&!n&&this.j(e)}j(e){e===p?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}},Te=class extends R{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===p?void 0:e}},Ne=class extends R{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==p)}},He=class extends R{constructor(e,t,r,n,o){super(e,t,r,n,o),this.type=5}_$AI(e,t=this){if((e=w(this,e,t,0)??p)===N)return;const r=this._$AH,n=e===p&&r!==p||e.capture!==r.capture||e.once!==r.once||e.passive!==r.passive,o=e!==p&&(r===p||n);n&&this.element.removeEventListener(this.name,this,r),o&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},Pe=class{constructor(e,t,r){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=r}get _$AU(){return this._$AM._$AU}_$AI(e){w(this,e)}},pt={M:te,P:A,A:re,C:1,L:ve,R:we,D:_e,V:w,I:Y,H:R,N:Ne,U:He,B:Te,F:Pe},je=ee.litHtmlPolyfillSupport;je?.(Z,Y),(ee.litHtmlVersions??=[]).push("3.3.3");var Ve=(e,t,r)=>{const n=r?.renderBefore??t;let o=n._$litPart$;if(o===void 0){const i=r?.renderBefore??null;n._$litPart$=o=new Y(t.insertBefore(M(),i),i,void 0,r??{})}return o._$AI(e),o},ie=globalThis,K=class extends S{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=Ve(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return N}};K._$litElement$=!0,K.finalized=!0,ie.litElementHydrateSupport?.({LitElement:K});var Ye=ie.litElementPolyfillSupport;Ye?.({LitElement:K});(ie.litElementVersions??=[]).push("4.2.2");var ht={interpolate(e,t,r){if(e.length!==2||t.length!==2)throw new Error("inputRange and outputRange must be an array of length 2");const n=e[0]||0,o=e[1]||0,i=t[0]||0,a=t[1]||0;return r<n?i:r>o?a:(a-i)/(o-n)*(r-n)+i}},qe={black:"#202020",white:"#FFFFFF",white010:"rgba(255, 255, 255, 0.1)",accent010:"rgba(9, 136, 240, 0.1)",accent020:"rgba(9, 136, 240, 0.2)",accent030:"rgba(9, 136, 240, 0.3)",accent040:"rgba(9, 136, 240, 0.4)",accent050:"rgba(9, 136, 240, 0.5)",accent060:"rgba(9, 136, 240, 0.6)",accent070:"rgba(9, 136, 240, 0.7)",accent080:"rgba(9, 136, 240, 0.8)",accent090:"rgba(9, 136, 240, 0.9)",accent100:"rgba(9, 136, 240, 1.0)",accentSecondary010:"rgba(199, 185, 148, 0.1)",accentSecondary020:"rgba(199, 185, 148, 0.2)",accentSecondary030:"rgba(199, 185, 148, 0.3)",accentSecondary040:"rgba(199, 185, 148, 0.4)",accentSecondary050:"rgba(199, 185, 148, 0.5)",accentSecondary060:"rgba(199, 185, 148, 0.6)",accentSecondary070:"rgba(199, 185, 148, 0.7)",accentSecondary080:"rgba(199, 185, 148, 0.8)",accentSecondary090:"rgba(199, 185, 148, 0.9)",accentSecondary100:"rgba(199, 185, 148, 1.0)",productWalletKit:"#FFB800",productAppKit:"#FF573B",productCloud:"#0988F0",productDocumentation:"#008847",neutrals050:"#F6F6F6",neutrals100:"#F3F3F3",neutrals200:"#E9E9E9",neutrals300:"#D0D0D0",neutrals400:"#BBB",neutrals500:"#9A9A9A",neutrals600:"#6C6C6C",neutrals700:"#4F4F4F",neutrals800:"#363636",neutrals900:"#2A2A2A",neutrals1000:"#252525",semanticSuccess010:"rgba(48, 164, 107, 0.1)",semanticSuccess020:"rgba(48, 164, 107, 0.2)",semanticSuccess030:"rgba(48, 164, 107, 0.3)",semanticSuccess040:"rgba(48, 164, 107, 0.4)",semanticSuccess050:"rgba(48, 164, 107, 0.5)",semanticSuccess060:"rgba(48, 164, 107, 0.6)",semanticSuccess070:"rgba(48, 164, 107, 0.7)",semanticSuccess080:"rgba(48, 164, 107, 0.8)",semanticSuccess090:"rgba(48, 164, 107, 0.9)",semanticSuccess100:"rgba(48, 164, 107, 1.0)",semanticError010:"rgba(223, 74, 52, 0.1)",semanticError020:"rgba(223, 74, 52, 0.2)",semanticError030:"rgba(223, 74, 52, 0.3)",semanticError040:"rgba(223, 74, 52, 0.4)",semanticError050:"rgba(223, 74, 52, 0.5)",semanticError060:"rgba(223, 74, 52, 0.6)",semanticError070:"rgba(223, 74, 52, 0.7)",semanticError080:"rgba(223, 74, 52, 0.8)",semanticError090:"rgba(223, 74, 52, 0.9)",semanticError100:"rgba(223, 74, 52, 1.0)",semanticWarning010:"rgba(243, 161, 63, 0.1)",semanticWarning020:"rgba(243, 161, 63, 0.2)",semanticWarning030:"rgba(243, 161, 63, 0.3)",semanticWarning040:"rgba(243, 161, 63, 0.4)",semanticWarning050:"rgba(243, 161, 63, 0.5)",semanticWarning060:"rgba(243, 161, 63, 0.6)",semanticWarning070:"rgba(243, 161, 63, 0.7)",semanticWarning080:"rgba(243, 161, 63, 0.8)",semanticWarning090:"rgba(243, 161, 63, 0.9)",semanticWarning100:"rgba(243, 161, 63, 1.0)"},B={core:{backgroundAccentPrimary:"#0988F0",backgroundAccentCertified:"#C7B994",backgroundWalletKit:"#FFB800",backgroundAppKit:"#FF573B",backgroundCloud:"#0988F0",backgroundDocumentation:"#008847",backgroundSuccess:"rgba(48, 164, 107, 0.20)",backgroundError:"rgba(223, 74, 52, 0.20)",backgroundWarning:"rgba(243, 161, 63, 0.20)",textAccentPrimary:"#0988F0",textAccentCertified:"#C7B994",textWalletKit:"#FFB800",textAppKit:"#FF573B",textCloud:"#0988F0",textDocumentation:"#008847",textSuccess:"#30A46B",textError:"#DF4A34",textWarning:"#F3A13F",borderAccentPrimary:"#0988F0",borderSecondary:"#C7B994",borderSuccess:"#30A46B",borderError:"#DF4A34",borderWarning:"#F3A13F",foregroundAccent010:"rgba(9, 136, 240, 0.1)",foregroundAccent020:"rgba(9, 136, 240, 0.2)",foregroundAccent040:"rgba(9, 136, 240, 0.4)",foregroundAccent060:"rgba(9, 136, 240, 0.6)",foregroundSecondary020:"rgba(199, 185, 148, 0.2)",foregroundSecondary040:"rgba(199, 185, 148, 0.4)",foregroundSecondary060:"rgba(199, 185, 148, 0.6)",iconAccentPrimary:"#0988F0",iconAccentCertified:"#C7B994",iconSuccess:"#30A46B",iconError:"#DF4A34",iconWarning:"#F3A13F",glass010:"rgba(255, 255, 255, 0.1)",zIndex:"9999"},dark:{overlay:"rgba(0, 0, 0, 0.50)",backgroundPrimary:"#202020",backgroundInvert:"#FFFFFF",textPrimary:"#FFFFFF",textSecondary:"#9A9A9A",textTertiary:"#BBBBBB",textInvert:"#202020",borderPrimary:"#2A2A2A",borderPrimaryDark:"#363636",borderSecondary:"#4F4F4F",foregroundPrimary:"#252525",foregroundSecondary:"#2A2A2A",foregroundTertiary:"#363636",iconDefault:"#9A9A9A",iconInverse:"#FFFFFF"},light:{overlay:"rgba(230 , 230, 230, 0.5)",backgroundPrimary:"#FFFFFF",borderPrimaryDark:"#E9E9E9",backgroundInvert:"#202020",textPrimary:"#202020",textSecondary:"#9A9A9A",textTertiary:"#6C6C6C",textInvert:"#FFFFFF",borderPrimary:"#E9E9E9",borderSecondary:"#D0D0D0",foregroundPrimary:"#F3F3F3",foregroundSecondary:"#E9E9E9",foregroundTertiary:"#D0D0D0",iconDefault:"#9A9A9A",iconInverse:"#202020"}},Xe={1:"4px",2:"8px",10:"10px",3:"12px",4:"16px",6:"24px",5:"20px",8:"32px",16:"64px",20:"80px",32:"128px",64:"256px",128:"512px",round:"9999px"},Ze={0:"0px","01":"2px",1:"4px",2:"8px",3:"12px",4:"16px",5:"20px",6:"24px",7:"28px",8:"32px",9:"36px",10:"40px",12:"48px",14:"56px",16:"64px",20:"80px",32:"128px",64:"256px"},Je={regular:"KHTeka",mono:"KHTekaMono"},Ge={regular:"400",medium:"500"},Qe={h1:"50px",h2:"44px",h3:"38px",h4:"32px",h5:"26px",h6:"20px",large:"16px",medium:"14px",small:"12px"},et={"h1-regular-mono":{lineHeight:"50px",letterSpacing:"-3px"},"h1-regular":{lineHeight:"50px",letterSpacing:"-1px"},"h1-medium":{lineHeight:"50px",letterSpacing:"-0.84px"},"h2-regular-mono":{lineHeight:"44px",letterSpacing:"-2.64px"},"h2-regular":{lineHeight:"44px",letterSpacing:"-0.88px"},"h2-medium":{lineHeight:"44px",letterSpacing:"-0.88px"},"h3-regular-mono":{lineHeight:"38px",letterSpacing:"-2.28px"},"h3-regular":{lineHeight:"38px",letterSpacing:"-0.76px"},"h3-medium":{lineHeight:"38px",letterSpacing:"-0.76px"},"h4-regular-mono":{lineHeight:"32px",letterSpacing:"-1.92px"},"h4-regular":{lineHeight:"32px",letterSpacing:"-0.32px"},"h4-medium":{lineHeight:"32px",letterSpacing:"-0.32px"},"h5-regular-mono":{lineHeight:"26px",letterSpacing:"-1.56px"},"h5-regular":{lineHeight:"26px",letterSpacing:"-0.26px"},"h5-medium":{lineHeight:"26px",letterSpacing:"-0.26px"},"h6-regular-mono":{lineHeight:"20px",letterSpacing:"-1.2px"},"h6-regular":{lineHeight:"20px",letterSpacing:"-0.6px"},"h6-medium":{lineHeight:"20px",letterSpacing:"-0.6px"},"lg-regular-mono":{lineHeight:"16px",letterSpacing:"-0.96px"},"lg-regular":{lineHeight:"18px",letterSpacing:"-0.16px"},"lg-medium":{lineHeight:"18px",letterSpacing:"-0.16px"},"md-regular-mono":{lineHeight:"14px",letterSpacing:"-0.84px"},"md-regular":{lineHeight:"16px",letterSpacing:"-0.14px"},"md-medium":{lineHeight:"16px",letterSpacing:"-0.14px"},"sm-regular-mono":{lineHeight:"12px",letterSpacing:"-0.72px"},"sm-regular":{lineHeight:"14px",letterSpacing:"-0.12px"},"sm-medium":{lineHeight:"14px",letterSpacing:"-0.12px"}},tt={"ease-out-power-2":"cubic-bezier(0.23, 0.09, 0.08, 1.13)","ease-out-power-1":"cubic-bezier(0.12, 0.04, 0.2, 1.06)","ease-in-power-2":"cubic-bezier(0.92, -0.13, 0.77, 0.91)","ease-in-power-1":"cubic-bezier(0.88, -0.06, 0.8, 0.96)","ease-inout-power-2":"cubic-bezier(0.77, 0.09, 0.23, 1.13)","ease-inout-power-1":"cubic-bezier(0.88, 0.04, 0.12, 1.06)"},rt={xl:"400ms",lg:"200ms",md:"125ms",sm:"75ms"},J={colors:qe,fontFamily:Je,fontWeight:Ge,textSize:Qe,typography:et,tokens:{core:B.core,theme:B.dark},borderRadius:Xe,spacing:Ze,durations:rt,easings:tt},$e="--apkt";function z(e){if(!e)return{};const t={};return t["font-family"]=e["--apkt-font-family"]??e["--w3m-font-family"]??"KHTeka",t.accent=e["--apkt-accent"]??e["--w3m-accent"]??"#0988F0",t["color-mix"]=e["--apkt-color-mix"]??e["--w3m-color-mix"]??"#000",t["color-mix-strength"]=e["--apkt-color-mix-strength"]??e["--w3m-color-mix-strength"]??0,t["font-size-master"]=e["--apkt-font-size-master"]??e["--w3m-font-size-master"]??"10px",t["border-radius-master"]=e["--apkt-border-radius-master"]??e["--w3m-border-radius-master"]??"4px",e["--apkt-z-index"]!==void 0?t["z-index"]=e["--apkt-z-index"]:e["--w3m-z-index"]!==void 0&&(t["z-index"]=e["--w3m-z-index"]),t}var x={createCSSVariables(e){const t={},r={};function n(i,a,s=""){for(const[c,u]of Object.entries(i)){const d=s?`${s}-${c}`:c;u&&typeof u=="object"&&Object.keys(u).length?(a[c]={},n(u,a[c],d)):typeof u=="string"&&(a[c]=`${$e}-${d}`)}}function o(i,a){for(const[s,c]of Object.entries(i))c&&typeof c=="object"?(a[s]={},o(c,a[s])):typeof c=="string"&&(a[s]=`var(${c})`)}return n(e,t),o(t,r),{cssVariables:t,cssVariablesVarPrefix:r}},assignCSSVariables(e,t){const r={};function n(o,i,a){for(const[s,c]of Object.entries(o)){const u=a?`${a}-${s}`:s,d=i[s];c&&typeof c=="object"?n(c,d,u):typeof d=="string"&&(r[`${$e}-${u}`]=d)}}return n(e,t),r},createRootStyles(e,t){const r={...J,tokens:{...J.tokens,theme:e==="light"?B.light:B.dark}},{cssVariables:n}=x.createCSSVariables(r),o=x.assignCSSVariables(n,r),i=x.generateW3MVariables(t),a=x.generateW3MOverrides(t),s=x.generateScaledVariables(t),c=x.generateBaseVariables(o),u={...o,...c,...i,...a,...s},d=x.applyColorMixToVariables(t,u),l={...u,...d};return`:root {${Object.entries(l).map(([h,f])=>`${h}:${f.replace("/[:;{}</>]/g","")};`).join("")}}`},generateW3MVariables(e){if(!e)return{};const t=z(e),r={};return r["--w3m-font-family"]=t["font-family"],r["--w3m-accent"]=t.accent,r["--w3m-color-mix"]=t["color-mix"],r["--w3m-color-mix-strength"]=`${t["color-mix-strength"]}%`,r["--w3m-font-size-master"]=t["font-size-master"],r["--w3m-border-radius-master"]=t["border-radius-master"],r},generateW3MOverrides(e){if(!e)return{};const t=z(e),r={};if(e["--apkt-accent"]||e["--w3m-accent"]){const n=t.accent;r["--apkt-tokens-core-iconAccentPrimary"]=n,r["--apkt-tokens-core-borderAccentPrimary"]=n,r["--apkt-tokens-core-textAccentPrimary"]=n,r["--apkt-tokens-core-backgroundAccentPrimary"]=n}return(e["--apkt-font-family"]||e["--w3m-font-family"])&&(r["--apkt-fontFamily-regular"]=t["font-family"]),t["z-index"]!==void 0&&(r["--apkt-tokens-core-zIndex"]=`${t["z-index"]}`),r},generateScaledVariables(e){if(!e)return{};const t=z(e),r={};if(e["--apkt-font-size-master"]||e["--w3m-font-size-master"]){const n=parseFloat(t["font-size-master"].replace("px",""));r["--apkt-textSize-h1"]=`${Number(n)*5}px`,r["--apkt-textSize-h2"]=`${Number(n)*4.4}px`,r["--apkt-textSize-h3"]=`${Number(n)*3.8}px`,r["--apkt-textSize-h4"]=`${Number(n)*3.2}px`,r["--apkt-textSize-h5"]=`${Number(n)*2.6}px`,r["--apkt-textSize-h6"]=`${Number(n)*2}px`,r["--apkt-textSize-large"]=`${Number(n)*1.6}px`,r["--apkt-textSize-medium"]=`${Number(n)*1.4}px`,r["--apkt-textSize-small"]=`${Number(n)*1.2}px`}if(e["--apkt-border-radius-master"]||e["--w3m-border-radius-master"]){const n=parseFloat(t["border-radius-master"].replace("px",""));r["--apkt-borderRadius-1"]=`${Number(n)}px`,r["--apkt-borderRadius-2"]=`${Number(n)*2}px`,r["--apkt-borderRadius-3"]=`${Number(n)*3}px`,r["--apkt-borderRadius-4"]=`${Number(n)*4}px`,r["--apkt-borderRadius-5"]=`${Number(n)*5}px`,r["--apkt-borderRadius-6"]=`${Number(n)*6}px`,r["--apkt-borderRadius-8"]=`${Number(n)*8}px`,r["--apkt-borderRadius-16"]=`${Number(n)*16}px`,r["--apkt-borderRadius-20"]=`${Number(n)*20}px`,r["--apkt-borderRadius-32"]=`${Number(n)*32}px`,r["--apkt-borderRadius-64"]=`${Number(n)*64}px`,r["--apkt-borderRadius-128"]=`${Number(n)*128}px`}return r},generateColorMixCSS(e,t){if(!e?.["--w3m-color-mix"]||!e["--w3m-color-mix-strength"])return"";const r=e["--w3m-color-mix"],n=e["--w3m-color-mix-strength"];if(!n||n===0)return"";const o=Object.keys(t||{}).filter(i=>{const a=i.includes("-tokens-core-background")||i.includes("-tokens-core-text")||i.includes("-tokens-core-border")||i.includes("-tokens-core-foreground")||i.includes("-tokens-core-icon")||i.includes("-tokens-theme-background")||i.includes("-tokens-theme-text")||i.includes("-tokens-theme-border")||i.includes("-tokens-theme-foreground")||i.includes("-tokens-theme-icon"),s=i.includes("-borderRadius-")||i.includes("-spacing-")||i.includes("-textSize-")||i.includes("-fontFamily-")||i.includes("-fontWeight-")||i.includes("-typography-")||i.includes("-duration-")||i.includes("-ease-")||i.includes("-path-")||i.includes("-width-")||i.includes("-height-")||i.includes("-visual-size-")||i.includes("-modal-width")||i.includes("-cover");return a&&!s});return o.length===0?"":` @supports (background: color-mix(in srgb, white 50%, black)) {
      :root {
        ${o.map(i=>{const a=t?.[i]||"";return a.includes("color-mix")||a.startsWith("#")||a.startsWith("rgb")?`${i}: color-mix(in srgb, ${r} ${n}%, ${a});`:`${i}: color-mix(in srgb, ${r} ${n}%, var(${i}-base, ${a}));`}).join("")}
      }
    }`},generateBaseVariables(e){const t={},r=e["--apkt-tokens-theme-backgroundPrimary"];r&&(t["--apkt-tokens-theme-backgroundPrimary-base"]=r);const n=e["--apkt-tokens-core-backgroundAccentPrimary"];return n&&(t["--apkt-tokens-core-backgroundAccentPrimary-base"]=n),t},applyColorMixToVariables(e,t){const r={};t?.["--apkt-tokens-theme-backgroundPrimary"]&&(r["--apkt-tokens-theme-backgroundPrimary"]="var(--apkt-tokens-theme-backgroundPrimary-base)"),t?.["--apkt-tokens-core-backgroundAccentPrimary"]&&(r["--apkt-tokens-core-backgroundAccentPrimary"]="var(--apkt-tokens-core-backgroundAccentPrimary-base)");const n=z(e),o=n["color-mix"],i=n["color-mix-strength"];if(!i||i===0)return r;const a=Object.keys(t||{}).filter(s=>{const c=s.includes("-tokens-core-background")||s.includes("-tokens-core-text")||s.includes("-tokens-core-border")||s.includes("-tokens-core-foreground")||s.includes("-tokens-core-icon")||s.includes("-tokens-theme-background")||s.includes("-tokens-theme-text")||s.includes("-tokens-theme-border")||s.includes("-tokens-theme-foreground")||s.includes("-tokens-theme-icon")||s.includes("-tokens-theme-overlay"),u=s.includes("-borderRadius-")||s.includes("-spacing-")||s.includes("-textSize-")||s.includes("-fontFamily-")||s.includes("-fontWeight-")||s.includes("-typography-")||s.includes("-duration-")||s.includes("-ease-")||s.includes("-path-")||s.includes("-width-")||s.includes("-height-")||s.includes("-visual-size-")||s.includes("-modal-width")||s.includes("-cover");return c&&!u});return a.length===0||a.forEach(s=>{const c=t?.[s]||"";s.endsWith("-base")||(s==="--apkt-tokens-theme-backgroundPrimary"||s==="--apkt-tokens-core-backgroundAccentPrimary"?r[s]=`color-mix(in srgb, ${o} ${i}%, var(${s}-base))`:c.includes("color-mix")||c.startsWith("#")||c.startsWith("rgb")?r[s]=`color-mix(in srgb, ${o} ${i}%, ${c})`:r[s]=`color-mix(in srgb, ${o} ${i}%, var(${s}-base, ${c}))`)}),r}},{cssVariablesVarPrefix:nt}=x.createCSSVariables(J);function gt(e,...t){return y(e,...t.map(r=>g(typeof r=="function"?r(nt):r)))}var C=void 0,v=void 0,b=void 0,m=void 0,L=void 0,$={"KHTeka-500-woff2":"https://fonts.reown.com/KHTeka-Medium.woff2","KHTeka-400-woff2":"https://fonts.reown.com/KHTeka-Regular.woff2","KHTeka-300-woff2":"https://fonts.reown.com/KHTeka-Light.woff2","KHTekaMono-400-woff2":"https://fonts.reown.com/KHTekaMono-Regular.woff2","KHTeka-500-woff":"https://fonts.reown.com/KHTeka-Light.woff","KHTeka-400-woff":"https://fonts.reown.com/KHTeka-Regular.woff","KHTeka-300-woff":"https://fonts.reown.com/KHTeka-Light.woff","KHTekaMono-400-woff":"https://fonts.reown.com/KHTekaMono-Regular.woff"};function j(e,t="dark"){C&&document.head.removeChild(C),C=document.createElement("style"),C.textContent=x.createRootStyles(t,e),document.head.appendChild(C)}function mt(e,t="dark"){if(L=e,v=document.createElement("style"),b=document.createElement("style"),m=document.createElement("style"),v.textContent=T(e).core.cssText,b.textContent=T(e).dark.cssText,m.textContent=T(e).light.cssText,document.head.appendChild(v),document.head.appendChild(b),document.head.appendChild(m),j(e,t),xe(t),!(e?.["--apkt-font-family"]||e?.["--w3m-font-family"]))for(const[r,n]of Object.entries($)){const o=document.createElement("link");o.rel="preload",o.href=n,o.as="font",o.type=r.includes("woff2")?"font/woff2":"font/woff",o.crossOrigin="anonymous",document.head.appendChild(o)}xe(t)}function xe(e="dark"){b&&m&&C&&(e==="light"?(j(L,e),b.removeAttribute("media"),m.media="enabled"):(j(L,e),m.removeAttribute("media"),b.media="enabled"))}function ft(e){if(L=e,v&&b&&m){v.textContent=T(e).core.cssText,b.textContent=T(e).dark.cssText,m.textContent=T(e).light.cssText;const t=e?.["--apkt-font-family"]||e?.["--w3m-font-family"];t&&(v.textContent=v.textContent?.replace("font-family: KHTeka",`font-family: ${t}`),b.textContent=b.textContent?.replace("font-family: KHTeka",`font-family: ${t}`),m.textContent=m.textContent?.replace("font-family: KHTeka",`font-family: ${t}`))}C&&j(e,m?.media==="enabled"?"light":"dark")}function T(e){return{core:y`
      ${e?.["--apkt-font-family"]||e?.["--w3m-font-family"]?y``:y`
            @font-face {
              font-family: 'KHTeka';
              src:
                url(${g($["KHTeka-400-woff2"])}) format('woff2'),
                url(${g($["KHTeka-400-woff"])}) format('woff');
              font-weight: 400;
              font-style: normal;
              font-display: swap;
            }

            @font-face {
              font-family: 'KHTeka';
              src:
                url(${g($["KHTeka-300-woff2"])}) format('woff2'),
                url(${g($["KHTeka-300-woff"])}) format('woff');
              font-weight: 300;
              font-style: normal;
            }

            @font-face {
              font-family: 'KHTekaMono';
              src:
                url(${g($["KHTekaMono-400-woff2"])}) format('woff2'),
                url(${g($["KHTekaMono-400-woff"])}) format('woff');
              font-weight: 400;
              font-style: normal;
            }

            @font-face {
              font-family: 'KHTeka';
              src:
                url(${g($["KHTeka-400-woff2"])}) format('woff2'),
                url(${g($["KHTeka-400-woff"])}) format('woff');
              font-weight: 400;
              font-style: normal;
            }
          `}

      @keyframes w3m-shake {
        0% {
          transform: scale(1) rotate(0deg);
        }
        20% {
          transform: scale(1) rotate(-1deg);
        }
        40% {
          transform: scale(1) rotate(1.5deg);
        }
        60% {
          transform: scale(1) rotate(-1.5deg);
        }
        80% {
          transform: scale(1) rotate(1deg);
        }
        100% {
          transform: scale(1) rotate(0deg);
        }
      }
      @keyframes w3m-iframe-fade-out {
        0% {
          opacity: 1;
        }
        100% {
          opacity: 0;
        }
      }
      @keyframes w3m-iframe-zoom-in {
        0% {
          transform: translateY(50px);
          opacity: 0;
        }
        100% {
          transform: translateY(0px);
          opacity: 1;
        }
      }
      @keyframes w3m-iframe-zoom-in-mobile {
        0% {
          transform: scale(0.95);
          opacity: 0;
        }
        100% {
          transform: scale(1);
          opacity: 1;
        }
      }
      :root {
        --apkt-modal-width: 370px;

        --apkt-visual-size-inherit: inherit;
        --apkt-visual-size-sm: 40px;
        --apkt-visual-size-md: 55px;
        --apkt-visual-size-lg: 80px;

        --apkt-path-network-sm: path(
          'M15.4 2.1a5.21 5.21 0 0 1 5.2 0l11.61 6.7a5.21 5.21 0 0 1 2.61 4.52v13.4c0 1.87-1 3.59-2.6 4.52l-11.61 6.7c-1.62.93-3.6.93-5.22 0l-11.6-6.7a5.21 5.21 0 0 1-2.61-4.51v-13.4c0-1.87 1-3.6 2.6-4.52L15.4 2.1Z'
        );

        --apkt-path-network-md: path(
          'M43.4605 10.7248L28.0485 1.61089C25.5438 0.129705 22.4562 0.129705 19.9515 1.61088L4.53951 10.7248C2.03626 12.2051 0.5 14.9365 0.5 17.886V36.1139C0.5 39.0635 2.03626 41.7949 4.53951 43.2752L19.9515 52.3891C22.4562 53.8703 25.5438 53.8703 28.0485 52.3891L43.4605 43.2752C45.9637 41.7949 47.5 39.0635 47.5 36.114V17.8861C47.5 14.9365 45.9637 12.2051 43.4605 10.7248Z'
        );

        --apkt-path-network-lg: path(
          'M78.3244 18.926L50.1808 2.45078C45.7376 -0.150261 40.2624 -0.150262 35.8192 2.45078L7.6756 18.926C3.23322 21.5266 0.5 26.3301 0.5 31.5248V64.4752C0.5 69.6699 3.23322 74.4734 7.6756 77.074L35.8192 93.5492C40.2624 96.1503 45.7376 96.1503 50.1808 93.5492L78.3244 77.074C82.7668 74.4734 85.5 69.6699 85.5 64.4752V31.5248C85.5 26.3301 82.7668 21.5266 78.3244 18.926Z'
        );

        --apkt-width-network-sm: 36px;
        --apkt-width-network-md: 48px;
        --apkt-width-network-lg: 86px;

        --apkt-duration-dynamic: 0ms;
        --apkt-height-network-sm: 40px;
        --apkt-height-network-md: 54px;
        --apkt-height-network-lg: 96px;
      }
    `,dark:y`
      :root {
      }
    `,light:y`
      :root {
      }
    `}}var bt=y`
  div,
  span,
  iframe,
  a,
  img,
  form,
  button,
  label,
  *::after,
  *::before {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-style: normal;
    text-rendering: optimizeSpeed;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    -webkit-tap-highlight-color: transparent;
    backface-visibility: hidden;
  }

  :host {
    font-family: var(--apkt-fontFamily-regular);
  }
`,$t=y`
  button,
  a {
    cursor: pointer;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;

    will-change: background-color, color, border, box-shadow, width, height, transform, opacity;
    outline: none;
    border: none;
    text-decoration: none;
    transition:
      background-color var(--apkt-durations-lg) var(--apkt-easings-ease-out-power-2),
      color var(--apkt-durations-lg) var(--apkt-easings-ease-out-power-2),
      border var(--apkt-durations-lg) var(--apkt-easings-ease-out-power-2),
      box-shadow var(--apkt-durations-lg) var(--apkt-easings-ease-out-power-2),
      width var(--apkt-durations-lg) var(--apkt-easings-ease-out-power-2),
      height var(--apkt-durations-lg) var(--apkt-easings-ease-out-power-2),
      transform var(--apkt-durations-lg) var(--apkt-easings-ease-out-power-2),
      opacity var(--apkt-durations-lg) var(--apkt-easings-ease-out-power-2),
      scale var(--apkt-durations-lg) var(--apkt-easings-ease-out-power-2),
      border-radius var(--apkt-durations-lg) var(--apkt-easings-ease-out-power-2);
    will-change:
      background-color, color, border, box-shadow, width, height, transform, opacity, scale,
      border-radius;
  }

  a:active:not([disabled]),
  button:active:not([disabled]) {
    scale: 0.975;
    transform-origin: center;
  }

  button:disabled {
    cursor: default;
  }

  input {
    border: none;
    outline: none;
    appearance: none;
  }
`,D=".",xt={getSpacingStyles(e,t){if(Array.isArray(e))return e[t]?`var(--apkt-spacing-${e[t]})`:void 0;if(typeof e=="string")return`var(--apkt-spacing-${e})`},getFormattedDate(e){return new Intl.DateTimeFormat("en-US",{month:"short",day:"numeric"}).format(e)},formatCurrency(e=0,t={}){const r=Number(e);return isNaN(r)?"$0.00":new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",minimumFractionDigits:2,maximumFractionDigits:2,...t}).format(r)},getHostName(e){try{return new URL(e).hostname}catch{return""}},getTruncateString({string:e,charsStart:t,charsEnd:r,truncate:n}){return e.length<=t+r?e:n==="end"?`${e.substring(0,t)}...`:n==="start"?`...${e.substring(e.length-r)}`:`${e.substring(0,Math.floor(t))}...${e.substring(e.length-Math.floor(r))}`},generateAvatarColors(e){const t=e.toLowerCase().replace(/^0x/iu,"").replace(/[^a-f0-9]/gu,"").substring(0,6).padEnd(6,"0"),r=this.hexToRgb(t),n=getComputedStyle(document.documentElement).getPropertyValue("--w3m-border-radius-master"),o=100-3*Number(n?.replace("px","")),i=`${o}% ${o}% at 65% 40%`,a=[];for(let s=0;s<5;s+=1){const c=this.tintColor(r,.15*s);a.push(`rgb(${c[0]}, ${c[1]}, ${c[2]})`)}return`
    --local-color-1: ${a[0]};
    --local-color-2: ${a[1]};
    --local-color-3: ${a[2]};
    --local-color-4: ${a[3]};
    --local-color-5: ${a[4]};
    --local-radial-circle: ${i}
   `},hexToRgb(e){const t=parseInt(e,16);return[t>>16&255,t>>8&255,t&255]},tintColor(e,t){const[r,n,o]=e;return[Math.round(r+(255-r)*t),Math.round(n+(255-n)*t),Math.round(o+(255-o)*t)]},isNumber(e){return/^[0-9]+$/u.test(e)},getColorTheme(e){return e||(typeof window<"u"&&window.matchMedia&&typeof window.matchMedia=="function"?window.matchMedia("(prefers-color-scheme: dark)")?.matches?"dark":"light":"dark")},splitBalance(e){const t=e.split(".");return t.length===2?[t[0],t[1]]:["0","00"]},roundNumber(e,t,r){return e.toString().length>=t?Number(e).toFixed(r):e},cssDurationToNumber(e){return e.endsWith("s")?Number(e.replace("s",""))*1e3:e.endsWith("ms")?Number(e.replace("ms","")):0},maskInput({value:e,decimals:t,integers:r}){if(e=e.replace(",","."),e===D)return`0${D}`;const[n="",o]=e.split(D).map(c=>c.replace(/[^0-9]/gu,"")),i=r?n.substring(0,r):n,a=i.length===2?String(Number(i)):i,s=typeof t=="number"?o?.substring(0,t):o;return(typeof s=="string"&&(typeof t!="number"||t>0)?[a,s].join(D):a)??""},capitalize(e){return e?e.charAt(0).toUpperCase()+e.slice(1):""}};function ot(e,t){const{kind:r,elements:n}=t;return{kind:r,elements:n,finisher(o){customElements.get(e)||customElements.define(e,o)}}}function it(e,t){return customElements.get(e)||customElements.define(e,t),t}function At(e){return function(r){return typeof r=="function"?it(e,r):ot(e,r)}}var st={METMASK_CONNECTOR_NAME:"MetaMask",TRUST_CONNECTOR_NAME:"Trust Wallet",SOLFLARE_CONNECTOR_NAME:"Solflare",PHANTOM_CONNECTOR_NAME:"Phantom",COIN98_CONNECTOR_NAME:"Coin98",MAGIC_EDEN_CONNECTOR_NAME:"Magic Eden",BACKPACK_CONNECTOR_NAME:"Backpack",BITGET_CONNECTOR_NAME:"Bitget Wallet",FRONTIER_CONNECTOR_NAME:"Frontier",XVERSE_CONNECTOR_NAME:"Xverse Wallet",LEATHER_CONNECTOR_NAME:"Leather",OKX_CONNECTOR_NAME:"OKX Wallet",BINANCE_CONNECTOR_NAME:"Binance Wallet",EIP155:P.CHAIN.EVM,ADD_CHAIN_METHOD:"wallet_addEthereumChain",EIP6963_ANNOUNCE_EVENT:"eip6963:announceProvider",EIP6963_REQUEST_EVENT:"eip6963:requestProvider",CONNECTOR_RDNS_MAP:{coinbaseWallet:"com.coinbase.wallet",coinbaseWalletSDK:"com.coinbase.wallet"},CONNECTOR_TYPE_EXTERNAL:"EXTERNAL",CONNECTOR_TYPE_WALLET_CONNECT:"WALLET_CONNECT",CONNECTOR_TYPE_INJECTED:"INJECTED",CONNECTOR_TYPE_ANNOUNCED:"ANNOUNCED",CONNECTOR_TYPE_AUTH:"AUTH",CONNECTOR_TYPE_MULTI_CHAIN:"MULTI_CHAIN",CONNECTOR_TYPE_W3M_AUTH:"AUTH",getSDKVersionWarningMessage(e,t){return`
     @@@@@@@           @@@@@@@@@@@@@@@@@@      
   @@@@@@@@@@@      @@@@@@@@@@@@@@@@@@@@@@@@   
  @@@@@@@@@@@@@    @@@@@@@@@@@@@@@@@@@@@@@@@@  
 @@@@@@@@@@@@@@@  @@@@@@@@@@@@@@@@@@@@@@@@@@@  
 @@@@@@@@@@@@@@@  @@@@@@@@@@@@@@   @@@@@@@@@@@ 
 @@@@@@@@@@@@@@@  @@@@@@@@@@@@@   @@@@@@@@@@@@ 
 @@@@@@@@@@@@@@@  @@@@@@@@@@@@@  @@@@@@@@@@@@@
 @@@@@@@@@@@@@@@  @@@@@@@@@@@@   @@@@@@@@@@@@@    
 @@@@@@   @@@@@@  @@@@@@@@@@@   @@@@@@@@@@@@@@    
 @@@@@@   @@@@@@  @@@@@@@@@@@  @@@@@@@@@@@@@@@ 
 @@@@@@@@@@@@@@@  @@@@@@@@@@   @@@@@@@@@@@@@@@ 
 @@@@@@@@@@@@@@@  @@@@@@@@@@@@@@@@@@@@@@@@@@@  
  @@@@@@@@@@@@@    @@@@@@@@@@@@@@@@@@@@@@@@@@  
   @@@@@@@@@@@      @@@@@@@@@@@@@@@@@@@@@@@@   
      @@@@@            @@@@@@@@@@@@@@@@@@  
      
AppKit SDK version ${e} is outdated. Latest version is ${t}. Please update to the latest version for bug fixes and new features.
            
Changelog: https://github.com/reown-com/appkit/releases
NPM Registry: https://www.npmjs.com/package/@reown/appkit`}},at={getCaipTokens(e){if(!e)return;const t={};return Object.entries(e).forEach(([r,n])=>{t[`${st.EIP155}:${r}`]=n}),t},isLowerCaseMatch(e,t){return e?.toLowerCase()===t?.toLowerCase()},getActiveNamespaceConnectedToAuth(){const e=Me.state.activeChain;return P.AUTH_CONNECTOR_SUPPORTED_CHAINS.find(t=>Oe.getConnectorId(t)===P.CONNECTOR_ID.AUTH&&t===e)},withRetry({conditionFn:e,intervalMs:t,maxRetries:r}){let n=0;return new Promise(o=>{async function i(){return n+=1,await e()?o(!0):n>=r?o(!1):(setTimeout(i,t),null)}i()})},userChainIdToChainNamespace(e){if(typeof e=="number")return P.CHAIN.EVM;const[t]=e.split(":");return t},getOtherAuthNamespaces(e){return e?P.AUTH_CONNECTOR_SUPPORTED_CHAINS.filter(t=>t!==e):[]},getConnectorStorageInfo(e,t){const r=se.getConnections()[t]??[];return{hasDisconnected:se.isConnectorDisconnected(e,t),hasConnected:r.some(n=>at.isLowerCaseMatch(n.connectorId,e))}}};export{y as S,lt as _,$t as a,ye as b,xe as c,nt as d,ht as f,ut as g,N as h,xt as i,ft as l,p as m,st as n,mt as o,K as p,At as r,bt as s,at as t,gt as u,pt as v,X as x,dt as y};

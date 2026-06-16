import{l as zt,r as k}from"./dist-C9thfrVX.js";import{C as Ie,D as Ct,E as ft,H as _t,J as it,M as Ut,N as xt,T as le,b as qt,c as L,g as Et,h as Ne,j as M,k as V,l as Ft,m as X,n as oe,t as z,v as G,x as nt,y as P}from"./ApiController-Cl_P8qug.js";import{S as Rt,_ as u,a as be,i as ae,m as gt,p as j,r as N,s as Z,t as Vt,u as q,v as Ht,y as Me}from"./HelpersUtil-BgIQWZjR.js";import{a as Kt,c as w,i as Gt,o as D,r as Jt,s as A,t as Qt}from"./wui-list-item-JbIagN-a.js";import{t as Yt}from"./CaipNetworkUtil-43FjdrnS.js";var Re=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},he=class extends j{constructor(){super(),this.unsubscribe=[],this.tabIdx=void 0,this.connectors=X.state.connectors,this.count=z.state.count,this.filteredCount=z.state.filteredWallets.length,this.isFetchingRecommendedWallets=z.state.isFetchingRecommendedWallets,this.unsubscribe.push(X.subscribeKey("connectors",t=>this.connectors=t),z.subscribeKey("count",t=>this.count=t),z.subscribeKey("filteredWallets",t=>this.filteredCount=t.length),z.subscribeKey("isFetchingRecommendedWallets",t=>this.isFetchingRecommendedWallets=t))}disconnectedCallback(){this.unsubscribe.forEach(t=>t())}render(){const t=this.connectors.find(c=>c.id==="walletConnect"),{allWallets:o}=V.state;if(!t||o==="HIDE"||o==="ONLY_MOBILE"&&!M.isMobile())return null;const r=z.state.featured.length,n=this.count+r,i=n<10?n:Math.floor(n/10)*10,a=this.filteredCount>0?this.filteredCount:i;let s=`${a}`;this.filteredCount>0?s=`${this.filteredCount}`:a<n&&(s=`${a}+`);const l=L.hasAnyConnection(it.CONNECTOR_ID.WALLET_CONNECT);return u`
      <wui-list-wallet
        name="Search Wallet"
        walletIcon="search"
        showAllWallets
        @click=${this.onAllWallets.bind(this)}
        tagLabel=${s}
        tagVariant="info"
        data-testid="all-wallets"
        tabIdx=${D(this.tabIdx)}
        .loading=${this.isFetchingRecommendedWallets}
        ?disabled=${l}
        size="sm"
      ></wui-list-wallet>
    `}onAllWallets(){G.sendEvent({type:"track",event:"CLICK_ALL_WALLETS"}),P.push("AllWallets",{redirectView:P.state.data?.redirectView})}};Re([w()],he.prototype,"tabIdx",void 0);Re([A()],he.prototype,"connectors",void 0);Re([A()],he.prototype,"count",void 0);Re([A()],he.prototype,"filteredCount",void 0);Re([A()],he.prototype,"isFetchingRecommendedWallets",void 0);he=Re([N("w3m-all-wallets-widget")],he);var Xt=q`
  :host {
    margin-top: ${({spacing:e})=>e[1]};
  }
  wui-separator {
    margin: ${({spacing:e})=>e[3]} calc(${({spacing:e})=>e[3]} * -1)
      ${({spacing:e})=>e[2]} calc(${({spacing:e})=>e[3]} * -1);
    width: calc(100% + ${({spacing:e})=>e[3]} * 2);
  }
`,Se=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},ce=class extends j{constructor(){super(),this.unsubscribe=[],this.explorerWallets=z.state.explorerWallets,this.connections=L.state.connections,this.connectorImages=ft.state.connectorImages,this.loadingTelegram=!1,this.unsubscribe.push(L.subscribeKey("connections",t=>this.connections=t),ft.subscribeKey("connectorImages",t=>this.connectorImages=t),z.subscribeKey("explorerFilteredWallets",t=>{this.explorerWallets=t?.length?t:z.state.explorerWallets}),z.subscribeKey("explorerWallets",t=>{this.explorerWallets?.length||(this.explorerWallets=t)})),M.isTelegram()&&M.isIos()&&(this.loadingTelegram=!L.state.wcUri,this.unsubscribe.push(L.subscribeKey("wcUri",t=>this.loadingTelegram=!t)))}disconnectedCallback(){this.unsubscribe.forEach(t=>t())}render(){return u`
      <wui-flex flexDirection="column" gap="2"> ${this.connectorListTemplate()} </wui-flex>
    `}connectorListTemplate(){return qt.connectorList().map((t,o)=>t.kind==="connector"?this.renderConnector(t,o):this.renderWallet(t,o))}getConnectorNamespaces(t){return t.subtype==="walletConnect"?[]:t.subtype==="multiChain"?t.connector.connectors?.map(o=>o.chain)||[]:[t.connector.chain]}renderConnector(t,o){const r=t.connector,n=le.getConnectorImage(r)||this.connectorImages[r?.imageId??""],i=(this.connections.get(r.chain)??[]).some(d=>Vt.isLowerCaseMatch(d.connectorId,r.id));let a,s;t.subtype==="walletConnect"?(a="qr code",s="accent"):t.subtype==="injected"||t.subtype==="announced"?(a=i?"connected":"installed",s=i?"info":"success"):(a=void 0,s=void 0);const l=L.hasAnyConnection(it.CONNECTOR_ID.WALLET_CONNECT),c=t.subtype==="walletConnect"||t.subtype==="external"?l:!1;return u`
      <w3m-list-wallet
        displayIndex=${o}
        imageSrc=${D(n)}
        .installed=${!0}
        name=${r.name??"Unknown"}
        .tagVariant=${s}
        tagLabel=${D(a)}
        data-testid=${`wallet-selector-${r.id.toLowerCase()}`}
        size="sm"
        @click=${()=>this.onClickConnector(t)}
        tabIdx=${D(this.tabIdx)}
        ?disabled=${c}
        rdnsId=${D(r.explorerWallet?.rdns||void 0)}
        walletRank=${D(r.explorerWallet?.order)}
        .namespaces=${this.getConnectorNamespaces(t)}
      >
      </w3m-list-wallet>
    `}onClickConnector(t){const o=P.state.data?.redirectView;if(t.subtype==="walletConnect"){X.setActiveConnector(t.connector),M.isMobile()?P.push("AllWallets"):P.push("ConnectingWalletConnect",{redirectView:o});return}if(t.subtype==="multiChain"){X.setActiveConnector(t.connector),P.push("ConnectingMultiChain",{redirectView:o});return}if(t.subtype==="injected"){X.setActiveConnector(t.connector),P.push("ConnectingExternal",{connector:t.connector,redirectView:o,wallet:t.connector.explorerWallet});return}if(t.subtype==="announced"){if(t.connector.id==="walletConnect"){M.isMobile()?P.push("AllWallets"):P.push("ConnectingWalletConnect",{redirectView:o});return}P.push("ConnectingExternal",{connector:t.connector,redirectView:o,wallet:t.connector.explorerWallet});return}P.push("ConnectingExternal",{connector:t.connector,redirectView:o})}renderWallet(t,o){const r=t.wallet,n=le.getWalletImage(r),i=L.hasAnyConnection(it.CONNECTOR_ID.WALLET_CONNECT),a=this.loadingTelegram,s=t.subtype==="recent"?"recent":void 0,l=t.subtype==="recent"?"info":void 0;return u`
      <w3m-list-wallet
        displayIndex=${o}
        imageSrc=${D(n)}
        name=${r.name??"Unknown"}
        @click=${()=>this.onClickWallet(t)}
        size="sm"
        data-testid=${`wallet-selector-${r.id}`}
        tabIdx=${D(this.tabIdx)}
        ?loading=${a}
        ?disabled=${i}
        rdnsId=${D(r.rdns||void 0)}
        walletRank=${D(r.order)}
        tagLabel=${D(s)}
        .tagVariant=${l}
      >
      </w3m-list-wallet>
    `}onClickWallet(t){const o=P.state.data?.redirectView,r=oe.state.activeChain;if(t.subtype==="featured"){X.selectWalletConnector(t.wallet);return}if(t.subtype==="recent"){if(this.loadingTelegram)return;X.selectWalletConnector(t.wallet);return}if(t.subtype==="custom"){if(this.loadingTelegram)return;P.push("ConnectingWalletConnect",{wallet:t.wallet,redirectView:o});return}if(this.loadingTelegram)return;const n=r?X.getConnector({id:t.wallet.id,namespace:r}):void 0;n?P.push("ConnectingExternal",{connector:n,redirectView:o}):P.push("ConnectingWalletConnect",{wallet:t.wallet,redirectView:o})}};ce.styles=Xt;Se([w({type:Number})],ce.prototype,"tabIdx",void 0);Se([A()],ce.prototype,"explorerWallets",void 0);Se([A()],ce.prototype,"connections",void 0);Se([A()],ce.prototype,"connectorImages",void 0);Se([A()],ce.prototype,"loadingTelegram",void 0);ce=Se([N("w3m-connector-list")],ce);var Zt=q`
  :host {
    flex: 1;
    height: 100%;
  }

  button {
    width: 100%;
    height: 100%;
    display: inline-flex;
    align-items: center;
    padding: ${({spacing:e})=>e[1]} ${({spacing:e})=>e[2]};
    column-gap: ${({spacing:e})=>e[1]};
    color: ${({tokens:e})=>e.theme.textSecondary};
    border-radius: ${({borderRadius:e})=>e[20]};
    background-color: transparent;
    transition: background-color ${({durations:e})=>e.lg}
      ${({easings:e})=>e["ease-out-power-2"]};
    will-change: background-color;
  }

  /* -- Hover & Active states ----------------------------------------------------------- */
  button[data-active='true'] {
    color: ${({tokens:e})=>e.theme.textPrimary};
    background-color: ${({tokens:e})=>e.theme.foregroundTertiary};
  }

  button:hover:enabled:not([data-active='true']),
  button:active:enabled:not([data-active='true']) {
    wui-text,
    wui-icon {
      color: ${({tokens:e})=>e.theme.textPrimary};
    }
  }
`,We=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},ei={lg:"lg-regular",md:"md-regular",sm:"sm-regular"},ti={lg:"md",md:"sm",sm:"sm"},pe=class extends j{constructor(){super(...arguments),this.icon="mobile",this.size="md",this.label="",this.active=!1}render(){return u`
      <button data-active=${this.active}>
        ${this.icon?u`<wui-icon size=${ti[this.size]} name=${this.icon}></wui-icon>`:""}
        <wui-text variant=${ei[this.size]}> ${this.label} </wui-text>
      </button>
    `}};pe.styles=[Z,be,Zt];We([w()],pe.prototype,"icon",void 0);We([w()],pe.prototype,"size",void 0);We([w()],pe.prototype,"label",void 0);We([w({type:Boolean})],pe.prototype,"active",void 0);pe=We([N("wui-tab-item")],pe);var ii=q`
  :host {
    display: inline-flex;
    align-items: center;
    background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
    border-radius: ${({borderRadius:e})=>e[32]};
    padding: ${({spacing:e})=>e["01"]};
    box-sizing: border-box;
  }

  :host([data-size='sm']) {
    height: 26px;
  }

  :host([data-size='md']) {
    height: 36px;
  }
`,Pe=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},fe=class extends j{constructor(){super(...arguments),this.tabs=[],this.onTabChange=()=>null,this.size="md",this.activeTab=0}render(){return this.dataset.size=this.size,this.tabs.map((t,o)=>{const r=o===this.activeTab;return u`
        <wui-tab-item
          @click=${()=>this.onTabClick(o)}
          icon=${t.icon}
          size=${this.size}
          label=${t.label}
          ?active=${r}
          data-active=${r}
          data-testid="tab-${t.label?.toLowerCase()}"
        ></wui-tab-item>
      `})}onTabClick(t){this.activeTab=t,this.onTabChange(t)}};fe.styles=[Z,be,ii];Pe([w({type:Array})],fe.prototype,"tabs",void 0);Pe([w()],fe.prototype,"onTabChange",void 0);Pe([w()],fe.prototype,"size",void 0);Pe([A()],fe.prototype,"activeTab",void 0);fe=Pe([N("wui-tabs")],fe);var ot=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},Oe=class extends j{constructor(){super(...arguments),this.platformTabs=[],this.unsubscribe=[],this.platforms=[],this.onSelectPlatfrom=void 0}disconnectCallback(){this.unsubscribe.forEach(t=>t())}render(){return u`
      <wui-flex justifyContent="center" .padding=${["0","0","4","0"]}>
        <wui-tabs .tabs=${this.generateTabs()} .onTabChange=${this.onTabChange.bind(this)}></wui-tabs>
      </wui-flex>
    `}generateTabs(){const t=this.platforms.map(o=>o==="browser"?{label:"Browser",icon:"extension",platform:"browser"}:o==="mobile"?{label:"Mobile",icon:"mobile",platform:"mobile"}:o==="qrcode"?{label:"Mobile",icon:"mobile",platform:"qrcode"}:o==="web"?{label:"Webapp",icon:"browser",platform:"web"}:o==="desktop"?{label:"Desktop",icon:"desktop",platform:"desktop"}:{label:"Browser",icon:"extension",platform:"unsupported"});return this.platformTabs=t.map(({platform:o})=>o),t}onTabChange(t){const o=this.platformTabs[t];o&&this.onSelectPlatfrom?.(o)}};ot([w({type:Array})],Oe.prototype,"platforms",void 0);ot([w()],Oe.prototype,"onSelectPlatfrom",void 0);Oe=ot([N("w3m-connecting-header")],Oe);var ni=q`
  :host {
    display: block;
    width: 100px;
    height: 100px;
  }

  svg {
    width: 100px;
    height: 100px;
  }

  rect {
    fill: none;
    stroke: ${e=>e.colors.accent100};
    stroke-width: 3px;
    stroke-linecap: round;
    animation: dash 1s linear infinite;
  }

  @keyframes dash {
    to {
      stroke-dashoffset: 0px;
    }
  }
`,St=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},je=class extends j{constructor(){super(...arguments),this.radius=36}render(){return this.svgLoaderTemplate()}svgLoaderTemplate(){const t=this.radius>50?50:this.radius,o=36-t;return u`
      <svg viewBox="0 0 110 110" width="110" height="110">
        <rect
          x="2"
          y="2"
          width="106"
          height="106"
          rx=${t}
          stroke-dasharray="${116+o} ${245+o}"
          stroke-dashoffset=${360+o*1.75}
        />
      </svg>
    `}};je.styles=[Z,ni];St([w({type:Number})],je.prototype,"radius",void 0);je=St([N("wui-loading-thumbnail")],je);var ri=q`
  wui-flex {
    width: 100%;
    height: 52px;
    box-sizing: border-box;
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    border-radius: ${({borderRadius:e})=>e[5]};
    padding-left: ${({spacing:e})=>e[3]};
    padding-right: ${({spacing:e})=>e[3]};
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: ${({spacing:e})=>e[6]};
  }

  wui-text {
    color: ${({tokens:e})=>e.theme.textSecondary};
  }

  wui-icon {
    width: 12px;
    height: 12px;
  }
`,Ge=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},xe=class extends j{constructor(){super(...arguments),this.disabled=!1,this.label="",this.buttonLabel=""}render(){return u`
      <wui-flex justifyContent="space-between" alignItems="center">
        <wui-text variant="lg-regular" color="inherit">${this.label}</wui-text>
        <wui-button variant="accent-secondary" size="sm">
          ${this.buttonLabel}
          <wui-icon name="chevronRight" color="inherit" size="inherit" slot="iconRight"></wui-icon>
        </wui-button>
      </wui-flex>
    `}};xe.styles=[Z,be,ri];Ge([w({type:Boolean})],xe.prototype,"disabled",void 0);Ge([w()],xe.prototype,"label",void 0);Ge([w()],xe.prototype,"buttonLabel",void 0);xe=Ge([N("wui-cta-button")],xe);var oi=q`
  :host {
    display: block;
    padding: 0 ${({spacing:e})=>e[5]} ${({spacing:e})=>e[5]};
  }
`,Tt=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},De=class extends j{constructor(){super(...arguments),this.wallet=void 0}render(){if(!this.wallet)return this.style.display="none",null;const{name:t,app_store:o,play_store:r,chrome_store:n,homepage:i}=this.wallet,a=M.isMobile(),s=M.isIos(),l=M.isAndroid(),c=[o,r,i,n].filter(Boolean).length>1,d=ae.getTruncateString({string:t,charsStart:12,charsEnd:0,truncate:"end"});return c&&!a?u`
        <wui-cta-button
          label=${`Don't have ${d}?`}
          buttonLabel="Get"
          @click=${()=>P.push("Downloads",{wallet:this.wallet})}
        ></wui-cta-button>
      `:!c&&i?u`
        <wui-cta-button
          label=${`Don't have ${d}?`}
          buttonLabel="Get"
          @click=${this.onHomePage.bind(this)}
        ></wui-cta-button>
      `:o&&s?u`
        <wui-cta-button
          label=${`Don't have ${d}?`}
          buttonLabel="Get"
          @click=${this.onAppStore.bind(this)}
        ></wui-cta-button>
      `:r&&l?u`
        <wui-cta-button
          label=${`Don't have ${d}?`}
          buttonLabel="Get"
          @click=${this.onPlayStore.bind(this)}
        ></wui-cta-button>
      `:(this.style.display="none",null)}onAppStore(){this.wallet?.app_store&&M.openHref(this.wallet.app_store,"_blank")}onPlayStore(){this.wallet?.play_store&&M.openHref(this.wallet.play_store,"_blank")}onHomePage(){this.wallet?.homepage&&M.openHref(this.wallet.homepage,"_blank")}};De.styles=[oi];Tt([w({type:Object})],De.prototype,"wallet",void 0);De=Tt([N("w3m-mobile-download-links")],De);var ai=q`
  @keyframes shake {
    0% {
      transform: translateX(0);
    }
    25% {
      transform: translateX(3px);
    }
    50% {
      transform: translateX(-3px);
    }
    75% {
      transform: translateX(3px);
    }
    100% {
      transform: translateX(0);
    }
  }

  wui-flex:first-child:not(:only-child) {
    position: relative;
  }

  wui-wallet-image {
    width: 56px;
    height: 56px;
  }

  wui-loading-thumbnail {
    position: absolute;
  }

  wui-icon-box {
    position: absolute;
    right: calc(${({spacing:e})=>e[1]} * -1);
    bottom: calc(${({spacing:e})=>e[1]} * -1);
    opacity: 0;
    transform: scale(0.5);
    transition-property: opacity, transform;
    transition-duration: ${({durations:e})=>e.lg};
    transition-timing-function: ${({easings:e})=>e["ease-out-power-2"]};
    will-change: opacity, transform;
  }

  wui-text[align='center'] {
    width: 100%;
    padding: 0px ${({spacing:e})=>e[4]};
  }

  [data-error='true'] wui-icon-box {
    opacity: 1;
    transform: scale(1);
  }

  [data-error='true'] > wui-flex:first-child {
    animation: shake 250ms ${({easings:e})=>e["ease-out-power-2"]} both;
  }

  [data-retry='false'] wui-link {
    display: none;
  }

  [data-retry='true'] wui-link {
    display: block;
    opacity: 1;
  }

  w3m-mobile-download-links {
    padding: 0px;
    width: 100%;
  }
`,ee=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},F=class extends j{constructor(){super(),this.wallet=P.state.data?.wallet,this.connector=P.state.data?.connector,this.timeout=void 0,this.secondaryBtnIcon="refresh",this.onConnect=void 0,this.onRender=void 0,this.onAutoConnect=void 0,this.isWalletConnect=!0,this.unsubscribe=[],this.imageSrc=le.getConnectorImage(this.connector)??le.getWalletImage(this.wallet),this.name=this.wallet?.name??this.connector?.name??"Wallet",this.isRetrying=!1,this.uri=L.state.wcUri,this.error=L.state.wcError,this.ready=!1,this.showRetry=!1,this.label=void 0,this.secondaryBtnLabel="Try again",this.secondaryLabel="Accept connection request in the wallet",this.isLoading=!1,this.isMobile=!1,this.onRetry=void 0,this.unsubscribe.push(L.subscribeKey("wcUri",e=>{this.uri=e,this.isRetrying&&this.onRetry&&(this.isRetrying=!1,this.onConnect?.())}),L.subscribeKey("wcError",e=>this.error=e)),(M.isTelegram()||M.isSafari())&&M.isIos()&&L.state.wcUri&&this.onConnect?.()}firstUpdated(){this.onAutoConnect?.(),this.showRetry=!this.onAutoConnect}disconnectedCallback(){this.unsubscribe.forEach(e=>e()),L.setWcError(!1),clearTimeout(this.timeout)}render(){this.onRender?.(),this.onShowRetry();const e=this.error?"Connection can be declined if a previous request is still active":this.secondaryLabel;let t="";return this.label?t=this.label:(t=`Continue in ${this.name}`,this.error&&(t="Connection declined")),u`
      <wui-flex
        data-error=${D(this.error)}
        data-retry=${this.showRetry}
        flexDirection="column"
        alignItems="center"
        .padding=${["10","5","5","5"]}
        gap="6"
      >
        <wui-flex gap="2" justifyContent="center" alignItems="center">
          <wui-wallet-image size="lg" imageSrc=${D(this.imageSrc)}></wui-wallet-image>

          ${this.error?null:this.loaderTemplate()}

          <wui-icon-box
            color="error"
            icon="close"
            size="sm"
            border
            borderColor="wui-color-bg-125"
          ></wui-icon-box>
        </wui-flex>

        <wui-flex flexDirection="column" alignItems="center" gap="6"> <wui-flex
          flexDirection="column"
          alignItems="center"
          gap="2"
          .padding=${["2","0","0","0"]}
        >
          <wui-text align="center" variant="lg-medium" color=${this.error?"error":"primary"}>
            ${t}
          </wui-text>
          <wui-text align="center" variant="lg-regular" color="secondary">${e}</wui-text>
        </wui-flex>

        ${this.secondaryBtnLabel?u`
                <wui-button
                  variant="neutral-secondary"
                  size="md"
                  ?disabled=${this.isRetrying||this.isLoading}
                  @click=${this.onTryAgain.bind(this)}
                  data-testid="w3m-connecting-widget-secondary-button"
                >
                  <wui-icon
                    color="inherit"
                    slot="iconLeft"
                    name=${this.secondaryBtnIcon}
                  ></wui-icon>
                  ${this.secondaryBtnLabel}
                </wui-button>
              `:null}
      </wui-flex>

      ${this.isWalletConnect?u`
              <wui-flex .padding=${["0","5","5","5"]} justifyContent="center">
                <wui-link
                  @click=${this.onCopyUri}
                  variant="secondary"
                  icon="copy"
                  data-testid="wui-link-copy"
                >
                  Copy link
                </wui-link>
              </wui-flex>
            `:null}

      <w3m-mobile-download-links .wallet=${this.wallet}></w3m-mobile-download-links></wui-flex>
      </wui-flex>
    `}onShowRetry(){this.error&&!this.showRetry&&(this.showRetry=!0,this.shadowRoot?.querySelector("wui-button")?.animate([{opacity:0},{opacity:1}],{fill:"forwards",easing:"ease"}))}onTryAgain(){L.setWcError(!1),this.onRetry?(this.isRetrying=!0,this.onRetry?.()):this.onConnect?.()}loaderTemplate(){const e=Ne.state.themeVariables["--w3m-border-radius-master"];return u`<wui-loading-thumbnail radius=${(e?parseInt(e.replace("px",""),10):4)*9}></wui-loading-thumbnail>`}onCopyUri(){try{this.uri&&(M.copyToClopboard(this.uri),Ie.showSuccess("Link copied"))}catch{Ie.showError("Failed to copy")}}};F.styles=ai;ee([A()],F.prototype,"isRetrying",void 0);ee([A()],F.prototype,"uri",void 0);ee([A()],F.prototype,"error",void 0);ee([A()],F.prototype,"ready",void 0);ee([A()],F.prototype,"showRetry",void 0);ee([A()],F.prototype,"label",void 0);ee([A()],F.prototype,"secondaryBtnLabel",void 0);ee([A()],F.prototype,"secondaryLabel",void 0);ee([A()],F.prototype,"isLoading",void 0);ee([w({type:Boolean})],F.prototype,"isMobile",void 0);ee([w()],F.prototype,"onRetry",void 0);var si=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},wt=class extends F{constructor(){if(super(),!this.wallet)throw new Error("w3m-connecting-wc-browser: No wallet provided");this.onConnect=this.onConnectProxy.bind(this),this.onAutoConnect=this.onConnectProxy.bind(this),G.sendEvent({type:"track",event:"SELECT_WALLET",properties:{name:this.wallet.name,platform:"browser",displayIndex:this.wallet?.display_index,walletRank:this.wallet.order,view:P.state.view}})}async onConnectProxy(){try{this.error=!1;const{connectors:t}=X.state,o=t.find(r=>r.type==="ANNOUNCED"&&r.info?.rdns===this.wallet?.rdns||r.type==="INJECTED"||r.name===this.wallet?.name);if(o)await L.connectExternal(o,o.chain);else throw new Error("w3m-connecting-wc-browser: No connector found");Et.close()}catch(t){t instanceof Ct&&t.originalName===_t.PROVIDER_RPC_ERROR_NAME.USER_REJECTED_REQUEST?G.sendEvent({type:"track",event:"USER_REJECTED",properties:{message:t.message}}):G.sendEvent({type:"track",event:"CONNECT_ERROR",properties:{message:t?.message??"Unknown"}}),this.error=!0}}};wt=si([N("w3m-connecting-wc-browser")],wt);var li=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},mt=class extends F{constructor(){if(super(),!this.wallet)throw new Error("w3m-connecting-wc-desktop: No wallet provided");this.onConnect=this.onConnectProxy.bind(this),this.onRender=this.onRenderProxy.bind(this),G.sendEvent({type:"track",event:"SELECT_WALLET",properties:{name:this.wallet.name,platform:"desktop",displayIndex:this.wallet?.display_index,walletRank:this.wallet.order,view:P.state.view}})}onRenderProxy(){!this.ready&&this.uri&&(this.ready=!0,this.onConnect?.())}onConnectProxy(){if(this.wallet?.desktop_link&&this.uri)try{this.error=!1;const{desktop_link:t,name:o}=this.wallet,{redirect:r,href:n}=M.formatNativeUrl(t,this.uri);L.setWcLinking({name:o,href:n}),L.setRecentWallet(this.wallet),M.openHref(r,"_blank")}catch{this.error=!0}}};mt=li([N("w3m-connecting-wc-desktop")],mt);var Te=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},ge=class extends F{constructor(){if(super(),this.btnLabelTimeout=void 0,this.redirectDeeplink=void 0,this.redirectUniversalLink=void 0,this.target=void 0,this.preferUniversalLinks=V.state.experimental_preferUniversalLinks,this.isLoading=!0,this.onConnect=()=>{Ft.onConnectMobile(this.wallet)},!this.wallet)throw new Error("w3m-connecting-wc-mobile: No wallet provided");this.secondaryBtnLabel="Open",this.secondaryLabel=xt.CONNECT_LABELS.MOBILE,this.secondaryBtnIcon="externalLink",this.onHandleURI(),this.unsubscribe.push(L.subscribeKey("wcUri",()=>{this.onHandleURI()})),G.sendEvent({type:"track",event:"SELECT_WALLET",properties:{name:this.wallet.name,platform:"mobile",displayIndex:this.wallet?.display_index,walletRank:this.wallet.order,view:P.state.view}})}disconnectedCallback(){super.disconnectedCallback(),clearTimeout(this.btnLabelTimeout)}onHandleURI(){this.isLoading=!this.uri,!this.ready&&this.uri&&(this.ready=!0,this.onConnect?.())}onTryAgain(){L.setWcError(!1),this.onConnect?.()}};Te([A()],ge.prototype,"redirectDeeplink",void 0);Te([A()],ge.prototype,"redirectUniversalLink",void 0);Te([A()],ge.prototype,"target",void 0);Te([A()],ge.prototype,"preferUniversalLinks",void 0);Te([A()],ge.prototype,"isLoading",void 0);ge=Te([N("w3m-connecting-wc-mobile")],ge);var ci=k(((e,t)=>{t.exports=function(){return typeof Promise=="function"&&Promise.prototype&&Promise.prototype.then}})),ve=k((e=>{var t,o=[0,26,44,70,100,134,172,196,242,292,346,404,466,532,581,655,733,815,901,991,1085,1156,1258,1364,1474,1588,1706,1828,1921,2051,2185,2323,2465,2611,2761,2876,3034,3196,3362,3532,3706];e.getSymbolSize=function(n){if(!n)throw new Error('"version" cannot be null or undefined');if(n<1||n>40)throw new Error('"version" should be in range from 1 to 40');return n*4+17},e.getSymbolTotalCodewords=function(n){return o[n]},e.getBCHDigit=function(r){let n=0;for(;r!==0;)n++,r>>>=1;return n},e.setToSJISFunction=function(n){if(typeof n!="function")throw new Error('"toSJISFunc" is not a valid function.');t=n},e.isKanjiModeEnabled=function(){return typeof t<"u"},e.toSJIS=function(n){return t(n)}})),at=k((e=>{e.L={bit:1},e.M={bit:0},e.Q={bit:3},e.H={bit:2};function t(o){if(typeof o!="string")throw new Error("Param is not a string");switch(o.toLowerCase()){case"l":case"low":return e.L;case"m":case"medium":return e.M;case"q":case"quartile":return e.Q;case"h":case"high":return e.H;default:throw new Error("Unknown EC Level: "+o)}}e.isValid=function(r){return r&&typeof r.bit<"u"&&r.bit>=0&&r.bit<4},e.from=function(r,n){if(e.isValid(r))return r;try{return t(r)}catch{return n}}})),ui=k(((e,t)=>{function o(){this.buffer=[],this.length=0}o.prototype={get:function(r){const n=Math.floor(r/8);return(this.buffer[n]>>>7-r%8&1)===1},put:function(r,n){for(let i=0;i<n;i++)this.putBit((r>>>n-i-1&1)===1)},getLengthInBits:function(){return this.length},putBit:function(r){const n=Math.floor(this.length/8);this.buffer.length<=n&&this.buffer.push(0),r&&(this.buffer[n]|=128>>>this.length%8),this.length++}},t.exports=o})),di=k(((e,t)=>{function o(r){if(!r||r<1)throw new Error("BitMatrix size must be defined and greater than 0");this.size=r,this.data=new Uint8Array(r*r),this.reservedBit=new Uint8Array(r*r)}o.prototype.set=function(r,n,i,a){const s=r*this.size+n;this.data[s]=i,a&&(this.reservedBit[s]=!0)},o.prototype.get=function(r,n){return this.data[r*this.size+n]},o.prototype.xor=function(r,n,i){this.data[r*this.size+n]^=i},o.prototype.isReserved=function(r,n){return this.reservedBit[r*this.size+n]},t.exports=o})),hi=k((e=>{var t=ve().getSymbolSize;e.getRowColCoords=function(r){if(r===1)return[];const n=Math.floor(r/7)+2,i=t(r),a=i===145?26:Math.ceil((i-13)/(2*n-2))*2,s=[i-7];for(let l=1;l<n-1;l++)s[l]=s[l-1]-a;return s.push(6),s.reverse()},e.getPositions=function(r){const n=[],i=e.getRowColCoords(r),a=i.length;for(let s=0;s<a;s++)for(let l=0;l<a;l++)s===0&&l===0||s===0&&l===a-1||s===a-1&&l===0||n.push([i[s],i[l]]);return n}})),pi=k((e=>{var t=ve().getSymbolSize,o=7;e.getPositions=function(n){const i=t(n);return[[0,0],[i-o,0],[0,i-o]]}})),fi=k((e=>{e.Patterns={PATTERN000:0,PATTERN001:1,PATTERN010:2,PATTERN011:3,PATTERN100:4,PATTERN101:5,PATTERN110:6,PATTERN111:7};var t={N1:3,N2:3,N3:40,N4:10};e.isValid=function(n){return n!=null&&n!==""&&!isNaN(n)&&n>=0&&n<=7},e.from=function(n){return e.isValid(n)?parseInt(n,10):void 0},e.getPenaltyN1=function(n){const i=n.size;let a=0,s=0,l=0,c=null,d=null;for(let T=0;T<i;T++){s=l=0,c=d=null;for(let f=0;f<i;f++){let h=n.get(T,f);h===c?s++:(s>=5&&(a+=t.N1+(s-5)),c=h,s=1),h=n.get(f,T),h===d?l++:(l>=5&&(a+=t.N1+(l-5)),d=h,l=1)}s>=5&&(a+=t.N1+(s-5)),l>=5&&(a+=t.N1+(l-5))}return a},e.getPenaltyN2=function(n){const i=n.size;let a=0;for(let s=0;s<i-1;s++)for(let l=0;l<i-1;l++){const c=n.get(s,l)+n.get(s,l+1)+n.get(s+1,l)+n.get(s+1,l+1);(c===4||c===0)&&a++}return a*t.N2},e.getPenaltyN3=function(n){const i=n.size;let a=0,s=0,l=0;for(let c=0;c<i;c++){s=l=0;for(let d=0;d<i;d++)s=s<<1&2047|n.get(c,d),d>=10&&(s===1488||s===93)&&a++,l=l<<1&2047|n.get(d,c),d>=10&&(l===1488||l===93)&&a++}return a*t.N3},e.getPenaltyN4=function(n){let i=0;const a=n.data.length;for(let s=0;s<a;s++)i+=n.data[s];return Math.abs(Math.ceil(i*100/a/5)-10)*t.N4};function o(r,n,i){switch(r){case e.Patterns.PATTERN000:return(n+i)%2===0;case e.Patterns.PATTERN001:return n%2===0;case e.Patterns.PATTERN010:return i%3===0;case e.Patterns.PATTERN011:return(n+i)%3===0;case e.Patterns.PATTERN100:return(Math.floor(n/2)+Math.floor(i/3))%2===0;case e.Patterns.PATTERN101:return n*i%2+n*i%3===0;case e.Patterns.PATTERN110:return(n*i%2+n*i%3)%2===0;case e.Patterns.PATTERN111:return(n*i%3+(n+i)%2)%2===0;default:throw new Error("bad maskPattern:"+r)}}e.applyMask=function(n,i){const a=i.size;for(let s=0;s<a;s++)for(let l=0;l<a;l++)i.isReserved(l,s)||i.xor(l,s,o(n,l,s))},e.getBestMask=function(n,i){const a=Object.keys(e.Patterns).length;let s=0,l=1/0;for(let c=0;c<a;c++){i(c),e.applyMask(c,n);const d=e.getPenaltyN1(n)+e.getPenaltyN2(n)+e.getPenaltyN3(n)+e.getPenaltyN4(n);e.applyMask(c,n),d<l&&(l=d,s=c)}return s}})),At=k((e=>{var t=at(),o=[1,1,1,1,1,1,1,1,1,1,2,2,1,2,2,4,1,2,4,4,2,4,4,4,2,4,6,5,2,4,6,6,2,5,8,8,4,5,8,8,4,5,8,11,4,8,10,11,4,9,12,16,4,9,16,16,6,10,12,18,6,10,17,16,6,11,16,19,6,13,18,21,7,14,21,25,8,16,20,25,8,17,23,25,9,17,23,34,9,18,25,30,10,20,27,32,12,21,29,35,12,23,34,37,12,25,34,40,13,26,35,42,14,28,38,45,15,29,40,48,16,31,43,51,17,33,45,54,18,35,48,57,19,37,51,60,19,38,53,63,20,40,56,66,21,43,59,70,22,45,62,74,24,47,65,77,25,49,68,81],r=[7,10,13,17,10,16,22,28,15,26,36,44,20,36,52,64,26,48,72,88,36,64,96,112,40,72,108,130,48,88,132,156,60,110,160,192,72,130,192,224,80,150,224,264,96,176,260,308,104,198,288,352,120,216,320,384,132,240,360,432,144,280,408,480,168,308,448,532,180,338,504,588,196,364,546,650,224,416,600,700,224,442,644,750,252,476,690,816,270,504,750,900,300,560,810,960,312,588,870,1050,336,644,952,1110,360,700,1020,1200,390,728,1050,1260,420,784,1140,1350,450,812,1200,1440,480,868,1290,1530,510,924,1350,1620,540,980,1440,1710,570,1036,1530,1800,570,1064,1590,1890,600,1120,1680,1980,630,1204,1770,2100,660,1260,1860,2220,720,1316,1950,2310,750,1372,2040,2430];e.getBlocksCount=function(i,a){switch(a){case t.L:return o[(i-1)*4+0];case t.M:return o[(i-1)*4+1];case t.Q:return o[(i-1)*4+2];case t.H:return o[(i-1)*4+3];default:return}},e.getTotalCodewordsCount=function(i,a){switch(a){case t.L:return r[(i-1)*4+0];case t.M:return r[(i-1)*4+1];case t.Q:return r[(i-1)*4+2];case t.H:return r[(i-1)*4+3];default:return}}})),gi=k((e=>{var t=new Uint8Array(512),o=new Uint8Array(256);(function(){let n=1;for(let i=0;i<255;i++)t[i]=n,o[n]=i,n<<=1,n&256&&(n^=285);for(let i=255;i<512;i++)t[i]=t[i-255]})(),e.log=function(n){if(n<1)throw new Error("log("+n+")");return o[n]},e.exp=function(n){return t[n]},e.mul=function(n,i){return n===0||i===0?0:t[o[n]+o[i]]}})),wi=k((e=>{var t=gi();e.mul=function(r,n){const i=new Uint8Array(r.length+n.length-1);for(let a=0;a<r.length;a++)for(let s=0;s<n.length;s++)i[a+s]^=t.mul(r[a],n[s]);return i},e.mod=function(r,n){let i=new Uint8Array(r);for(;i.length-n.length>=0;){const a=i[0];for(let l=0;l<n.length;l++)i[l]^=t.mul(n[l],a);let s=0;for(;s<i.length&&i[s]===0;)s++;i=i.slice(s)}return i},e.generateECPolynomial=function(r){let n=new Uint8Array([1]);for(let i=0;i<r;i++)n=e.mul(n,new Uint8Array([1,t.exp(i)]));return n}})),mi=k(((e,t)=>{var o=wi();function r(n){this.genPoly=void 0,this.degree=n,this.degree&&this.initialize(this.degree)}r.prototype.initialize=function(i){this.degree=i,this.genPoly=o.generateECPolynomial(this.degree)},r.prototype.encode=function(i){if(!this.genPoly)throw new Error("Encoder not initialized");const a=new Uint8Array(i.length+this.degree);a.set(i);const s=o.mod(a,this.genPoly),l=this.degree-s.length;if(l>0){const c=new Uint8Array(this.degree);return c.set(s,l),c}return s},t.exports=r})),It=k((e=>{e.isValid=function(o){return!isNaN(o)&&o>=1&&o<=40}})),Wt=k((e=>{var t="[0-9]+",o="[A-Z $%*+\\-./:]+",r="(?:[u3000-u303F]|[u3040-u309F]|[u30A0-u30FF]|[uFF00-uFFEF]|[u4E00-u9FAF]|[u2605-u2606]|[u2190-u2195]|u203B|[u2010u2015u2018u2019u2025u2026u201Cu201Du2225u2260]|[u0391-u0451]|[u00A7u00A8u00B1u00B4u00D7u00F7])+";r=r.replace(/u/g,"\\u");var n="(?:(?![A-Z0-9 $%*+\\-./:]|"+r+`)(?:.|[\r
]))+`;e.KANJI=new RegExp(r,"g"),e.BYTE_KANJI=new RegExp("[^A-Z0-9 $%*+\\-./:]+","g"),e.BYTE=new RegExp(n,"g"),e.NUMERIC=new RegExp(t,"g"),e.ALPHANUMERIC=new RegExp(o,"g");var i=new RegExp("^"+r+"$"),a=new RegExp("^[0-9]+$"),s=new RegExp("^[A-Z0-9 $%*+\\-./:]+$");e.testKanji=function(c){return i.test(c)},e.testNumeric=function(c){return a.test(c)},e.testAlphanumeric=function(c){return s.test(c)}})),ye=k((e=>{var t=It(),o=Wt();e.NUMERIC={id:"Numeric",bit:1,ccBits:[10,12,14]},e.ALPHANUMERIC={id:"Alphanumeric",bit:2,ccBits:[9,11,13]},e.BYTE={id:"Byte",bit:4,ccBits:[8,16,16]},e.KANJI={id:"Kanji",bit:8,ccBits:[8,10,12]},e.MIXED={bit:-1},e.getCharCountIndicator=function(i,a){if(!i.ccBits)throw new Error("Invalid mode: "+i);if(!t.isValid(a))throw new Error("Invalid version: "+a);return a>=1&&a<10?i.ccBits[0]:a<27?i.ccBits[1]:i.ccBits[2]},e.getBestModeForData=function(i){return o.testNumeric(i)?e.NUMERIC:o.testAlphanumeric(i)?e.ALPHANUMERIC:o.testKanji(i)?e.KANJI:e.BYTE},e.toString=function(i){if(i&&i.id)return i.id;throw new Error("Invalid mode")},e.isValid=function(i){return i&&i.bit&&i.ccBits};function r(n){if(typeof n!="string")throw new Error("Param is not a string");switch(n.toLowerCase()){case"numeric":return e.NUMERIC;case"alphanumeric":return e.ALPHANUMERIC;case"kanji":return e.KANJI;case"byte":return e.BYTE;default:throw new Error("Unknown mode: "+n)}}e.from=function(i,a){if(e.isValid(i))return i;try{return r(i)}catch{return a}}})),bi=k((e=>{var t=ve(),o=At(),r=at(),n=ye(),i=It(),a=7973,s=t.getBCHDigit(a);function l(f,h,C){for(let v=1;v<=40;v++)if(h<=e.getCapacity(v,C,f))return v}function c(f,h){return n.getCharCountIndicator(f,h)+4}function d(f,h){let C=0;return f.forEach(function(v){const x=c(v.mode,h);C+=x+v.getBitsLength()}),C}function T(f,h){for(let C=1;C<=40;C++)if(d(f,C)<=e.getCapacity(C,h,n.MIXED))return C}e.from=function(h,C){return i.isValid(h)?parseInt(h,10):C},e.getCapacity=function(h,C,v){if(!i.isValid(h))throw new Error("Invalid QR Code version");typeof v>"u"&&(v=n.BYTE);const x=(t.getSymbolTotalCodewords(h)-o.getTotalCodewordsCount(h,C))*8;if(v===n.MIXED)return x;const m=x-c(v,h);switch(v){case n.NUMERIC:return Math.floor(m/10*3);case n.ALPHANUMERIC:return Math.floor(m/11*2);case n.KANJI:return Math.floor(m/13);case n.BYTE:default:return Math.floor(m/8)}},e.getBestVersionForData=function(h,C){let v;const x=r.from(C,r.M);if(Array.isArray(h)){if(h.length>1)return T(h,x);if(h.length===0)return 1;v=h[0]}else v=h;return l(v.mode,v.getLength(),x)},e.getEncodedBits=function(h){if(!i.isValid(h)||h<7)throw new Error("Invalid QR Code version");let C=h<<12;for(;t.getBCHDigit(C)-s>=0;)C^=a<<t.getBCHDigit(C)-s;return h<<12|C}})),vi=k((e=>{var t=ve(),o=1335,r=21522,n=t.getBCHDigit(o);e.getEncodedBits=function(a,s){const l=a.bit<<3|s;let c=l<<10;for(;t.getBCHDigit(c)-n>=0;)c^=o<<t.getBCHDigit(c)-n;return(l<<10|c)^r}})),yi=k(((e,t)=>{var o=ye();function r(n){this.mode=o.NUMERIC,this.data=n.toString()}r.getBitsLength=function(i){return 10*Math.floor(i/3)+(i%3?i%3*3+1:0)},r.prototype.getLength=function(){return this.data.length},r.prototype.getBitsLength=function(){return r.getBitsLength(this.data.length)},r.prototype.write=function(i){let a,s,l;for(a=0;a+3<=this.data.length;a+=3)s=this.data.substr(a,3),l=parseInt(s,10),i.put(l,10);const c=this.data.length-a;c>0&&(s=this.data.substr(a),l=parseInt(s,10),i.put(l,c*3+1))},t.exports=r})),$i=k(((e,t)=>{var o=ye(),r=["0","1","2","3","4","5","6","7","8","9","A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"," ","$","%","*","+","-",".","/",":"];function n(i){this.mode=o.ALPHANUMERIC,this.data=i}n.getBitsLength=function(a){return 11*Math.floor(a/2)+6*(a%2)},n.prototype.getLength=function(){return this.data.length},n.prototype.getBitsLength=function(){return n.getBitsLength(this.data.length)},n.prototype.write=function(a){let s;for(s=0;s+2<=this.data.length;s+=2){let l=r.indexOf(this.data[s])*45;l+=r.indexOf(this.data[s+1]),a.put(l,11)}this.data.length%2&&a.put(r.indexOf(this.data[s]),6)},t.exports=n})),Ci=k(((e,t)=>{t.exports=function(r){for(var n=[],i=r.length,a=0;a<i;a++){var s=r.charCodeAt(a);if(s>=55296&&s<=56319&&i>a+1){var l=r.charCodeAt(a+1);l>=56320&&l<=57343&&(s=(s-55296)*1024+l-56320+65536,a+=1)}if(s<128){n.push(s);continue}if(s<2048){n.push(s>>6|192),n.push(s&63|128);continue}if(s<55296||s>=57344&&s<65536){n.push(s>>12|224),n.push(s>>6&63|128),n.push(s&63|128);continue}if(s>=65536&&s<=1114111){n.push(s>>18|240),n.push(s>>12&63|128),n.push(s>>6&63|128),n.push(s&63|128);continue}n.push(239,191,189)}return new Uint8Array(n).buffer}})),_i=k(((e,t)=>{var o=Ci(),r=ye();function n(i){this.mode=r.BYTE,typeof i=="string"&&(i=o(i)),this.data=new Uint8Array(i)}n.getBitsLength=function(a){return a*8},n.prototype.getLength=function(){return this.data.length},n.prototype.getBitsLength=function(){return n.getBitsLength(this.data.length)},n.prototype.write=function(i){for(let a=0,s=this.data.length;a<s;a++)i.put(this.data[a],8)},t.exports=n})),xi=k(((e,t)=>{var o=ye(),r=ve();function n(i){this.mode=o.KANJI,this.data=i}n.getBitsLength=function(a){return a*13},n.prototype.getLength=function(){return this.data.length},n.prototype.getBitsLength=function(){return n.getBitsLength(this.data.length)},n.prototype.write=function(i){let a;for(a=0;a<this.data.length;a++){let s=r.toSJIS(this.data[a]);if(s>=33088&&s<=40956)s-=33088;else if(s>=57408&&s<=60351)s-=49472;else throw new Error("Invalid SJIS character: "+this.data[a]+`
Make sure your charset is UTF-8`);s=(s>>>8&255)*192+(s&255),i.put(s,13)}},t.exports=n})),Ei=k(((e,t)=>{var o={single_source_shortest_paths:function(r,n,i){var a={},s={};s[n]=0;var l=o.PriorityQueue.make();l.push(n,0);for(var c,d,T,f,h,C,v,x,m;!l.empty();){c=l.pop(),d=c.value,f=c.cost,h=r[d]||{};for(T in h)h.hasOwnProperty(T)&&(C=h[T],v=f+C,x=s[T],m=typeof s[T]>"u",(m||x>v)&&(s[T]=v,l.push(T,v),a[T]=d))}if(typeof i<"u"&&typeof s[i]>"u"){var g=["Could not find a path from ",n," to ",i,"."].join("");throw new Error(g)}return a},extract_shortest_path_from_predecessor_list:function(r,n){for(var i=[],a=n;a;)i.push(a),r[a],a=r[a];return i.reverse(),i},find_path:function(r,n,i){var a=o.single_source_shortest_paths(r,n,i);return o.extract_shortest_path_from_predecessor_list(a,i)},PriorityQueue:{make:function(r){var n=o.PriorityQueue,i={},a;r=r||{};for(a in n)n.hasOwnProperty(a)&&(i[a]=n[a]);return i.queue=[],i.sorter=r.sorter||n.default_sorter,i},default_sorter:function(r,n){return r.cost-n.cost},push:function(r,n){var i={value:r,cost:n};this.queue.push(i),this.queue.sort(this.sorter)},pop:function(){return this.queue.shift()},empty:function(){return this.queue.length===0}}};typeof t<"u"&&(t.exports=o)})),Ri=k((e=>{var t=ye(),o=yi(),r=$i(),n=_i(),i=xi(),a=Wt(),s=ve(),l=Ei();function c(m){return unescape(encodeURIComponent(m)).length}function d(m,g,$){const p=[];let B;for(;(B=m.exec($))!==null;)p.push({data:B[0],index:B.index,mode:g,length:B[0].length});return p}function T(m){const g=d(a.NUMERIC,t.NUMERIC,m),$=d(a.ALPHANUMERIC,t.ALPHANUMERIC,m);let p,B;return s.isKanjiModeEnabled()?(p=d(a.BYTE,t.BYTE,m),B=d(a.KANJI,t.KANJI,m)):(p=d(a.BYTE_KANJI,t.BYTE,m),B=[]),g.concat($,p,B).sort(function(U,E){return U.index-E.index}).map(function(U){return{data:U.data,mode:U.mode,length:U.length}})}function f(m,g){switch(g){case t.NUMERIC:return o.getBitsLength(m);case t.ALPHANUMERIC:return r.getBitsLength(m);case t.KANJI:return i.getBitsLength(m);case t.BYTE:return n.getBitsLength(m)}}function h(m){return m.reduce(function(g,$){const p=g.length-1>=0?g[g.length-1]:null;return p&&p.mode===$.mode?(g[g.length-1].data+=$.data,g):(g.push($),g)},[])}function C(m){const g=[];for(let $=0;$<m.length;$++){const p=m[$];switch(p.mode){case t.NUMERIC:g.push([p,{data:p.data,mode:t.ALPHANUMERIC,length:p.length},{data:p.data,mode:t.BYTE,length:p.length}]);break;case t.ALPHANUMERIC:g.push([p,{data:p.data,mode:t.BYTE,length:p.length}]);break;case t.KANJI:g.push([p,{data:p.data,mode:t.BYTE,length:c(p.data)}]);break;case t.BYTE:g.push([{data:p.data,mode:t.BYTE,length:c(p.data)}])}}return g}function v(m,g){const $={},p={start:{}};let B=["start"];for(let U=0;U<m.length;U++){const E=m[U],W=[];for(let S=0;S<E.length;S++){const b=E[S],I=""+U+S;W.push(I),$[I]={node:b,lastCount:0},p[I]={};for(let y=0;y<B.length;y++){const _=B[y];$[_]&&$[_].node.mode===b.mode?(p[_][I]=f($[_].lastCount+b.length,b.mode)-f($[_].lastCount,b.mode),$[_].lastCount+=b.length):($[_]&&($[_].lastCount=b.length),p[_][I]=f(b.length,b.mode)+4+t.getCharCountIndicator(b.mode,g))}}B=W}for(let U=0;U<B.length;U++)p[B[U]].end=0;return{map:p,table:$}}function x(m,g){let $;const p=t.getBestModeForData(m);if($=t.from(g,p),$!==t.BYTE&&$.bit<p.bit)throw new Error('"'+m+'" cannot be encoded with mode '+t.toString($)+`.
 Suggested mode is: `+t.toString(p));switch($===t.KANJI&&!s.isKanjiModeEnabled()&&($=t.BYTE),$){case t.NUMERIC:return new o(m);case t.ALPHANUMERIC:return new r(m);case t.KANJI:return new i(m);case t.BYTE:return new n(m)}}e.fromArray=function(g){return g.reduce(function($,p){return typeof p=="string"?$.push(x(p,null)):p.data&&$.push(x(p.data,p.mode)),$},[])},e.fromString=function(g,$){const p=v(C(T(g,s.isKanjiModeEnabled())),$),B=l.find_path(p.map,"start","end"),U=[];for(let E=1;E<B.length-1;E++)U.push(p.table[B[E]].node);return e.fromArray(h(U))},e.rawSplit=function(g){return e.fromArray(T(g,s.isKanjiModeEnabled()))}})),Si=k((e=>{var t=ve(),o=at(),r=ui(),n=di(),i=hi(),a=pi(),s=fi(),l=At(),c=mi(),d=bi(),T=vi(),f=ye(),h=Ri();function C(E,W){const S=E.size,b=a.getPositions(W);for(let I=0;I<b.length;I++){const y=b[I][0],_=b[I][1];for(let R=-1;R<=7;R++)if(!(y+R<=-1||S<=y+R))for(let O=-1;O<=7;O++)_+O<=-1||S<=_+O||(R>=0&&R<=6&&(O===0||O===6)||O>=0&&O<=6&&(R===0||R===6)||R>=2&&R<=4&&O>=2&&O<=4?E.set(y+R,_+O,!0,!0):E.set(y+R,_+O,!1,!0))}}function v(E){const W=E.size;for(let S=8;S<W-8;S++){const b=S%2===0;E.set(S,6,b,!0),E.set(6,S,b,!0)}}function x(E,W){const S=i.getPositions(W);for(let b=0;b<S.length;b++){const I=S[b][0],y=S[b][1];for(let _=-2;_<=2;_++)for(let R=-2;R<=2;R++)_===-2||_===2||R===-2||R===2||_===0&&R===0?E.set(I+_,y+R,!0,!0):E.set(I+_,y+R,!1,!0)}}function m(E,W){const S=E.size,b=d.getEncodedBits(W);let I,y,_;for(let R=0;R<18;R++)I=Math.floor(R/3),y=R%3+S-8-3,_=(b>>R&1)===1,E.set(I,y,_,!0),E.set(y,I,_,!0)}function g(E,W,S){const b=E.size,I=T.getEncodedBits(W,S);let y,_;for(y=0;y<15;y++)_=(I>>y&1)===1,y<6?E.set(y,8,_,!0):y<8?E.set(y+1,8,_,!0):E.set(b-15+y,8,_,!0),y<8?E.set(8,b-y-1,_,!0):y<9?E.set(8,15-y-1+1,_,!0):E.set(8,15-y-1,_,!0);E.set(b-8,8,1,!0)}function $(E,W){const S=E.size;let b=-1,I=S-1,y=7,_=0;for(let R=S-1;R>0;R-=2)for(R===6&&R--;;){for(let O=0;O<2;O++)if(!E.isReserved(I,R-O)){let Ce=!1;_<W.length&&(Ce=(W[_]>>>y&1)===1),E.set(I,R-O,Ce),y--,y===-1&&(_++,y=7)}if(I+=b,I<0||S<=I){I-=b,b=-b;break}}}function p(E,W,S){const b=new r;S.forEach(function(_){b.put(_.mode.bit,4),b.put(_.getLength(),f.getCharCountIndicator(_.mode,E)),_.write(b)});const I=(t.getSymbolTotalCodewords(E)-l.getTotalCodewordsCount(E,W))*8;for(b.getLengthInBits()+4<=I&&b.put(0,4);b.getLengthInBits()%8!==0;)b.putBit(0);const y=(I-b.getLengthInBits())/8;for(let _=0;_<y;_++)b.put(_%2?17:236,8);return B(b,E,W)}function B(E,W,S){const b=t.getSymbolTotalCodewords(W),I=b-l.getTotalCodewordsCount(W,S),y=l.getBlocksCount(W,S),_=y-b%y,R=Math.floor(b/y),O=Math.floor(I/y),Ce=O+1,dt=R-O,jt=new c(dt);let Qe=0;const ke=new Array(y),ht=new Array(y);let Ye=0;const Dt=new Uint8Array(E.buffer);for(let _e=0;_e<y;_e++){const Ze=_e<_?O:Ce;ke[_e]=Dt.slice(Qe,Qe+Ze),ht[_e]=jt.encode(ke[_e]),Qe+=Ze,Ye=Math.max(Ye,Ze)}const Xe=new Uint8Array(b);let pt=0,ne,re;for(ne=0;ne<Ye;ne++)for(re=0;re<y;re++)ne<ke[re].length&&(Xe[pt++]=ke[re][ne]);for(ne=0;ne<dt;ne++)for(re=0;re<y;re++)Xe[pt++]=ht[re][ne];return Xe}function U(E,W,S,b){let I;if(Array.isArray(E))I=h.fromArray(E);else if(typeof E=="string"){let O=W;if(!O){const Ce=h.rawSplit(E);O=d.getBestVersionForData(Ce,S)}I=h.fromString(E,O||40)}else throw new Error("Invalid data");const y=d.getBestVersionForData(I,S);if(!y)throw new Error("The amount of data is too big to be stored in a QR Code");if(!W)W=y;else if(W<y)throw new Error(`
The chosen QR Code version cannot contain this amount of data.
Minimum version required to store current data is: `+y+`.
`);const _=p(W,S,I),R=new n(t.getSymbolSize(W));return C(R,W),v(R),x(R,W),g(R,S,0),W>=7&&m(R,W),$(R,_),isNaN(b)&&(b=s.getBestMask(R,g.bind(null,R,S))),s.applyMask(b,R),g(R,S,b),{modules:R,version:W,errorCorrectionLevel:S,maskPattern:b,segments:I}}e.create=function(W,S){if(typeof W>"u"||W==="")throw new Error("No input text");let b=o.M,I,y;return typeof S<"u"&&(b=o.from(S.errorCorrectionLevel,o.M),I=d.from(S.version),y=s.from(S.maskPattern),S.toSJISFunc&&t.setToSJISFunction(S.toSJISFunc)),U(W,I,b,y)}})),Pt=k((e=>{function t(o){if(typeof o=="number"&&(o=o.toString()),typeof o!="string")throw new Error("Color should be defined as hex string");let r=o.slice().replace("#","").split("");if(r.length<3||r.length===5||r.length>8)throw new Error("Invalid hex color: "+o);(r.length===3||r.length===4)&&(r=Array.prototype.concat.apply([],r.map(function(i){return[i,i]}))),r.length===6&&r.push("F","F");const n=parseInt(r.join(""),16);return{r:n>>24&255,g:n>>16&255,b:n>>8&255,a:n&255,hex:"#"+r.slice(0,6).join("")}}e.getOptions=function(r){r||(r={}),r.color||(r.color={});const n=typeof r.margin>"u"||r.margin===null||r.margin<0?4:r.margin,i=r.width&&r.width>=21?r.width:void 0,a=r.scale||4;return{width:i,scale:i?4:a,margin:n,color:{dark:t(r.color.dark||"#000000ff"),light:t(r.color.light||"#ffffffff")},type:r.type,rendererOpts:r.rendererOpts||{}}},e.getScale=function(r,n){return n.width&&n.width>=r+n.margin*2?n.width/(r+n.margin*2):n.scale},e.getImageWidth=function(r,n){const i=e.getScale(r,n);return Math.floor((r+n.margin*2)*i)},e.qrToImageData=function(r,n,i){const a=n.modules.size,s=n.modules.data,l=e.getScale(a,i),c=Math.floor((a+i.margin*2)*l),d=i.margin*l,T=[i.color.light,i.color.dark];for(let f=0;f<c;f++)for(let h=0;h<c;h++){let C=(f*c+h)*4,v=i.color.light;if(f>=d&&h>=d&&f<c-d&&h<c-d){const x=Math.floor((f-d)/l),m=Math.floor((h-d)/l);v=T[s[x*a+m]?1:0]}r[C++]=v.r,r[C++]=v.g,r[C++]=v.b,r[C]=v.a}}})),Ti=k((e=>{var t=Pt();function o(n,i,a){n.clearRect(0,0,i.width,i.height),i.style||(i.style={}),i.height=a,i.width=a,i.style.height=a+"px",i.style.width=a+"px"}function r(){try{return document.createElement("canvas")}catch{throw new Error("You need to specify a canvas element")}}e.render=function(i,a,s){let l=s,c=a;typeof l>"u"&&(!a||!a.getContext)&&(l=a,a=void 0),a||(c=r()),l=t.getOptions(l);const d=t.getImageWidth(i.modules.size,l),T=c.getContext("2d"),f=T.createImageData(d,d);return t.qrToImageData(f.data,i,l),o(T,c,d),T.putImageData(f,0,0),c},e.renderToDataURL=function(i,a,s){let l=s;typeof l>"u"&&(!a||!a.getContext)&&(l=a,a=void 0),l||(l={});const c=e.render(i,a,l),d=l.type||"image/png",T=l.rendererOpts||{};return c.toDataURL(d,T.quality)}})),Ai=k((e=>{var t=Pt();function o(i,a){const s=i.a/255,l=a+'="'+i.hex+'"';return s<1?l+" "+a+'-opacity="'+s.toFixed(2).slice(1)+'"':l}function r(i,a,s){let l=i+a;return typeof s<"u"&&(l+=" "+s),l}function n(i,a,s){let l="",c=0,d=!1,T=0;for(let f=0;f<i.length;f++){const h=Math.floor(f%a),C=Math.floor(f/a);!h&&!d&&(d=!0),i[f]?(T++,f>0&&h>0&&i[f-1]||(l+=d?r("M",h+s,.5+C+s):r("m",c,0),c=0,d=!1),h+1<a&&i[f+1]||(l+=r("h",T),T=0)):c++}return l}e.render=function(a,s,l){const c=t.getOptions(s),d=a.modules.size,T=a.modules.data,f=d+c.margin*2,h=c.color.light.a?"<path "+o(c.color.light,"fill")+' d="M0 0h'+f+"v"+f+'H0z"/>':"",C="<path "+o(c.color.dark,"stroke")+' d="'+n(T,d,c.margin)+'"/>',v='viewBox="0 0 '+f+" "+f+'"',x='<svg xmlns="http://www.w3.org/2000/svg" '+(c.width?'width="'+c.width+'" height="'+c.width+'" ':"")+v+' shape-rendering="crispEdges">'+h+C+`</svg>
`;return typeof l=="function"&&l(null,x),x}})),Ii=k((e=>{var t=ci(),o=Si(),r=Ti(),n=Ai();function i(a,s,l,c,d){const T=[].slice.call(arguments,1),f=T.length,h=typeof T[f-1]=="function";if(!h&&!t())throw new Error("Callback required as last argument");if(h){if(f<2)throw new Error("Too few arguments provided");f===2?(d=l,l=s,s=c=void 0):f===3&&(s.getContext&&typeof d>"u"?(d=c,c=void 0):(d=c,c=l,l=s,s=void 0))}else{if(f<1)throw new Error("Too few arguments provided");return f===1?(l=s,s=c=void 0):f===2&&!s.getContext&&(c=l,l=s,s=void 0),new Promise(function(C,v){try{C(a(o.create(l,c),s,c))}catch(x){v(x)}})}try{const C=o.create(l,c);d(null,a(C,s,c))}catch(C){d(C)}}e.create=o.create,e.toCanvas=i.bind(null,r.render),e.toDataURL=i.bind(null,r.renderToDataURL),e.toString=i.bind(null,function(a,s,l){return n.render(a,l)})})),Wi=zt(Ii(),1),Pi=.1,bt=2.5,de=7;function et(e,t,o){return e===t?!1:(e-t<0?t-e:e-t)<=o+Pi}function Bi(e,t){const o=Array.prototype.slice.call(Wi.create(e,{errorCorrectionLevel:t}).modules.data,0),r=Math.sqrt(o.length);return o.reduce((n,i,a)=>(a%r===0?n.push([i]):n[n.length-1].push(i))&&n,[])}var Li={generate({uri:e,size:t,logoSize:o,padding:r=8,dotColor:n="var(--apkt-colors-black)"}){const a=[],s=Bi(e,"Q"),l=(t-2*r)/s.length,c=[{x:0,y:0},{x:1,y:0},{x:0,y:1}];c.forEach(({x:v,y:x})=>{const m=(s.length-de)*l*v+r,g=(s.length-de)*l*x+r,$=.45;for(let p=0;p<c.length;p+=1){const B=l*(de-p*2);a.push(Me`
            <rect
              fill=${p===2?"var(--apkt-colors-black)":"var(--apkt-colors-white)"}
              width=${p===0?B-10:B}
              rx= ${p===0?(B-10)*$:B*$}
              ry= ${p===0?(B-10)*$:B*$}
              stroke=${n}
              stroke-width=${p===0?10:0}
              height=${p===0?B-10:B}
              x= ${p===0?g+l*p+10/2:g+l*p}
              y= ${p===0?m+l*p+10/2:m+l*p}
            />
          `)}});const d=Math.floor((o+25)/l),T=s.length/2-d/2,f=s.length/2+d/2-1,h=[];s.forEach((v,x)=>{v.forEach((m,g)=>{if(s[x][g]&&!(x<de&&g<de||x>s.length-8&&g<de||x<de&&g>s.length-8)&&!(x>T&&x<f&&g>T&&g<f)){const $=x*l+l/2+r,p=g*l+l/2+r;h.push([$,p])}})});const C={};return h.forEach(([v,x])=>{C[v]?C[v]?.push(x):C[v]=[x]}),Object.entries(C).map(([v,x])=>{const m=x.filter(g=>x.every($=>!et(g,$,l)));return[Number(v),m]}).forEach(([v,x])=>{x.forEach(m=>{a.push(Me`<circle cx=${v} cy=${m} fill=${n} r=${l/bt} />`)})}),Object.entries(C).filter(([v,x])=>x.length>1).map(([v,x])=>{const m=x.filter(g=>x.some($=>et(g,$,l)));return[Number(v),m]}).map(([v,x])=>{x.sort((g,$)=>g<$?-1:1);const m=[];for(const g of x){const $=m.find(p=>p.some(B=>et(g,B,l)));$?$.push(g):m.push([g])}return[v,m.map(g=>[g[0],g[g.length-1]])]}).forEach(([v,x])=>{x.forEach(([m,g])=>{a.push(Me`
              <line
                x1=${v}
                x2=${v}
                y1=${m}
                y2=${g}
                stroke=${n}
                stroke-width=${l/(bt/2)}
                stroke-linecap="round"
              />
            `)})}),a}},ki=q`
  :host {
    position: relative;
    user-select: none;
    display: block;
    overflow: hidden;
    aspect-ratio: 1 / 1;
    width: 100%;
    height: 100%;
    background-color: ${({colors:e})=>e.white};
    border: 1px solid ${({tokens:e})=>e.theme.borderPrimary};
  }

  :host {
    border-radius: ${({borderRadius:e})=>e[4]};
    display: flex;
    align-items: center;
    justify-content: center;
  }

  :host([data-clear='true']) > wui-icon {
    display: none;
  }

  svg:first-child,
  wui-image,
  wui-icon {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translateY(-50%) translateX(-50%);
    background-color: ${({tokens:e})=>e.theme.backgroundPrimary};
    box-shadow: inset 0 0 0 4px ${({tokens:e})=>e.theme.backgroundPrimary};
    border-radius: ${({borderRadius:e})=>e[6]};
  }

  wui-image {
    width: 25%;
    height: 25%;
    border-radius: ${({borderRadius:e})=>e[2]};
  }

  wui-icon {
    width: 100%;
    height: 100%;
    color: #3396ff !important;
    transform: translateY(-50%) translateX(-50%) scale(0.25);
  }

  wui-icon > svg {
    width: inherit;
    height: inherit;
  }
`,ue=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},te=class extends j{constructor(){super(...arguments),this.uri="",this.size=500,this.theme="dark",this.imageSrc=void 0,this.alt=void 0,this.arenaClear=void 0,this.farcaster=void 0}render(){return this.dataset.theme=this.theme,this.dataset.clear=String(this.arenaClear),u`<wui-flex
      alignItems="center"
      justifyContent="center"
      class="wui-qr-code"
      direction="column"
      gap="4"
      width="100%"
      style="height: 100%"
    >
      ${this.templateVisual()} ${this.templateSvg()}
    </wui-flex>`}templateSvg(){return Me`
      <svg viewBox="0 0 ${this.size} ${this.size}" width="100%" height="100%">
        ${Li.generate({uri:this.uri,size:this.size,logoSize:this.arenaClear?0:this.size/4})}
      </svg>
    `}templateVisual(){return this.imageSrc?u`<wui-image src=${this.imageSrc} alt=${this.alt??"logo"}></wui-image>`:this.farcaster?u`<wui-icon
        class="farcaster"
        size="inherit"
        color="inherit"
        name="farcaster"
      ></wui-icon>`:u`<wui-icon size="inherit" color="inherit" name="walletConnect"></wui-icon>`}};te.styles=[Z,ki];ue([w()],te.prototype,"uri",void 0);ue([w({type:Number})],te.prototype,"size",void 0);ue([w()],te.prototype,"theme",void 0);ue([w()],te.prototype,"imageSrc",void 0);ue([w()],te.prototype,"alt",void 0);ue([w({type:Boolean})],te.prototype,"arenaClear",void 0);ue([w({type:Boolean})],te.prototype,"farcaster",void 0);te=ue([N("wui-qr-code")],te);var Ni=q`
  wui-shimmer {
    width: 100%;
    aspect-ratio: 1 / 1;
    border-radius: ${({borderRadius:e})=>e[4]};
  }

  wui-qr-code {
    opacity: 0;
    animation-duration: ${({durations:e})=>e.xl};
    animation-timing-function: ${({easings:e})=>e["ease-out-power-2"]};
    animation-name: fade-in;
    animation-fill-mode: forwards;
  }

  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
`,Bt=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},ze=class extends F{constructor(){super(),this.basic=!1}firstUpdated(){this.basic||G.sendEvent({type:"track",event:"SELECT_WALLET",properties:{name:this.wallet?.name??"WalletConnect",platform:"qrcode",displayIndex:this.wallet?.display_index,walletRank:this.wallet?.order,view:P.state.view}})}disconnectedCallback(){super.disconnectedCallback(),this.unsubscribe?.forEach(t=>t())}render(){return this.onRenderProxy(),u`
      <wui-flex
        flexDirection="column"
        alignItems="center"
        .padding=${["0","5","5","5"]}
        gap="5"
      >
        <wui-shimmer width="100%"> ${this.qrCodeTemplate()} </wui-shimmer>
        <wui-text variant="lg-medium" color="primary"> Scan this QR Code with your phone </wui-text>
        ${this.copyTemplate()}
      </wui-flex>
      <w3m-mobile-download-links .wallet=${this.wallet}></w3m-mobile-download-links>
    `}onRenderProxy(){!this.ready&&this.uri&&(this.ready=!0)}qrCodeTemplate(){if(!this.uri||!this.ready)return null;const t=this.wallet?this.wallet.name:void 0;L.setWcLinking(void 0),L.setRecentWallet(this.wallet);const o=Ne.state.themeVariables["--apkt-qr-color"]??Ne.state.themeVariables["--w3m-qr-color"];return u` <wui-qr-code
      theme=${Ne.state.themeMode}
      uri=${this.uri}
      imageSrc=${D(le.getWalletImage(this.wallet))}
      color=${D(o)}
      alt=${D(t)}
      data-testid="wui-qr-code"
    ></wui-qr-code>`}copyTemplate(){return u`<wui-button
      .disabled=${!this.uri||!this.ready}
      @click=${this.onCopyUri}
      variant="neutral-secondary"
      size="sm"
      data-testid="copy-wc2-uri"
    >
      Copy link
      <wui-icon size="sm" color="inherit" name="copy" slot="iconRight"></wui-icon>
    </wui-button>`}};ze.styles=Ni;Bt([w({type:Boolean})],ze.prototype,"basic",void 0);ze=Bt([N("w3m-connecting-wc-qrcode")],ze);var Mi=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},vt=class extends j{constructor(){if(super(),this.wallet=P.state.data?.wallet,!this.wallet)throw new Error("w3m-connecting-wc-unsupported: No wallet provided");G.sendEvent({type:"track",event:"SELECT_WALLET",properties:{name:this.wallet.name,platform:"browser",displayIndex:this.wallet?.display_index,walletRank:this.wallet?.order,view:P.state.view}})}render(){return u`
      <wui-flex
        flexDirection="column"
        alignItems="center"
        .padding=${["10","5","5","5"]}
        gap="5"
      >
        <wui-wallet-image
          size="lg"
          imageSrc=${D(le.getWalletImage(this.wallet))}
        ></wui-wallet-image>

        <wui-text variant="md-regular" color="primary">Not Detected</wui-text>
      </wui-flex>

      <w3m-mobile-download-links .wallet=${this.wallet}></w3m-mobile-download-links>
    `}};vt=Mi([N("w3m-connecting-wc-unsupported")],vt);var Lt=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},rt=class extends F{constructor(){if(super(),this.isLoading=!0,!this.wallet)throw new Error("w3m-connecting-wc-web: No wallet provided");this.onConnect=this.onConnectProxy.bind(this),this.secondaryBtnLabel="Open",this.secondaryLabel=xt.CONNECT_LABELS.MOBILE,this.secondaryBtnIcon="externalLink",this.updateLoadingState(),this.unsubscribe.push(L.subscribeKey("wcUri",()=>{this.updateLoadingState()})),G.sendEvent({type:"track",event:"SELECT_WALLET",properties:{name:this.wallet.name,platform:"web",displayIndex:this.wallet?.display_index,walletRank:this.wallet?.order,view:P.state.view}})}updateLoadingState(){this.isLoading=!this.uri}onConnectProxy(){if(this.wallet?.webapp_link&&this.uri)try{this.error=!1;const{webapp_link:t,name:o}=this.wallet,{redirect:r,href:n}=M.formatUniversalUrl(t,this.uri);L.setWcLinking({name:o,href:n}),L.setRecentWallet(this.wallet),M.openHref(r,"_blank")}catch{this.error=!0}}};Lt([A()],rt.prototype,"isLoading",void 0);rt=Lt([N("w3m-connecting-wc-web")],rt);var Oi=q`
  :host([data-mobile-fullscreen='true']) {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  :host([data-mobile-fullscreen='true']) wui-ux-by-reown {
    margin-top: auto;
  }
`,$e=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},se=class extends j{constructor(){super(),this.wallet=P.state.data?.wallet,this.unsubscribe=[],this.platform=void 0,this.platforms=[],this.isSiwxEnabled=!!V.state.siwx,this.remoteFeatures=V.state.remoteFeatures,this.displayBranding=!0,this.basic=!1,this.determinePlatforms(),this.initializeConnection(),this.unsubscribe.push(V.subscribeKey("remoteFeatures",t=>this.remoteFeatures=t))}disconnectedCallback(){this.unsubscribe.forEach(t=>t())}render(){return V.state.enableMobileFullScreen&&this.setAttribute("data-mobile-fullscreen","true"),u`
      ${this.headerTemplate()}
      <div class="platform-container">${this.platformTemplate()}</div>
      ${this.reownBrandingTemplate()}
    `}reownBrandingTemplate(){return!this.remoteFeatures?.reownBranding||!this.displayBranding?null:u`<wui-ux-by-reown></wui-ux-by-reown>`}async initializeConnection(t=!1){if(!(this.platform==="browser"||V.state.manualWCControl&&!t))try{const{wcPairingExpiry:o,status:r}=L.state,{redirectView:n}=P.state.data??{};if(t||V.state.enableEmbedded||M.isPairingExpired(o)||r==="connecting"){const i=L.getConnections(oe.state.activeChain),a=this.remoteFeatures?.multiWallet,s=i.length>0;await L.connectWalletConnect({cache:"never"}),this.isSiwxEnabled||(s&&a?(P.replace("ProfileWallets"),Ie.showSuccess("New Wallet Added")):n?P.replace(n):Et.close())}}catch(o){if(o instanceof Error&&o.message.includes("An error occurred when attempting to switch chain")&&!V.state.enableNetworkSwitch&&oe.state.activeChain){oe.setActiveCaipNetwork(Yt.getUnsupportedNetwork(`${oe.state.activeChain}:${oe.state.activeCaipNetwork?.id}`)),oe.showUnsupportedChainUI();return}o instanceof Ct&&o.originalName===_t.PROVIDER_RPC_ERROR_NAME.USER_REJECTED_REQUEST?G.sendEvent({type:"track",event:"USER_REJECTED",properties:{message:o.message}}):G.sendEvent({type:"track",event:"CONNECT_ERROR",properties:{message:o?.message??"Unknown"}}),L.setWcError(!0),Ie.showError(o.message??"Connection error"),L.resetWcConnection(),P.goBack()}}determinePlatforms(){if(!this.wallet){this.platforms.push("qrcode"),this.platform="qrcode";return}if(this.platform)return;const{mobile_link:t,desktop_link:o,webapp_link:r,injected:n,rdns:i}=this.wallet,a=n?.map(({injected_id:C})=>C).filter(Boolean),s=[...i?[i]:a??[]],l=V.state.isUniversalProvider?!1:s.length,c=t,d=r,T=L.checkInstalled(s),f=l&&T,h=o&&!M.isMobile();f&&!oe.state.noAdapters&&this.platforms.push("browser"),c&&this.platforms.push(M.isMobile()?"mobile":"qrcode"),d&&this.platforms.push("web"),h&&this.platforms.push("desktop"),!f&&l&&!oe.state.noAdapters&&this.platforms.push("unsupported"),this.platform=this.platforms[0]}platformTemplate(){switch(this.platform){case"browser":return u`<w3m-connecting-wc-browser></w3m-connecting-wc-browser>`;case"web":return u`<w3m-connecting-wc-web></w3m-connecting-wc-web>`;case"desktop":return u`
          <w3m-connecting-wc-desktop .onRetry=${()=>this.initializeConnection(!0)}>
          </w3m-connecting-wc-desktop>
        `;case"mobile":return u`
          <w3m-connecting-wc-mobile isMobile .onRetry=${()=>this.initializeConnection(!0)}>
          </w3m-connecting-wc-mobile>
        `;case"qrcode":return u`<w3m-connecting-wc-qrcode ?basic=${this.basic}></w3m-connecting-wc-qrcode>`;default:return u`<w3m-connecting-wc-unsupported></w3m-connecting-wc-unsupported>`}}headerTemplate(){return this.platforms.length>1?u`
      <w3m-connecting-header
        .platforms=${this.platforms}
        .onSelectPlatfrom=${this.onSelectPlatform.bind(this)}
      >
      </w3m-connecting-header>
    `:null}async onSelectPlatform(t){const o=this.shadowRoot?.querySelector("div");o&&(await o.animate([{opacity:1},{opacity:0}],{duration:200,fill:"forwards",easing:"ease"}).finished,this.platform=t,o.animate([{opacity:0},{opacity:1}],{duration:200,fill:"forwards",easing:"ease"}))}};se.styles=Oi;$e([A()],se.prototype,"platform",void 0);$e([A()],se.prototype,"platforms",void 0);$e([A()],se.prototype,"isSiwxEnabled",void 0);$e([A()],se.prototype,"remoteFeatures",void 0);$e([w({type:Boolean})],se.prototype,"displayBranding",void 0);$e([w({type:Boolean})],se.prototype,"basic",void 0);se=$e([N("w3m-connecting-wc-view")],se);var st=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},Ue=class extends j{constructor(){super(),this.unsubscribe=[],this.isMobile=M.isMobile(),this.remoteFeatures=V.state.remoteFeatures,this.unsubscribe.push(V.subscribeKey("remoteFeatures",t=>this.remoteFeatures=t))}disconnectedCallback(){this.unsubscribe.forEach(t=>t())}render(){if(this.isMobile){const{featured:t,recommended:o}=z.state,{customWallets:r}=V.state,n=Ut.getRecentWallets();return u`<wui-flex flexDirection="column" gap="2" .margin=${["1","3","3","3"]}>
        ${t.length||o.length||r?.length||n.length?u`<w3m-connector-list></w3m-connector-list>`:null}
        <w3m-all-wallets-widget></w3m-all-wallets-widget>
      </wui-flex>`}return u`<wui-flex flexDirection="column" .padding=${["0","0","4","0"]}>
        <w3m-connecting-wc-view ?basic=${!0} .displayBranding=${!1}></w3m-connecting-wc-view>
        <wui-flex flexDirection="column" .padding=${["0","3","0","3"]}>
          <w3m-all-wallets-widget></w3m-all-wallets-widget>
        </wui-flex>
      </wui-flex>
      ${this.reownBrandingTemplate()} `}reownBrandingTemplate(){return this.remoteFeatures?.reownBranding?u` <wui-flex flexDirection="column" .padding=${["1","0","1","0"]}>
      <wui-ux-by-reown></wui-ux-by-reown>
    </wui-flex>`:null}};st([A()],Ue.prototype,"isMobile",void 0);st([A()],Ue.prototype,"remoteFeatures",void 0);Ue=st([N("w3m-connecting-wc-basic-view")],Ue);var{I:xn}=Ht;var ji=e=>e.strings===void 0;var Ae=(e,t)=>{const o=e._$AN;if(o===void 0)return!1;for(const r of o)r._$AO?.(t,!1),Ae(r,t);return!0},qe=e=>{let t,o;do{if((t=e._$AM)===void 0)break;o=t._$AN,o.delete(e),e=t}while(o?.size===0)},kt=e=>{for(let t;t=e._$AM;e=t){let o=t._$AN;if(o===void 0)t._$AN=o=new Set;else if(o.has(e))break;o.add(e),Ui(t)}};function Di(e){this._$AN!==void 0?(qe(this),this._$AM=e,kt(this)):this._$AM=e}function zi(e,t=!1,o=0){const r=this._$AH,n=this._$AN;if(n!==void 0&&n.size!==0)if(t)if(Array.isArray(r))for(let i=o;i<r.length;i++)Ae(r[i],!1),qe(r[i]);else r!=null&&(Ae(r,!1),qe(r));else Ae(this,e)}var Ui=e=>{e.type==Kt.CHILD&&(e._$AP??=zi,e._$AQ??=Di)},qi=class extends Gt{constructor(){super(...arguments),this._$AN=void 0}_$AT(e,t,o){super._$AT(e,t,o),kt(this),this.isConnected=e._$AU}_$AO(e,t=!0){e!==this.isConnected&&(this.isConnected=e,e?this.reconnected?.():this.disconnected?.()),t&&(Ae(this,e),qe(this))}setValue(e){if(ji(this._$Ct))this._$Ct._$AI(e,this);else{const t=[...this._$Ct._$AH];t[this._$Ci]=e,this._$Ct._$AI(t,this,0)}}disconnected(){}reconnected(){}},lt=()=>new Fi,Fi=class{},tt=new WeakMap,ct=Jt(class extends qi{render(e){return gt}update(e,[t]){const o=t!==this.G;return o&&this.rt(void 0),(o||this.lt!==this.ct)&&(this.G=t,this.ht=e.options?.host,this.rt(this.ct=e.element)),gt}rt(e){if(this.G!==void 0)if(this.isConnected||(e=void 0),typeof this.G=="function"){const t=this.ht??globalThis;let o=tt.get(t);o===void 0&&(o=new WeakMap,tt.set(t,o)),o.get(this.G)!==void 0&&this.G.call(this.ht,void 0),o.set(this.G,e),e!==void 0&&this.G.call(this.ht,e)}else this.G.value=e}get lt(){return typeof this.G=="function"?tt.get(this.ht??globalThis)?.get(this.G):this.G?.value}disconnected(){this.lt===this.ct&&this.rt(void 0)}reconnected(){this.rt(this.ct)}}),Vi=q`
  :host {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  label {
    position: relative;
    display: inline-block;
    user-select: none;
    transition:
      background-color ${({durations:e})=>e.lg}
        ${({easings:e})=>e["ease-out-power-2"]},
      color ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-2"]},
      border ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-2"]},
      box-shadow ${({durations:e})=>e.lg}
        ${({easings:e})=>e["ease-out-power-2"]},
      width ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-2"]},
      height ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-2"]},
      transform ${({durations:e})=>e.lg}
        ${({easings:e})=>e["ease-out-power-2"]},
      opacity ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-2"]};
    will-change: background-color, color, border, box-shadow, width, height, transform, opacity;
  }

  input {
    width: 0;
    height: 0;
    opacity: 0;
  }

  span {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: ${({colors:e})=>e.neutrals300};
    border-radius: ${({borderRadius:e})=>e.round};
    border: 1px solid transparent;
    will-change: border;
    transition:
      background-color ${({durations:e})=>e.lg}
        ${({easings:e})=>e["ease-out-power-2"]},
      color ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-2"]},
      border ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-2"]},
      box-shadow ${({durations:e})=>e.lg}
        ${({easings:e})=>e["ease-out-power-2"]},
      width ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-2"]},
      height ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-2"]},
      transform ${({durations:e})=>e.lg}
        ${({easings:e})=>e["ease-out-power-2"]},
      opacity ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-2"]};
    will-change: background-color, color, border, box-shadow, width, height, transform, opacity;
  }

  span:before {
    content: '';
    position: absolute;
    background-color: ${({colors:e})=>e.white};
    border-radius: 50%;
  }

  /* -- Sizes --------------------------------------------------------- */
  label[data-size='lg'] {
    width: 48px;
    height: 32px;
  }

  label[data-size='md'] {
    width: 40px;
    height: 28px;
  }

  label[data-size='sm'] {
    width: 32px;
    height: 22px;
  }

  label[data-size='lg'] > span:before {
    height: 24px;
    width: 24px;
    left: 4px;
    top: 3px;
  }

  label[data-size='md'] > span:before {
    height: 20px;
    width: 20px;
    left: 4px;
    top: 3px;
  }

  label[data-size='sm'] > span:before {
    height: 16px;
    width: 16px;
    left: 3px;
    top: 2px;
  }

  /* -- Focus states --------------------------------------------------- */
  input:focus-visible:not(:checked) + span,
  input:focus:not(:checked) + span {
    border: 1px solid ${({tokens:e})=>e.core.iconAccentPrimary};
    background-color: ${({tokens:e})=>e.theme.textTertiary};
    box-shadow: 0px 0px 0px 4px rgba(9, 136, 240, 0.2);
  }

  input:focus-visible:checked + span,
  input:focus:checked + span {
    border: 1px solid ${({tokens:e})=>e.core.iconAccentPrimary};
    box-shadow: 0px 0px 0px 4px rgba(9, 136, 240, 0.2);
  }

  /* -- Checked states --------------------------------------------------- */
  input:checked + span {
    background-color: ${({tokens:e})=>e.core.iconAccentPrimary};
  }

  label[data-size='lg'] > input:checked + span:before {
    transform: translateX(calc(100% - 9px));
  }

  label[data-size='md'] > input:checked + span:before {
    transform: translateX(calc(100% - 9px));
  }

  label[data-size='sm'] > input:checked + span:before {
    transform: translateX(calc(100% - 7px));
  }

  /* -- Hover states ------------------------------------------------------- */
  label:hover > input:not(:checked):not(:disabled) + span {
    background-color: ${({colors:e})=>e.neutrals400};
  }

  label:hover > input:checked:not(:disabled) + span {
    background-color: ${({colors:e})=>e.accent080};
  }

  /* -- Disabled state --------------------------------------------------- */
  label:has(input:disabled) {
    pointer-events: none;
    user-select: none;
  }

  input:not(:checked):disabled + span {
    background-color: ${({colors:e})=>e.neutrals700};
  }

  input:checked:disabled + span {
    background-color: ${({colors:e})=>e.neutrals700};
  }

  input:not(:checked):disabled + span::before {
    background-color: ${({colors:e})=>e.neutrals400};
  }

  input:checked:disabled + span::before {
    background-color: ${({tokens:e})=>e.theme.textTertiary};
  }
`,Je=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},Ee=class extends j{constructor(){super(...arguments),this.inputElementRef=lt(),this.checked=!1,this.disabled=!1,this.size="md"}render(){return u`
      <label data-size=${this.size}>
        <input
          ${ct(this.inputElementRef)}
          type="checkbox"
          ?checked=${this.checked}
          ?disabled=${this.disabled}
          @change=${this.dispatchChangeEvent.bind(this)}
        />
        <span></span>
      </label>
    `}dispatchChangeEvent(){this.dispatchEvent(new CustomEvent("switchChange",{detail:this.inputElementRef.value?.checked,bubbles:!0,composed:!0}))}};Ee.styles=[Z,be,Vi];Je([w({type:Boolean})],Ee.prototype,"checked",void 0);Je([w({type:Boolean})],Ee.prototype,"disabled",void 0);Je([w()],Ee.prototype,"size",void 0);Ee=Je([N("wui-toggle")],Ee);var Hi=q`
  :host {
    height: auto;
  }

  :host > wui-flex {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    column-gap: ${({spacing:e})=>e[2]};
    padding: ${({spacing:e})=>e[2]} ${({spacing:e})=>e[3]};
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    border-radius: ${({borderRadius:e})=>e[4]};
    box-shadow: inset 0 0 0 1px ${({tokens:e})=>e.theme.foregroundPrimary};
    transition: background-color ${({durations:e})=>e.lg}
      ${({easings:e})=>e["ease-out-power-2"]};
    will-change: background-color;
    cursor: pointer;
  }

  wui-switch {
    pointer-events: none;
  }
`,Nt=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},Fe=class extends j{constructor(){super(...arguments),this.checked=!1}render(){return u`
      <wui-flex>
        <wui-icon size="xl" name="walletConnectBrown"></wui-icon>
        <wui-toggle
          ?checked=${this.checked}
          size="sm"
          @switchChange=${this.handleToggleChange.bind(this)}
        ></wui-toggle>
      </wui-flex>
    `}handleToggleChange(t){t.stopPropagation(),this.checked=t.detail,this.dispatchSwitchEvent()}dispatchSwitchEvent(){this.dispatchEvent(new CustomEvent("certifiedSwitchChange",{detail:this.checked,bubbles:!0,composed:!0}))}};Fe.styles=[Z,be,Hi];Nt([w({type:Boolean})],Fe.prototype,"checked",void 0);Fe=Nt([N("wui-certified-switch")],Fe);var Ki=q`
  :host {
    position: relative;
    width: 100%;
    display: inline-flex;
    flex-direction: column;
    gap: ${({spacing:e})=>e[3]};
    color: ${({tokens:e})=>e.theme.textPrimary};
    caret-color: ${({tokens:e})=>e.core.textAccentPrimary};
  }

  .wui-input-text-container {
    position: relative;
    display: flex;
  }

  input {
    width: 100%;
    border-radius: ${({borderRadius:e})=>e[4]};
    color: inherit;
    background: transparent;
    border: 1px solid ${({tokens:e})=>e.theme.borderPrimary};
    caret-color: ${({tokens:e})=>e.core.textAccentPrimary};
    padding: ${({spacing:e})=>e[3]} ${({spacing:e})=>e[3]}
      ${({spacing:e})=>e[3]} ${({spacing:e})=>e[10]};
    font-size: ${({textSize:e})=>e.large};
    line-height: ${({typography:e})=>e["lg-regular"].lineHeight};
    letter-spacing: ${({typography:e})=>e["lg-regular"].letterSpacing};
    font-weight: ${({fontWeight:e})=>e.regular};
    font-family: ${({fontFamily:e})=>e.regular};
  }

  input[data-size='lg'] {
    padding: ${({spacing:e})=>e[4]} ${({spacing:e})=>e[3]}
      ${({spacing:e})=>e[4]} ${({spacing:e})=>e[10]};
  }

  @media (hover: hover) and (pointer: fine) {
    input:hover:enabled {
      border: 1px solid ${({tokens:e})=>e.theme.borderSecondary};
    }
  }

  input:disabled {
    cursor: unset;
    border: 1px solid ${({tokens:e})=>e.theme.borderPrimary};
  }

  input::placeholder {
    color: ${({tokens:e})=>e.theme.textSecondary};
  }

  input:focus:enabled {
    border: 1px solid ${({tokens:e})=>e.theme.borderSecondary};
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    -webkit-box-shadow: 0px 0px 0px 4px ${({tokens:e})=>e.core.foregroundAccent040};
    -moz-box-shadow: 0px 0px 0px 4px ${({tokens:e})=>e.core.foregroundAccent040};
    box-shadow: 0px 0px 0px 4px ${({tokens:e})=>e.core.foregroundAccent040};
  }

  div.wui-input-text-container:has(input:disabled) {
    opacity: 0.5;
  }

  wui-icon.wui-input-text-left-icon {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    pointer-events: none;
    left: ${({spacing:e})=>e[4]};
    color: ${({tokens:e})=>e.theme.iconDefault};
  }

  button.wui-input-text-submit-button {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    right: ${({spacing:e})=>e[3]};
    width: 24px;
    height: 24px;
    border: none;
    background: transparent;
    border-radius: ${({borderRadius:e})=>e[2]};
    color: ${({tokens:e})=>e.core.textAccentPrimary};
  }

  button.wui-input-text-submit-button:disabled {
    opacity: 1;
  }

  button.wui-input-text-submit-button.loading wui-icon {
    animation: spin 1s linear infinite;
  }

  button.wui-input-text-submit-button:hover {
    background: ${({tokens:e})=>e.core.foregroundAccent010};
  }

  input:has(+ .wui-input-text-submit-button) {
    padding-right: ${({spacing:e})=>e[12]};
  }

  input[type='number'] {
    -moz-appearance: textfield;
  }

  input[type='search']::-webkit-search-decoration,
  input[type='search']::-webkit-search-cancel-button,
  input[type='search']::-webkit-search-results-button,
  input[type='search']::-webkit-search-results-decoration {
    -webkit-appearance: none;
  }

  /* -- Keyframes --------------------------------------------------- */
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
`,Q=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},H=class extends j{constructor(){super(...arguments),this.inputElementRef=lt(),this.disabled=!1,this.loading=!1,this.placeholder="",this.type="text",this.value="",this.size="md"}render(){return u` <div class="wui-input-text-container">
        ${this.templateLeftIcon()}
        <input
          data-size=${this.size}
          ${ct(this.inputElementRef)}
          data-testid="wui-input-text"
          type=${this.type}
          enterkeyhint=${D(this.enterKeyHint)}
          ?disabled=${this.disabled}
          placeholder=${this.placeholder}
          @input=${this.dispatchInputChangeEvent.bind(this)}
          @keydown=${this.onKeyDown}
          .value=${this.value||""}
        />
        ${this.templateSubmitButton()}
        <slot class="wui-input-text-slot"></slot>
      </div>
      ${this.templateError()} ${this.templateWarning()}`}templateLeftIcon(){return this.icon?u`<wui-icon
        class="wui-input-text-left-icon"
        size="md"
        data-size=${this.size}
        color="inherit"
        name=${this.icon}
      ></wui-icon>`:null}templateSubmitButton(){return this.onSubmit?u`<button
        class="wui-input-text-submit-button ${this.loading?"loading":""}"
        @click=${this.onSubmit?.bind(this)}
        ?disabled=${this.disabled||this.loading}
      >
        ${this.loading?u`<wui-icon name="spinner" size="md"></wui-icon>`:u`<wui-icon name="chevronRight" size="md"></wui-icon>`}
      </button>`:null}templateError(){return this.errorText?u`<wui-text variant="sm-regular" color="error">${this.errorText}</wui-text>`:null}templateWarning(){return this.warningText?u`<wui-text variant="sm-regular" color="warning">${this.warningText}</wui-text>`:null}dispatchInputChangeEvent(){this.dispatchEvent(new CustomEvent("inputChange",{detail:this.inputElementRef.value?.value,bubbles:!0,composed:!0}))}};H.styles=[Z,be,Ki];Q([w()],H.prototype,"icon",void 0);Q([w({type:Boolean})],H.prototype,"disabled",void 0);Q([w({type:Boolean})],H.prototype,"loading",void 0);Q([w()],H.prototype,"placeholder",void 0);Q([w()],H.prototype,"type",void 0);Q([w()],H.prototype,"value",void 0);Q([w()],H.prototype,"errorText",void 0);Q([w()],H.prototype,"warningText",void 0);Q([w()],H.prototype,"onSubmit",void 0);Q([w()],H.prototype,"size",void 0);Q([w({attribute:!1})],H.prototype,"onKeyDown",void 0);H=Q([N("wui-input-text")],H);var Gi=q`
  :host {
    position: relative;
    display: inline-block;
    width: 100%;
  }

  wui-icon {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    right: ${({spacing:e})=>e[3]};
    color: ${({tokens:e})=>e.theme.iconDefault};
    cursor: pointer;
    padding: ${({spacing:e})=>e[2]};
    background-color: transparent;
    border-radius: ${({borderRadius:e})=>e[4]};
    transition: background-color ${({durations:e})=>e.lg}
      ${({easings:e})=>e["ease-out-power-2"]};
  }

  @media (hover: hover) {
    wui-icon:hover {
      background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
    }
  }
`,Mt=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},Ve=class extends j{constructor(){super(...arguments),this.inputComponentRef=lt(),this.inputValue=""}render(){return u`
      <wui-input-text
        ${ct(this.inputComponentRef)}
        placeholder="Search wallet"
        icon="search"
        type="search"
        enterKeyHint="search"
        size="sm"
        @inputChange=${this.onInputChange}
      >
        ${this.inputValue?u`<wui-icon
              @click=${this.clearValue}
              color="inherit"
              size="sm"
              name="close"
            ></wui-icon>`:null}
      </wui-input-text>
    `}onInputChange(t){this.inputValue=t.detail||""}clearValue(){const t=this.inputComponentRef.value?.inputElementRef.value;t&&(t.value="",this.inputValue="",t.focus(),t.dispatchEvent(new Event("input")))}};Ve.styles=[Z,Gi];Mt([w()],Ve.prototype,"inputValue",void 0);Ve=Mt([N("wui-search-bar")],Ve);var Ji=q`
  :host {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 104px;
    width: 104px;
    row-gap: ${({spacing:e})=>e[2]};
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    border-radius: ${({borderRadius:e})=>e[5]};
    position: relative;
  }

  wui-shimmer[data-type='network'] {
    border: none;
    -webkit-clip-path: var(--apkt-path-network);
    clip-path: var(--apkt-path-network);
  }

  svg {
    position: absolute;
    width: 48px;
    height: 54px;
    z-index: 1;
  }

  svg > path {
    stroke: ${({tokens:e})=>e.theme.foregroundSecondary};
    stroke-width: 1px;
  }

  @media (max-width: 350px) {
    :host {
      width: 100%;
    }
  }
`,Ot=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},He=class extends j{constructor(){super(...arguments),this.type="wallet"}render(){return u`
      ${this.shimmerTemplate()}
      <wui-shimmer width="80px" height="20px"></wui-shimmer>
    `}shimmerTemplate(){return this.type==="network"?u` <wui-shimmer data-type=${this.type} width="48px" height="54px"></wui-shimmer>
        ${Qt}`:u`<wui-shimmer width="56px" height="56px"></wui-shimmer>`}};He.styles=[Z,be,Ji];Ot([w()],He.prototype,"type",void 0);He=Ot([N("wui-card-select-loader")],He);var Qi=Rt`
  :host {
    display: grid;
    width: inherit;
    height: inherit;
  }
`,Y=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},K=class extends j{render(){return this.style.cssText=`
      grid-template-rows: ${this.gridTemplateRows};
      grid-template-columns: ${this.gridTemplateColumns};
      justify-items: ${this.justifyItems};
      align-items: ${this.alignItems};
      justify-content: ${this.justifyContent};
      align-content: ${this.alignContent};
      column-gap: ${this.columnGap&&`var(--apkt-spacing-${this.columnGap})`};
      row-gap: ${this.rowGap&&`var(--apkt-spacing-${this.rowGap})`};
      gap: ${this.gap&&`var(--apkt-spacing-${this.gap})`};
      padding-top: ${this.padding&&ae.getSpacingStyles(this.padding,0)};
      padding-right: ${this.padding&&ae.getSpacingStyles(this.padding,1)};
      padding-bottom: ${this.padding&&ae.getSpacingStyles(this.padding,2)};
      padding-left: ${this.padding&&ae.getSpacingStyles(this.padding,3)};
      margin-top: ${this.margin&&ae.getSpacingStyles(this.margin,0)};
      margin-right: ${this.margin&&ae.getSpacingStyles(this.margin,1)};
      margin-bottom: ${this.margin&&ae.getSpacingStyles(this.margin,2)};
      margin-left: ${this.margin&&ae.getSpacingStyles(this.margin,3)};
    `,u`<slot></slot>`}};K.styles=[Z,Qi];Y([w()],K.prototype,"gridTemplateRows",void 0);Y([w()],K.prototype,"gridTemplateColumns",void 0);Y([w()],K.prototype,"justifyItems",void 0);Y([w()],K.prototype,"alignItems",void 0);Y([w()],K.prototype,"justifyContent",void 0);Y([w()],K.prototype,"alignContent",void 0);Y([w()],K.prototype,"columnGap",void 0);Y([w()],K.prototype,"rowGap",void 0);Y([w()],K.prototype,"gap",void 0);Y([w()],K.prototype,"padding",void 0);Y([w()],K.prototype,"margin",void 0);K=Y([N("wui-grid")],K);var Yi=q`
  button {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    cursor: pointer;
    width: 104px;
    row-gap: ${({spacing:e})=>e[2]};
    padding: ${({spacing:e})=>e[3]} ${({spacing:e})=>e[0]};
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    border-radius: clamp(0px, ${({borderRadius:e})=>e[4]}, 20px);
    transition:
      color ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-1"]},
      background-color ${({durations:e})=>e.lg}
        ${({easings:e})=>e["ease-out-power-1"]},
      border-radius ${({durations:e})=>e.lg}
        ${({easings:e})=>e["ease-out-power-1"]};
    will-change: background-color, color, border-radius;
    outline: none;
    border: none;
  }

  button > wui-flex > wui-text {
    color: ${({tokens:e})=>e.theme.textPrimary};
    max-width: 86px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    justify-content: center;
  }

  button > wui-flex > wui-text.certified {
    max-width: 66px;
  }

  @media (hover: hover) and (pointer: fine) {
    button:hover:enabled {
      background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
    }
  }

  button:disabled > wui-flex > wui-text {
    color: ${({tokens:e})=>e.core.glass010};
  }

  [data-selected='true'] {
    background-color: ${({colors:e})=>e.accent020};
  }

  @media (hover: hover) and (pointer: fine) {
    [data-selected='true']:hover:enabled {
      background-color: ${({colors:e})=>e.accent010};
    }
  }

  [data-selected='true']:active:enabled {
    background-color: ${({colors:e})=>e.accent010};
  }

  @media (max-width: 350px) {
    button {
      width: 100%;
    }
  }
`,ie=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},J=class extends j{constructor(){super(),this.observer=new IntersectionObserver(()=>{}),this.visible=!1,this.imageSrc=void 0,this.imageLoading=!1,this.isImpressed=!1,this.explorerId="",this.walletQuery="",this.certified=!1,this.displayIndex=0,this.wallet=void 0,this.observer=new IntersectionObserver(t=>{t.forEach(o=>{o.isIntersecting?(this.visible=!0,this.fetchImageSrc(),this.sendImpressionEvent()):this.visible=!1})},{threshold:.01})}firstUpdated(){this.observer.observe(this)}disconnectedCallback(){this.observer.disconnect()}render(){const t=this.wallet?.badge_type==="certified";return u`
      <button>
        ${this.imageTemplate()}
        <wui-flex flexDirection="row" alignItems="center" justifyContent="center" gap="1">
          <wui-text
            variant="md-regular"
            color="inherit"
            class=${D(t?"certified":void 0)}
            >${this.wallet?.name}</wui-text
          >
          ${t?u`<wui-icon size="sm" name="walletConnectBrown"></wui-icon>`:null}
        </wui-flex>
      </button>
    `}imageTemplate(){return!this.visible&&!this.imageSrc||this.imageLoading?this.shimmerTemplate():u`
      <wui-wallet-image
        size="lg"
        imageSrc=${D(this.imageSrc)}
        name=${D(this.wallet?.name)}
        .installed=${this.wallet?.installed??!1}
        badgeSize="sm"
      >
      </wui-wallet-image>
    `}shimmerTemplate(){return u`<wui-shimmer width="56px" height="56px"></wui-shimmer>`}async fetchImageSrc(){this.wallet&&(this.imageSrc=le.getWalletImage(this.wallet),!this.imageSrc&&(this.imageLoading=!0,this.imageSrc=await le.fetchWalletImage(this.wallet.image_id),this.imageLoading=!1))}sendImpressionEvent(){!this.wallet||this.isImpressed||(this.isImpressed=!0,G.sendWalletImpressionEvent({name:this.wallet.name,walletRank:this.wallet.order,explorerId:this.explorerId,view:P.state.view,query:this.walletQuery,certified:this.certified,displayIndex:this.displayIndex}))}};J.styles=Yi;ie([A()],J.prototype,"visible",void 0);ie([A()],J.prototype,"imageSrc",void 0);ie([A()],J.prototype,"imageLoading",void 0);ie([A()],J.prototype,"isImpressed",void 0);ie([w()],J.prototype,"explorerId",void 0);ie([w()],J.prototype,"walletQuery",void 0);ie([w()],J.prototype,"certified",void 0);ie([w()],J.prototype,"displayIndex",void 0);ie([w({type:Object})],J.prototype,"wallet",void 0);J=ie([N("w3m-all-wallets-list-item")],J);var Xi=q`
  wui-grid {
    max-height: clamp(360px, 400px, 80vh);
    overflow: scroll;
    scrollbar-width: none;
    grid-auto-rows: min-content;
    grid-template-columns: repeat(auto-fill, 104px);
  }

  :host([data-mobile-fullscreen='true']) wui-grid {
    max-height: none;
  }

  @media (max-width: 350px) {
    wui-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  wui-grid[data-scroll='false'] {
    overflow: hidden;
  }

  wui-grid::-webkit-scrollbar {
    display: none;
  }

  w3m-all-wallets-list-item {
    opacity: 0;
    animation-duration: ${({durations:e})=>e.xl};
    animation-timing-function: ${({easings:e})=>e["ease-inout-power-2"]};
    animation-name: fade-in;
    animation-fill-mode: forwards;
  }

  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  wui-loading-spinner {
    padding-top: ${({spacing:e})=>e[4]};
    padding-bottom: ${({spacing:e})=>e[4]};
    justify-content: center;
    grid-column: 1 / span 4;
  }
`,Be=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},yt="local-paginator",we=class extends j{constructor(){super(),this.unsubscribe=[],this.paginationObserver=void 0,this.loading=!z.state.wallets.length,this.wallets=z.state.wallets,this.mobileFullScreen=V.state.enableMobileFullScreen,this.unsubscribe.push(z.subscribeKey("wallets",t=>this.wallets=t))}firstUpdated(){this.initialFetch(),this.createPaginationObserver()}disconnectedCallback(){this.unsubscribe.forEach(t=>t()),this.paginationObserver?.disconnect()}render(){return this.mobileFullScreen&&this.setAttribute("data-mobile-fullscreen","true"),u`
      <wui-grid
        data-scroll=${!this.loading}
        .padding=${["0","3","3","3"]}
        gap="2"
        justifyContent="space-between"
      >
        ${this.loading?this.shimmerTemplate(16):this.walletsTemplate()}
        ${this.paginationLoaderTemplate()}
      </wui-grid>
    `}async initialFetch(){this.loading=!0;const t=this.shadowRoot?.querySelector("wui-grid");t&&(await z.fetchWalletsByPage({page:1}),await t.animate([{opacity:1},{opacity:0}],{duration:200,fill:"forwards",easing:"ease"}).finished,this.loading=!1,t.animate([{opacity:0},{opacity:1}],{duration:200,fill:"forwards",easing:"ease"}))}shimmerTemplate(t,o){return[...Array(t)].map(()=>u`
        <wui-card-select-loader type="wallet" id=${D(o)}></wui-card-select-loader>
      `)}walletsTemplate(){return nt.getWalletConnectWallets(this.wallets).map((t,o)=>u`
        <w3m-all-wallets-list-item
          data-testid="wallet-search-item-${t.id}"
          @click=${()=>this.onConnectWallet(t)}
          .wallet=${t}
          explorerId=${t.id}
          certified=${this.badge==="certified"}
          displayIndex=${o}
        ></w3m-all-wallets-list-item>
      `)}paginationLoaderTemplate(){const{wallets:t,recommended:o,featured:r,count:n,mobileFilteredOutWalletsLength:i}=z.state,a=window.innerWidth<352?3:4,s=t.length+o.length;let l=Math.ceil(s/a)*a-s+a;return l-=t.length?r.length%a:0,n===0&&r.length>0?null:n===0||[...r,...t,...o].length<n-(i??0)?this.shimmerTemplate(l,yt):null}createPaginationObserver(){const t=this.shadowRoot?.querySelector(`#${yt}`);t&&(this.paginationObserver=new IntersectionObserver(([o])=>{if(o?.isIntersecting&&!this.loading){const{page:r,count:n,wallets:i}=z.state;i.length<n&&z.fetchWalletsByPage({page:r+1})}}),this.paginationObserver.observe(t))}onConnectWallet(t){X.selectWalletConnector(t)}};we.styles=Xi;Be([A()],we.prototype,"loading",void 0);Be([A()],we.prototype,"wallets",void 0);Be([A()],we.prototype,"badge",void 0);Be([A()],we.prototype,"mobileFullScreen",void 0);we=Be([N("w3m-all-wallets-list")],we);var Zi=Rt`
  wui-grid,
  wui-loading-spinner,
  wui-flex {
    height: 360px;
  }

  wui-grid {
    overflow: scroll;
    scrollbar-width: none;
    grid-auto-rows: min-content;
    grid-template-columns: repeat(auto-fill, 104px);
  }

  :host([data-mobile-fullscreen='true']) wui-grid {
    max-height: none;
    height: auto;
  }

  wui-grid[data-scroll='false'] {
    overflow: hidden;
  }

  wui-grid::-webkit-scrollbar {
    display: none;
  }

  wui-loading-spinner {
    justify-content: center;
    align-items: center;
  }

  @media (max-width: 350px) {
    wui-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
`,Le=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},me=class extends j{constructor(){super(...arguments),this.prevQuery="",this.prevBadge=void 0,this.loading=!0,this.mobileFullScreen=V.state.enableMobileFullScreen,this.query=""}render(){return this.mobileFullScreen&&this.setAttribute("data-mobile-fullscreen","true"),this.onSearch(),this.loading?u`<wui-loading-spinner color="accent-primary"></wui-loading-spinner>`:this.walletsTemplate()}async onSearch(){(this.query.trim()!==this.prevQuery.trim()||this.badge!==this.prevBadge)&&(this.prevQuery=this.query,this.prevBadge=this.badge,this.loading=!0,await z.searchWallet({search:this.query,badge:this.badge}),this.loading=!1)}walletsTemplate(){const{search:t}=z.state,o=nt.markWalletsAsInstalled(t),r=nt.filterWalletsByWcSupport(o);return r.length?u`
      <wui-grid
        data-testid="wallet-list"
        .padding=${["0","3","3","3"]}
        rowGap="4"
        columngap="2"
        justifyContent="space-between"
      >
        ${r.map((n,i)=>u`
            <w3m-all-wallets-list-item
              @click=${()=>this.onConnectWallet(n)}
              .wallet=${n}
              data-testid="wallet-search-item-${n.id}"
              explorerId=${n.id}
              certified=${this.badge==="certified"}
              walletQuery=${this.query}
              displayIndex=${i}
            ></w3m-all-wallets-list-item>
          `)}
      </wui-grid>
    `:u`
        <wui-flex
          data-testid="no-wallet-found"
          justifyContent="center"
          alignItems="center"
          gap="3"
          flexDirection="column"
        >
          <wui-icon-box size="lg" color="default" icon="wallet"></wui-icon-box>
          <wui-text data-testid="no-wallet-found-text" color="secondary" variant="md-medium">
            No Wallet found
          </wui-text>
        </wui-flex>
      `}onConnectWallet(t){X.selectWalletConnector(t)}};me.styles=Zi;Le([A()],me.prototype,"loading",void 0);Le([A()],me.prototype,"mobileFullScreen",void 0);Le([w()],me.prototype,"query",void 0);Le([w()],me.prototype,"badge",void 0);me=Le([N("w3m-all-wallets-search")],me);var ut=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},Ke=class extends j{constructor(){super(...arguments),this.search="",this.badge=void 0,this.onDebouncedSearch=M.debounce(t=>{this.search=t})}render(){const t=this.search.length>=2;return u`
      <wui-flex .padding=${["1","3","3","3"]} gap="2" alignItems="center">
        <wui-search-bar @inputChange=${this.onInputChange.bind(this)}></wui-search-bar>
        <wui-certified-switch
          ?checked=${this.badge==="certified"}
          @certifiedSwitchChange=${this.onCertifiedSwitchChange.bind(this)}
          data-testid="wui-certified-switch"
        ></wui-certified-switch>
        ${this.qrButtonTemplate()}
      </wui-flex>
      ${t||this.badge?u`<w3m-all-wallets-search
            query=${this.search}
            .badge=${this.badge}
          ></w3m-all-wallets-search>`:u`<w3m-all-wallets-list .badge=${this.badge}></w3m-all-wallets-list>`}
    `}onInputChange(t){this.onDebouncedSearch(t.detail)}onCertifiedSwitchChange(t){t.detail?(this.badge="certified",Ie.showSvg("Only WalletConnect certified",{icon:"walletConnectBrown",iconColor:"accent-100"})):this.badge=void 0}qrButtonTemplate(){return M.isMobile()?u`
        <wui-icon-box
          size="xl"
          iconSize="xl"
          color="accent-primary"
          icon="qrCode"
          border
          borderColor="wui-accent-glass-010"
          @click=${this.onWalletConnectQr.bind(this)}
        ></wui-icon-box>
      `:null}onWalletConnectQr(){P.push("ConnectingWalletConnect")}};ut([A()],Ke.prototype,"search",void 0);ut([A()],Ke.prototype,"badge",void 0);Ke=ut([N("w3m-all-wallets-view")],Ke);var en=function(e,t,o,r){var n=arguments.length,i=n<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,o):r,a;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")i=Reflect.decorate(e,t,o,r);else for(var s=e.length-1;s>=0;s--)(a=e[s])&&(i=(n<3?a(i):n>3?a(t,o,i):a(t,o))||i);return n>3&&i&&Object.defineProperty(t,o,i),i},$t=class extends j{constructor(){super(...arguments),this.wallet=P.state.data?.wallet}render(){if(!this.wallet)throw new Error("w3m-downloads-view");return u`
      <wui-flex gap="2" flexDirection="column" .padding=${["3","3","4","3"]}>
        ${this.chromeTemplate()} ${this.iosTemplate()} ${this.androidTemplate()}
        ${this.homepageTemplate()}
      </wui-flex>
    `}chromeTemplate(){return this.wallet?.chrome_store?u`<wui-list-item
      variant="icon"
      icon="chromeStore"
      iconVariant="square"
      @click=${this.onChromeStore.bind(this)}
      chevron
    >
      <wui-text variant="md-medium" color="primary">Chrome Extension</wui-text>
    </wui-list-item>`:null}iosTemplate(){return this.wallet?.app_store?u`<wui-list-item
      variant="icon"
      icon="appStore"
      iconVariant="square"
      @click=${this.onAppStore.bind(this)}
      chevron
    >
      <wui-text variant="md-medium" color="primary">iOS App</wui-text>
    </wui-list-item>`:null}androidTemplate(){return this.wallet?.play_store?u`<wui-list-item
      variant="icon"
      icon="playStore"
      iconVariant="square"
      @click=${this.onPlayStore.bind(this)}
      chevron
    >
      <wui-text variant="md-medium" color="primary">Android App</wui-text>
    </wui-list-item>`:null}homepageTemplate(){return this.wallet?.homepage?u`
      <wui-list-item
        variant="icon"
        icon="browser"
        iconVariant="square-blue"
        @click=${this.onHomePage.bind(this)}
        chevron
      >
        <wui-text variant="md-medium" color="primary">Website</wui-text>
      </wui-list-item>
    `:null}openStore(t){t.href&&this.wallet&&(G.sendEvent({type:"track",event:"GET_WALLET",properties:{name:this.wallet.name,walletRank:this.wallet.order,explorerId:this.wallet.id,type:t.type}}),M.openHref(t.href,"_blank"))}onChromeStore(){this.wallet?.chrome_store&&this.openStore({href:this.wallet.chrome_store,type:"chrome_store"})}onAppStore(){this.wallet?.app_store&&this.openStore({href:this.wallet.app_store,type:"app_store"})}onPlayStore(){this.wallet?.play_store&&this.openStore({href:this.wallet.play_store,type:"play_store"})}onHomePage(){this.wallet?.homepage&&this.openStore({href:this.wallet.homepage,type:"homepage"})}};$t=en([N("w3m-downloads-view")],$t);export{Ke as W3mAllWalletsView,Ue as W3mConnectingWcBasicView,$t as W3mDownloadsView};

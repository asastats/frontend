import{n as Mt,t as qt}from"./dist-C9thfrVX.js";import{A as Vt,C as A,E as Ht,G as Gt,I as ot,J as E,K as v,L as rt,N as Qe,O as Nt,R as at,S as fe,T as L,W as C,a as Yt,c as W,d as Kt,f as ft,g as O,h as Qt,i as ye,j as F,k as S,m as U,n as g,o as Xt,p as Oe,s as _t,t as _e,v as D,w as Ue,y as m}from"./ApiController-Cl_P8qug.js";import{S as Me,_ as s,a as qe,d as xe,f as yt,i as Ve,o as Zt,p as k,r as b,s as X,t as V,u as T,y as Rt}from"./HelpersUtil-BgIQWZjR.js";import{c as d,n as Ot,o as x,s as h,t as Jt}from"./wui-list-item-JbIagN-a.js";import{n as Ut,t as ve}from"./AlertController-BUtD-ZYp.js";var ie={getGasPriceInEther(e,t){const i=t*e;return Number(i)/1e18},getGasPriceInUSD(e,t,i){const r=ie.getGasPriceInEther(t,i);return v.bigNumber(e).times(r).toNumber()},getPriceImpact({sourceTokenAmount:e,sourceTokenPriceInUSD:t,toTokenPriceInUSD:i,toTokenAmount:r}){const a=v.bigNumber(e).times(t),o=v.bigNumber(r).times(i);return a.minus(o).div(a).times(100).toNumber()},getMaxSlippage(e,t){const i=v.bigNumber(e).div(100);return v.multiply(t,i).toNumber()},getProviderFee(e,t=.0085){return v.bigNumber(e).times(t).toString()},isInsufficientNetworkTokenForGas(e,t){const i=t||"0";return v.bigNumber(e).eq(0)?!0:v.bigNumber(v.bigNumber(i)).gt(e)},isInsufficientSourceTokenForSwap(e,t,i){const r=i?.find(a=>a.address===t)?.quantity?.numeric;return v.bigNumber(r||"0").lt(e)}},vt=15e4;var R={initializing:!1,initialized:!1,loadingPrices:!1,loadingQuote:!1,loadingApprovalTransaction:!1,loadingBuildTransaction:!1,loadingTransaction:!1,switchingTokens:!1,fetchError:!1,approvalTransaction:void 0,swapTransaction:void 0,transactionError:void 0,sourceToken:void 0,sourceTokenAmount:"",sourceTokenPriceInUSD:0,toToken:void 0,toTokenAmount:"",toTokenPriceInUSD:0,networkPrice:"0",networkBalanceInUSD:"0",networkTokenSymbol:"",inputError:void 0,slippage:Qe.CONVERT_SLIPPAGE_TOLERANCE,tokens:void 0,popularTokens:void 0,suggestedTokens:void 0,foundTokens:void 0,myTokensWithBalance:void 0,tokensPriceMap:{},gasFee:"0",gasPriceInUSD:0,priceImpact:void 0,maxSlippage:void 0,providerFee:void 0},c=rt({...R}),We={state:c,subscribe(e){return at(c,()=>e(c))},subscribeKey(e,t){return ot(c,e,t)},getParams(){const e=g.state.activeChain,t=g.getAccountData(e)?.caipAddress??g.state.activeCaipAddress,i=F.getPlainAddress(t),r=Kt(),a=U.getConnectorId(g.state.activeChain);if(!i)throw new Error("No address found to swap the tokens from.");const o=!c.toToken?.address||!c.toToken?.decimals,n=!c.sourceToken?.address||!c.sourceToken?.decimals||!v.bigNumber(c.sourceTokenAmount).gt(0),l=!c.sourceTokenAmount;return{networkAddress:r,fromAddress:i,fromCaipAddress:t,sourceTokenAddress:c.sourceToken?.address,toTokenAddress:c.toToken?.address,toTokenAmount:c.toTokenAmount,toTokenDecimals:c.toToken?.decimals,sourceTokenAmount:c.sourceTokenAmount,sourceTokenDecimals:c.sourceToken?.decimals,invalidToToken:o,invalidSourceToken:n,invalidSourceTokenAmount:l,availableToSwap:t&&!o&&!n&&!l,isAuthConnector:a===E.CONNECTOR_ID.AUTH}},async setSourceToken(e){if(!e){c.sourceToken=e,c.sourceTokenAmount="",c.sourceTokenPriceInUSD=0;return}c.sourceToken=e,await w.setTokenPrice(e.address,"sourceToken")},setSourceTokenAmount(e){c.sourceTokenAmount=e},async setToToken(e){if(!e){c.toToken=e,c.toTokenAmount="",c.toTokenPriceInUSD=0;return}c.toToken=e,await w.setTokenPrice(e.address,"toToken")},setToTokenAmount(e){c.toTokenAmount=e?v.toFixed(e,6):""},async setTokenPrice(e,t){let i=c.tokensPriceMap[e]||0;i||(c.loadingPrices=!0,i=await w.getAddressPrice(e)),t==="sourceToken"?c.sourceTokenPriceInUSD=i:t==="toToken"&&(c.toTokenPriceInUSD=i),c.loadingPrices&&(c.loadingPrices=!1),w.getParams().availableToSwap&&!c.switchingTokens&&w.swapTokens()},async switchTokens(){if(!(c.initializing||!c.initialized||c.switchingTokens)){c.switchingTokens=!0;try{const e=c.toToken?{...c.toToken}:void 0,t=c.sourceToken?{...c.sourceToken}:void 0,i=e&&c.toTokenAmount===""?"1":c.toTokenAmount;w.setSourceTokenAmount(i),w.setToTokenAmount(""),await w.setSourceToken(e),await w.setToToken(t),c.switchingTokens=!1,w.swapTokens()}catch(e){throw c.switchingTokens=!1,e}}},resetState(){c.myTokensWithBalance=R.myTokensWithBalance,c.tokensPriceMap=R.tokensPriceMap,c.initialized=R.initialized,c.initializing=R.initializing,c.switchingTokens=R.switchingTokens,c.sourceToken=R.sourceToken,c.sourceTokenAmount=R.sourceTokenAmount,c.sourceTokenPriceInUSD=R.sourceTokenPriceInUSD,c.toToken=R.toToken,c.toTokenAmount=R.toTokenAmount,c.toTokenPriceInUSD=R.toTokenPriceInUSD,c.networkPrice=R.networkPrice,c.networkTokenSymbol=R.networkTokenSymbol,c.networkBalanceInUSD=R.networkBalanceInUSD,c.inputError=R.inputError},resetValues(){const{networkAddress:e}=w.getParams(),t=c.tokens?.find(i=>i.address===e);w.setSourceToken(t),w.setToToken(void 0)},getApprovalLoadingState(){return c.loadingApprovalTransaction},clearError(){c.transactionError=void 0},async initializeState(){if(!c.initializing){if(c.initializing=!0,!c.initialized)try{await w.fetchTokens(),c.initialized=!0}catch{c.initialized=!1,A.showError("Failed to initialize swap"),m.goBack()}c.initializing=!1}},async fetchTokens(){const{networkAddress:e}=w.getParams();await w.getNetworkTokenPrice(),await w.getMyTokensWithBalance();const t=c.myTokensWithBalance?.find(i=>i.address===e);t&&(c.networkTokenSymbol=t.symbol,w.setSourceToken(t),w.setSourceTokenAmount("0"))},async getTokenList(){const e=g.state.activeCaipNetwork?.caipNetworkId;if(!(c.caipNetworkId===e&&c.tokens))try{c.tokensLoading=!0;const t=await ye.getTokenList(e);c.tokens=t,c.caipNetworkId=e,c.popularTokens=t.sort((a,o)=>a.symbol<o.symbol?-1:a.symbol>o.symbol?1:0);const i=(e&&Qe.SUGGESTED_TOKENS_BY_CHAIN?.[e]||[]).map(a=>t.find(o=>o.symbol===a)).filter(a=>!!a),r=(Qe.SWAP_SUGGESTED_TOKENS||[]).map(a=>t.find(o=>o.symbol===a)).filter(a=>!!a).filter(a=>!i.some(o=>o.address===a.address));c.suggestedTokens=[...i,...r]}catch{c.tokens=[],c.popularTokens=[],c.suggestedTokens=[]}finally{c.tokensLoading=!1}},async getAddressPrice(e){const t=c.tokensPriceMap[e];if(t)return t;const i=(await fe.fetchTokenPrice({addresses:[e]}))?.fungibles||[],r=[...c.tokens||[],...c.myTokensWithBalance||[]].find(n=>n.address===e)?.symbol,a=i.find(n=>n.symbol.toLowerCase()===r?.toLowerCase())?.price||0,o=parseFloat(a.toString());return c.tokensPriceMap[e]=o,o},async getNetworkTokenPrice(){const{networkAddress:e}=w.getParams(),t=(await fe.fetchTokenPrice({addresses:[e]}).catch(()=>(A.showError("Failed to fetch network token price"),{fungibles:[]}))).fungibles?.[0],i=t?.price.toString()||"0";c.tokensPriceMap[e]=parseFloat(i),c.networkTokenSymbol=t?.symbol||"",c.networkPrice=i},async getMyTokensWithBalance(e){const t=await _t.getMyTokensWithBalance({forceUpdate:e,caipNetwork:g.state.activeCaipNetwork,address:g.getAccountData()?.address}),i=ye.mapBalancesToSwapTokens(t);i&&(await w.getInitialGasPrice(),w.setBalances(i))},setBalances(e){const{networkAddress:t}=w.getParams(),i=g.state.activeCaipNetwork;if(!i)return;const r=e.find(a=>a.address===t);e.forEach(a=>{c.tokensPriceMap[a.address]=a.price||0}),c.myTokensWithBalance=e.filter(a=>a.address.startsWith(i.caipNetworkId)),c.networkBalanceInUSD=r?v.multiply(r.quantity.numeric,r.price).toString():"0"},async getInitialGasPrice(){const e=await ye.fetchGasPrice();if(!e)return{gasPrice:null,gasPriceInUSD:null};switch(g.state?.activeCaipNetwork?.chainNamespace){case E.CHAIN.SOLANA:return c.gasFee=e.standard??"0",c.gasPriceInUSD=v.multiply(e.standard,c.networkPrice).div(1e9).toNumber(),{gasPrice:BigInt(c.gasFee),gasPriceInUSD:Number(c.gasPriceInUSD)};case E.CHAIN.EVM:default:const t=e.standard??"0",i=BigInt(t),r=BigInt(vt),a=ie.getGasPriceInUSD(c.networkPrice,r,i);return c.gasFee=t,c.gasPriceInUSD=a,{gasPrice:i,gasPriceInUSD:a}}},async swapTokens(){const e=g.getAccountData()?.address,t=c.sourceToken,i=c.toToken,r=v.bigNumber(c.sourceTokenAmount).gt(0);if(r||w.setToTokenAmount(""),!i||!t||c.loadingPrices||!r||!e)return;c.loadingQuote=!0;const a=v.bigNumber(c.sourceTokenAmount).times(10**t.decimals).round(0).toFixed(0);try{const o=await fe.fetchSwapQuote({userAddress:e,from:t.address,to:i.address,gasPrice:c.gasFee,amount:a.toString()});c.loadingQuote=!1;const n=o?.quotes?.[0]?.toAmount;if(!n){ve.open({displayMessage:"Incorrect amount",debugMessage:"Please enter a valid amount"},"error");return}const l=v.bigNumber(n).div(10**i.decimals).toString();w.setToTokenAmount(l),w.hasInsufficientToken(c.sourceTokenAmount,t.address)?c.inputError="Insufficient balance":(c.inputError=void 0,w.setTransactionDetails())}catch(o){const n=await ye.handleSwapError(o);c.loadingQuote=!1,c.inputError=n||"Insufficient balance"}},async getTransaction(){const{fromCaipAddress:e,availableToSwap:t}=w.getParams(),i=c.sourceToken,r=c.toToken;if(!(!e||!t||!i||!r||c.loadingQuote))try{c.loadingBuildTransaction=!0;const a=await ye.fetchSwapAllowance({userAddress:e,tokenAddress:i.address,sourceTokenAmount:c.sourceTokenAmount,sourceTokenDecimals:i.decimals});let o;return a?o=await w.createSwapTransaction():o=await w.createAllowanceTransaction(),c.loadingBuildTransaction=!1,c.fetchError=!1,o}catch{m.goBack(),A.showError("Failed to check allowance"),c.loadingBuildTransaction=!1,c.approvalTransaction=void 0,c.swapTransaction=void 0,c.fetchError=!0;return}},async createAllowanceTransaction(){const{fromCaipAddress:e,sourceTokenAddress:t,toTokenAddress:i}=w.getParams();if(!(!e||!i)){if(!t)throw new Error("createAllowanceTransaction - No source token address found.");try{const r=await fe.generateApproveCalldata({from:t,to:i,userAddress:e}),a=F.getPlainAddress(r.tx.from);if(!a)throw new Error("SwapController:createAllowanceTransaction - address is required");const o={data:r.tx.data,to:a,gasPrice:BigInt(r.tx.eip155.gasPrice),value:BigInt(r.tx.value),toAmount:c.toTokenAmount};return c.swapTransaction=void 0,c.approvalTransaction={data:o.data,to:o.to,gasPrice:o.gasPrice,value:o.value,toAmount:o.toAmount},{data:o.data,to:o.to,gasPrice:o.gasPrice,value:o.value,toAmount:o.toAmount}}catch{m.goBack(),A.showError("Failed to create approval transaction"),c.approvalTransaction=void 0,c.swapTransaction=void 0,c.fetchError=!0;return}}},async createSwapTransaction(){const{networkAddress:e,fromCaipAddress:t,sourceTokenAmount:i}=w.getParams(),r=c.sourceToken,a=c.toToken;if(!t||!i||!r||!a)return;const o=W.parseUnits(i,r.decimals)?.toString();try{const n=await fe.generateSwapCalldata({userAddress:t,from:r.address,to:a.address,amount:o,disableEstimate:!0}),l=r.address===e,_=BigInt(n.tx.eip155.gas),$e=BigInt(n.tx.eip155.gasPrice),Ne=F.getPlainAddress(n.tx.to);if(!Ne)throw new Error("SwapController:createSwapTransaction - address is required");const gt={data:n.tx.data,to:Ne,gas:_,gasPrice:$e,value:BigInt(l?o??"0":"0"),toAmount:c.toTokenAmount};return c.gasPriceInUSD=ie.getGasPriceInUSD(c.networkPrice,_,$e),c.approvalTransaction=void 0,c.swapTransaction=gt,gt}catch{m.goBack(),A.showError("Failed to create transaction"),c.approvalTransaction=void 0,c.swapTransaction=void 0,c.fetchError=!0;return}},onEmbeddedWalletApprovalSuccess(){A.showLoading("Approve limit increase in your wallet"),m.replace("SwapPreview")},async sendTransactionForApproval(e){const{fromAddress:t,isAuthConnector:i}=w.getParams();c.loadingApprovalTransaction=!0,i?m.pushTransactionStack({onSuccess:w.onEmbeddedWalletApprovalSuccess}):A.showLoading("Approve limit increase in your wallet");try{await W.sendTransaction({address:t,to:e.to,data:e.data,value:e.value,chainNamespace:E.CHAIN.EVM}),await w.swapTokens(),await w.getTransaction(),c.approvalTransaction=void 0,c.loadingApprovalTransaction=!1}catch(a){const o=a;c.transactionError=o?.displayMessage,c.loadingApprovalTransaction=!1,A.showError(o?.displayMessage||"Transaction error"),D.sendEvent({type:"track",event:"SWAP_APPROVAL_ERROR",properties:{message:o?.displayMessage||o?.message||"Unknown",network:g.state.activeCaipNetwork?.caipNetworkId||"",swapFromToken:w.state.sourceToken?.symbol||"",swapToToken:w.state.toToken?.symbol||"",swapFromAmount:w.state.sourceTokenAmount||"",swapToAmount:w.state.toTokenAmount||"",isSmartAccount:Oe(E.CHAIN.EVM)===Ue.ACCOUNT_TYPES.SMART_ACCOUNT}})}},async sendTransactionForSwap(e){if(!e)return;const{fromAddress:t,toTokenAmount:i,isAuthConnector:r}=w.getParams();c.loadingTransaction=!0;const a=`Swapping ${c.sourceToken?.symbol} to ${v.formatNumberToLocalString(i,3)} ${c.toToken?.symbol}`,o=`Swapped ${c.sourceToken?.symbol} to ${v.formatNumberToLocalString(i,3)} ${c.toToken?.symbol}`;r?m.pushTransactionStack({onSuccess(){m.replace("Account"),A.showLoading(a),We.resetState()}}):A.showLoading("Confirm transaction in your wallet");try{const n=[c.sourceToken?.address,c.toToken?.address].join(","),l=await W.sendTransaction({address:t,to:e.to,data:e.data,value:e.value,chainNamespace:E.CHAIN.EVM});return c.loadingTransaction=!1,A.showSuccess(o),D.sendEvent({type:"track",event:"SWAP_SUCCESS",properties:{network:g.state.activeCaipNetwork?.caipNetworkId||"",swapFromToken:w.state.sourceToken?.symbol||"",swapToToken:w.state.toToken?.symbol||"",swapFromAmount:w.state.sourceTokenAmount||"",swapToAmount:w.state.toTokenAmount||"",isSmartAccount:Oe(E.CHAIN.EVM)===Ue.ACCOUNT_TYPES.SMART_ACCOUNT}}),We.resetState(),r||m.replace("Account"),We.getMyTokensWithBalance(n),l}catch(n){const l=n;c.transactionError=l?.displayMessage,c.loadingTransaction=!1,A.showError(l?.displayMessage||"Transaction error"),D.sendEvent({type:"track",event:"SWAP_ERROR",properties:{message:l?.displayMessage||l?.message||"Unknown",network:g.state.activeCaipNetwork?.caipNetworkId||"",swapFromToken:w.state.sourceToken?.symbol||"",swapToToken:w.state.toToken?.symbol||"",swapFromAmount:w.state.sourceTokenAmount||"",swapToAmount:w.state.toTokenAmount||"",isSmartAccount:Oe(E.CHAIN.EVM)===Ue.ACCOUNT_TYPES.SMART_ACCOUNT}});return}},hasInsufficientToken(e,t){return ie.isInsufficientSourceTokenForSwap(e,t,c.myTokensWithBalance)},setTransactionDetails(){const{toTokenAddress:e,toTokenDecimals:t}=w.getParams();!e||!t||(c.gasPriceInUSD=ie.getGasPriceInUSD(c.networkPrice,BigInt(c.gasFee),BigInt(vt)),c.priceImpact=ie.getPriceImpact({sourceTokenAmount:c.sourceTokenAmount,sourceTokenPriceInUSD:c.sourceTokenPriceInUSD,toTokenPriceInUSD:c.toTokenPriceInUSD,toTokenAmount:c.toTokenAmount}),c.maxSlippage=ie.getMaxSlippage(c.slippage,c.toTokenAmount),c.providerFee=ie.getProviderFee(c.sourceTokenAmount))}},w=Nt(We),q=rt({message:"",open:!1,triggerRect:{width:0,height:0,top:0,left:0},variant:"shade"}),ei={state:q,subscribe(e){return at(q,()=>e(q))},subscribeKey(e,t){return ot(q,e,t)},showTooltip({message:e,triggerRect:t,variant:i}){q.open=!0,q.message=e,q.triggerRect=t,q.variant=i},hide(){q.open=!1,q.message="",q.triggerRect={width:0,height:0,top:0,left:0}}},z=Nt(ei),Wt={isUnsupportedChainView(){return m.state.view==="UnsupportedChain"||m.state.view==="SwitchNetwork"&&m.state.history.includes("UnsupportedChain")},async safeClose(){if(this.isUnsupportedChainView()){O.shake();return}if(await Ut.isSIWXCloseDisabled()){O.shake();return}(m.state.view==="DataCapture"||m.state.view==="DataCaptureOtpConfirm")&&W.disconnect(),O.close()}},ti=T`
  :host {
    display: block;
    border-radius: clamp(0px, ${({borderRadius:e})=>e[8]}, 44px);
    box-shadow: 0 0 0 1px ${({tokens:e})=>e.theme.foregroundPrimary};
    overflow: hidden;
  }
`,ii=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},Xe=class extends k{render(){return s`<slot></slot>`}};Xe.styles=[X,ti];Xe=ii([b("wui-card")],Xe);var oi=T`
  :host {
    width: 100%;
  }

  :host > wui-flex {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: ${({spacing:e})=>e[2]};
    padding: ${({spacing:e})=>e[3]};
    border-radius: ${({borderRadius:e})=>e[6]};
    border: 1px solid ${({tokens:e})=>e.theme.borderPrimary};
    box-sizing: border-box;
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    box-shadow: 0px 0px 16px 0px rgba(0, 0, 0, 0.25);
    color: ${({tokens:e})=>e.theme.textPrimary};
  }

  :host > wui-flex[data-type='info'] {
    .icon-box {
      background-color: ${({tokens:e})=>e.theme.foregroundSecondary};

      wui-icon {
        color: ${({tokens:e})=>e.theme.iconDefault};
      }
    }
  }
  :host > wui-flex[data-type='success'] {
    .icon-box {
      background-color: ${({tokens:e})=>e.core.backgroundSuccess};

      wui-icon {
        color: ${({tokens:e})=>e.core.borderSuccess};
      }
    }
  }
  :host > wui-flex[data-type='warning'] {
    .icon-box {
      background-color: ${({tokens:e})=>e.core.backgroundWarning};

      wui-icon {
        color: ${({tokens:e})=>e.core.borderWarning};
      }
    }
  }
  :host > wui-flex[data-type='error'] {
    .icon-box {
      background-color: ${({tokens:e})=>e.core.backgroundError};

      wui-icon {
        color: ${({tokens:e})=>e.core.borderError};
      }
    }
  }

  wui-flex {
    width: 100%;
  }

  wui-text {
    word-break: break-word;
    flex: 1;
  }

  .close {
    cursor: pointer;
    color: ${({tokens:e})=>e.theme.iconDefault};
  }

  .icon-box {
    height: 40px;
    width: 40px;
    border-radius: ${({borderRadius:e})=>e[2]};
    background-color: var(--local-icon-bg-value);
  }
`,nt=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},ri={info:"info",success:"checkmark",warning:"warningCircle",error:"warning"},ke=class extends k{constructor(){super(...arguments),this.message="",this.type="info"}render(){return s`
      <wui-flex
        data-type=${x(this.type)}
        flexDirection="row"
        justifyContent="space-between"
        alignItems="center"
        gap="2"
      >
        <wui-flex columnGap="2" flexDirection="row" alignItems="center">
          <wui-flex
            flexDirection="row"
            alignItems="center"
            justifyContent="center"
            class="icon-box"
          >
            <wui-icon color="inherit" size="md" name=${ri[this.type]}></wui-icon>
          </wui-flex>
          <wui-text variant="md-medium" color="inherit" data-testid="wui-alertbar-text"
            >${this.message}</wui-text
          >
        </wui-flex>
        <wui-icon
          class="close"
          color="inherit"
          size="sm"
          name="close"
          @click=${this.onClose}
        ></wui-icon>
      </wui-flex>
    `}onClose(){ve.close()}};ke.styles=[X,oi];nt([d()],ke.prototype,"message",void 0);nt([d()],ke.prototype,"type",void 0);ke=nt([b("wui-alertbar")],ke);var ai=T`
  :host {
    display: block;
    position: absolute;
    top: ${({spacing:e})=>e[3]};
    left: ${({spacing:e})=>e[4]};
    right: ${({spacing:e})=>e[4]};
    opacity: 0;
    pointer-events: none;
  }
`,Dt=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},ni={info:{backgroundColor:"fg-350",iconColor:"fg-325",icon:"info"},success:{backgroundColor:"success-glass-reown-020",iconColor:"success-125",icon:"checkmark"},warning:{backgroundColor:"warning-glass-reown-020",iconColor:"warning-100",icon:"warningCircle"},error:{backgroundColor:"error-glass-reown-020",iconColor:"error-125",icon:"warning"}},De=class extends k{constructor(){super(),this.unsubscribe=[],this.open=ve.state.open,this.onOpen(!0),this.unsubscribe.push(ve.subscribeKey("open",t=>{this.open=t,this.onOpen(!1)}))}disconnectedCallback(){this.unsubscribe.forEach(t=>t())}render(){const{message:t,variant:i}=ve.state,r=ni[i];return s`
      <wui-alertbar
        message=${t}
        backgroundColor=${r?.backgroundColor}
        iconColor=${r?.iconColor}
        icon=${r?.icon}
        type=${i}
      ></wui-alertbar>
    `}onOpen(t){this.open?(this.animate([{opacity:0,transform:"scale(0.85)"},{opacity:1,transform:"scale(1)"}],{duration:150,fill:"forwards",easing:"ease"}),this.style.cssText="pointer-events: auto"):t||(this.animate([{opacity:1,transform:"scale(1)"},{opacity:0,transform:"scale(0.85)"}],{duration:150,fill:"forwards",easing:"ease"}),this.style.cssText="pointer-events: none")}};De.styles=ai;Dt([h()],De.prototype,"open",void 0);De=Dt([b("w3m-alertbar")],De);var si=T`
  :host {
    position: relative;
  }

  button {
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: transparent;
    padding: ${({spacing:e})=>e[1]};
  }

  /* -- Colors --------------------------------------------------- */
  button[data-type='accent'] wui-icon {
    color: ${({tokens:e})=>e.core.iconAccentPrimary};
  }

  button[data-type='neutral'][data-variant='primary'] wui-icon {
    color: ${({tokens:e})=>e.theme.iconInverse};
  }

  button[data-type='neutral'][data-variant='secondary'] wui-icon {
    color: ${({tokens:e})=>e.theme.iconDefault};
  }

  button[data-type='success'] wui-icon {
    color: ${({tokens:e})=>e.core.iconSuccess};
  }

  button[data-type='error'] wui-icon {
    color: ${({tokens:e})=>e.core.iconError};
  }

  /* -- Sizes --------------------------------------------------- */
  button[data-size='xs'] {
    width: 16px;
    height: 16px;

    border-radius: ${({borderRadius:e})=>e[1]};
  }

  button[data-size='sm'] {
    width: 20px;
    height: 20px;
    border-radius: ${({borderRadius:e})=>e[1]};
  }

  button[data-size='md'] {
    width: 24px;
    height: 24px;
    border-radius: ${({borderRadius:e})=>e[2]};
  }

  button[data-size='lg'] {
    width: 28px;
    height: 28px;
    border-radius: ${({borderRadius:e})=>e[2]};
  }

  button[data-size='xs'] wui-icon {
    width: 8px;
    height: 8px;
  }

  button[data-size='sm'] wui-icon {
    width: 12px;
    height: 12px;
  }

  button[data-size='md'] wui-icon {
    width: 16px;
    height: 16px;
  }

  button[data-size='lg'] wui-icon {
    width: 20px;
    height: 20px;
  }

  /* -- Hover --------------------------------------------------- */
  @media (hover: hover) {
    button[data-type='accent']:hover:enabled {
      background-color: ${({tokens:e})=>e.core.foregroundAccent010};
    }

    button[data-variant='primary'][data-type='neutral']:hover:enabled {
      background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
    }

    button[data-variant='secondary'][data-type='neutral']:hover:enabled {
      background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
    }

    button[data-type='success']:hover:enabled {
      background-color: ${({tokens:e})=>e.core.backgroundSuccess};
    }

    button[data-type='error']:hover:enabled {
      background-color: ${({tokens:e})=>e.core.backgroundError};
    }
  }

  /* -- Focus --------------------------------------------------- */
  button:focus-visible {
    box-shadow: 0 0 0 4px ${({tokens:e})=>e.core.foregroundAccent020};
  }

  /* -- Properties --------------------------------------------------- */
  button[data-full-width='true'] {
    width: 100%;
  }

  :host([fullWidth]) {
    width: 100%;
  }

  button[disabled] {
    opacity: 0.5;
    cursor: not-allowed;
  }
`,se=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},Y=class extends k{constructor(){super(...arguments),this.icon="card",this.variant="primary",this.type="accent",this.size="md",this.iconSize=void 0,this.fullWidth=!1,this.disabled=!1}render(){return s`<button
      data-variant=${this.variant}
      data-type=${this.type}
      data-size=${this.size}
      data-full-width=${this.fullWidth}
      ?disabled=${this.disabled}
    >
      <wui-icon color="inherit" name=${this.icon} size=${x(this.iconSize)}></wui-icon>
    </button>`}};Y.styles=[X,qe,si];se([d()],Y.prototype,"icon",void 0);se([d()],Y.prototype,"variant",void 0);se([d()],Y.prototype,"type",void 0);se([d()],Y.prototype,"size",void 0);se([d()],Y.prototype,"iconSize",void 0);se([d({type:Boolean})],Y.prototype,"fullWidth",void 0);se([d({type:Boolean})],Y.prototype,"disabled",void 0);Y=se([b("wui-icon-button")],Y);var ci=T`
  button {
    display: block;
    display: flex;
    align-items: center;
    padding: ${({spacing:e})=>e[1]};
    transition: background-color ${({durations:e})=>e.lg}
      ${({easings:e})=>e["ease-out-power-2"]};
    will-change: background-color;
    border-radius: ${({borderRadius:e})=>e[32]};
  }

  wui-image {
    border-radius: 100%;
  }

  wui-text {
    padding-left: ${({spacing:e})=>e[1]};
  }

  .left-icon-container,
  .right-icon-container {
    width: 24px;
    height: 24px;
    justify-content: center;
    align-items: center;
  }

  wui-icon {
    color: ${({tokens:e})=>e.theme.iconDefault};
  }

  /* -- Sizes --------------------------------------------------- */
  button[data-size='lg'] {
    height: 32px;
  }

  button[data-size='md'] {
    height: 28px;
  }

  button[data-size='sm'] {
    height: 24px;
  }

  button[data-size='lg'] wui-image {
    width: 24px;
    height: 24px;
  }

  button[data-size='md'] wui-image {
    width: 20px;
    height: 20px;
  }

  button[data-size='sm'] wui-image {
    width: 16px;
    height: 16px;
  }

  button[data-size='lg'] .left-icon-container {
    width: 24px;
    height: 24px;
  }

  button[data-size='md'] .left-icon-container {
    width: 20px;
    height: 20px;
  }

  button[data-size='sm'] .left-icon-container {
    width: 16px;
    height: 16px;
  }

  /* -- Variants --------------------------------------------------------- */
  button[data-type='filled-dropdown'] {
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
  }

  button[data-type='text-dropdown'] {
    background-color: transparent;
  }

  /* -- Focus states --------------------------------------------------- */
  button:focus-visible:enabled {
    background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
    box-shadow: 0 0 0 4px ${({tokens:e})=>e.core.foregroundAccent040};
  }

  /* -- Hover & Active states ----------------------------------------------------------- */
  @media (hover: hover) and (pointer: fine) {
    button:hover:enabled,
    button:active:enabled {
      background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
    }
  }

  /* -- Disabled states --------------------------------------------------- */
  button:disabled {
    background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
    opacity: 0.5;
  }
`,me=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},li={lg:"lg-regular",md:"md-regular",sm:"sm-regular"},ui={lg:"lg",md:"md",sm:"sm"},re=class extends k{constructor(){super(...arguments),this.imageSrc="",this.text="",this.size="lg",this.type="text-dropdown",this.disabled=!1}render(){return s`<button ?disabled=${this.disabled} data-size=${this.size} data-type=${this.type}>
      ${this.imageTemplate()} ${this.textTemplate()}
      <wui-flex class="right-icon-container">
        <wui-icon name="chevronBottom"></wui-icon>
      </wui-flex>
    </button>`}textTemplate(){const t=li[this.size];return this.text?s`<wui-text color="primary" variant=${t}>${this.text}</wui-text>`:null}imageTemplate(){return this.imageSrc?s`<wui-image src=${this.imageSrc} alt="select visual"></wui-image>`:s` <wui-flex class="left-icon-container">
      <wui-icon size=${ui[this.size]} name="networkPlaceholder"></wui-icon>
    </wui-flex>`}};re.styles=[X,qe,ci];me([d()],re.prototype,"imageSrc",void 0);me([d()],re.prototype,"text",void 0);me([d()],re.prototype,"size",void 0);me([d()],re.prototype,"type",void 0);me([d({type:Boolean})],re.prototype,"disabled",void 0);re=me([b("wui-select")],re);qt();var ue={ACCOUNT_TABS:[{label:"Tokens"},{label:"Activity"}],SECURE_SITE_ORIGIN:(typeof Mt<"u"?{}.NEXT_PUBLIC_SECURE_SITE_ORIGIN:void 0)||"https://secure.walletconnect.org",VIEW_DIRECTION:{Next:"next",Prev:"prev"},ANIMATION_DURATIONS:{HeaderText:120,ModalHeight:150,ViewTransition:150},VIEWS_WITH_LEGAL_FOOTER:["Connect","ConnectWallets","OnRampTokenSelect","OnRampFiatSelect","OnRampProviders"],VIEWS_WITH_DEFAULT_FOOTER:["Networks"]},di=T`
  button {
    background-color: transparent;
    padding: ${({spacing:e})=>e[1]};
  }

  button:focus-visible {
    box-shadow: 0 0 0 4px ${({tokens:e})=>e.core.foregroundAccent020};
  }

  button[data-variant='accent']:hover:enabled,
  button[data-variant='accent']:focus-visible {
    background-color: ${({tokens:e})=>e.core.foregroundAccent010};
  }

  button[data-variant='primary']:hover:enabled,
  button[data-variant='primary']:focus-visible,
  button[data-variant='secondary']:hover:enabled,
  button[data-variant='secondary']:focus-visible {
    background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
  }

  button[data-size='xs'] > wui-icon {
    width: 8px;
    height: 8px;
  }

  button[data-size='sm'] > wui-icon {
    width: 12px;
    height: 12px;
  }

  button[data-size='xs'],
  button[data-size='sm'] {
    border-radius: ${({borderRadius:e})=>e[1]};
  }

  button[data-size='md'],
  button[data-size='lg'] {
    border-radius: ${({borderRadius:e})=>e[2]};
  }

  button[data-size='md'] > wui-icon {
    width: 16px;
    height: 16px;
  }

  button[data-size='lg'] > wui-icon {
    width: 20px;
    height: 20px;
  }

  button:disabled {
    background-color: transparent;
    cursor: not-allowed;
    opacity: 0.5;
  }

  button:hover:not(:disabled) {
    background-color: var(--wui-color-accent-glass-015);
  }

  button:focus-visible:not(:disabled) {
    background-color: var(--wui-color-accent-glass-015);
    box-shadow:
      inset 0 0 0 1px var(--wui-color-accent-100),
      0 0 0 4px var(--wui-color-accent-glass-020);
  }
`,we=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},ae=class extends k{constructor(){super(...arguments),this.size="md",this.disabled=!1,this.icon="copy",this.iconColor="default",this.variant="accent"}render(){return s`
      <button data-variant=${this.variant} ?disabled=${this.disabled} data-size=${this.size}>
        <wui-icon
          color=${{accent:"accent-primary",primary:"inverse",secondary:"default"}[this.variant]||this.iconColor}
          size=${this.size}
          name=${this.icon}
        ></wui-icon>
      </button>
    `}};ae.styles=[X,qe,di];we([d()],ae.prototype,"size",void 0);we([d({type:Boolean})],ae.prototype,"disabled",void 0);we([d()],ae.prototype,"icon",void 0);we([d()],ae.prototype,"iconColor",void 0);we([d()],ae.prototype,"variant",void 0);ae=we([b("wui-icon-link")],ae);var pi=Rt`<svg width="86" height="96" fill="none">
  <path
    d="M78.3244 18.926L50.1808 2.45078C45.7376 -0.150261 40.2624 -0.150262 35.8192 2.45078L7.6756 18.926C3.23322 21.5266 0.5 26.3301 0.5 31.5248V64.4752C0.5 69.6699 3.23322 74.4734 7.6756 77.074L35.8192 93.5492C40.2624 96.1503 45.7376 96.1503 50.1808 93.5492L78.3244 77.074C82.7668 74.4734 85.5 69.6699 85.5 64.4752V31.5248C85.5 26.3301 82.7668 21.5266 78.3244 18.926Z"
  />
</svg>`,hi=Rt`
  <svg fill="none" viewBox="0 0 36 40">
    <path
      d="M15.4 2.1a5.21 5.21 0 0 1 5.2 0l11.61 6.7a5.21 5.21 0 0 1 2.61 4.52v13.4c0 1.87-1 3.59-2.6 4.52l-11.61 6.7c-1.62.93-3.6.93-5.22 0l-11.6-6.7a5.21 5.21 0 0 1-2.61-4.51v-13.4c0-1.87 1-3.6 2.6-4.52L15.4 2.1Z"
    />
  </svg>
`,mi=T`
  :host {
    position: relative;
    border-radius: inherit;
    display: flex;
    justify-content: center;
    align-items: center;
    width: var(--local-width);
    height: var(--local-height);
  }

  :host([data-round='true']) {
    background: ${({tokens:e})=>e.theme.foregroundPrimary};
    border-radius: 100%;
    outline: 1px solid ${({tokens:e})=>e.core.glass010};
  }

  svg {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
  }

  svg > path {
    stroke: var(--local-stroke);
  }

  wui-image {
    width: 100%;
    height: 100%;
    -webkit-clip-path: var(--local-path);
    clip-path: var(--local-path);
    background: ${({tokens:e})=>e.theme.foregroundPrimary};
  }

  wui-icon {
    transform: translateY(-5%);
    width: var(--local-icon-size);
    height: var(--local-icon-size);
  }
`,pe=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},te=class extends k{constructor(){super(...arguments),this.size="md",this.name="uknown",this.networkImagesBySize={sm:hi,md:Jt,lg:pi},this.selected=!1,this.round=!1}render(){const t={sm:"4",md:"6",lg:"10"};return this.round?(this.dataset.round="true",this.style.cssText=`
      --local-width: var(--apkt-spacing-10);
      --local-height: var(--apkt-spacing-10);
      --local-icon-size: var(--apkt-spacing-4);
    `):this.style.cssText=`

      --local-path: var(--apkt-path-network-${this.size});
      --local-width:  var(--apkt-width-network-${this.size});
      --local-height:  var(--apkt-height-network-${this.size});
      --local-icon-size:  var(--apkt-spacing-${t[this.size]});
    `,s`${this.templateVisual()} ${this.svgTemplate()} `}svgTemplate(){return this.round?null:this.networkImagesBySize[this.size]}templateVisual(){return this.imageSrc?s`<wui-image src=${this.imageSrc} alt=${this.name}></wui-image>`:s`<wui-icon size="inherit" color="default" name="networkPlaceholder"></wui-icon>`}};te.styles=[X,mi];pe([d()],te.prototype,"size",void 0);pe([d()],te.prototype,"name",void 0);pe([d({type:Object})],te.prototype,"networkImagesBySize",void 0);pe([d()],te.prototype,"imageSrc",void 0);pe([d({type:Boolean})],te.prototype,"selected",void 0);pe([d({type:Boolean})],te.prototype,"round",void 0);te=pe([b("wui-network-image")],te);var wi=T`
  :host {
    position: relative;
    display: flex;
    width: 100%;
    height: 1px;
    background-color: ${({tokens:e})=>e.theme.borderPrimary};
    justify-content: center;
    align-items: center;
  }

  :host > wui-text {
    position: absolute;
    padding: 0px 8px;
    transition: background-color ${({durations:e})=>e.lg}
      ${({easings:e})=>e["ease-out-power-2"]};
    will-change: background-color;
  }

  :host([data-bg-color='primary']) > wui-text {
    background-color: ${({tokens:e})=>e.theme.backgroundPrimary};
  }

  :host([data-bg-color='secondary']) > wui-text {
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
  }
`,st=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},Te=class extends k{constructor(){super(...arguments),this.text="",this.bgColor="primary"}render(){return this.dataset.bgColor=this.bgColor,s`${this.template()}`}template(){return this.text?s`<wui-text variant="md-regular" color="secondary">${this.text}</wui-text>`:null}};Te.styles=[X,wi];st([d()],Te.prototype,"text",void 0);st([d()],Te.prototype,"bgColor",void 0);Te=st([b("wui-separator")],Te);var f={INVALID_PAYMENT_CONFIG:"INVALID_PAYMENT_CONFIG",INVALID_RECIPIENT:"INVALID_RECIPIENT",INVALID_ASSET:"INVALID_ASSET",INVALID_AMOUNT:"INVALID_AMOUNT",UNKNOWN_ERROR:"UNKNOWN_ERROR",UNABLE_TO_INITIATE_PAYMENT:"UNABLE_TO_INITIATE_PAYMENT",INVALID_CHAIN_NAMESPACE:"INVALID_CHAIN_NAMESPACE",GENERIC_PAYMENT_ERROR:"GENERIC_PAYMENT_ERROR",UNABLE_TO_GET_EXCHANGES:"UNABLE_TO_GET_EXCHANGES",ASSET_NOT_SUPPORTED:"ASSET_NOT_SUPPORTED",UNABLE_TO_GET_PAY_URL:"UNABLE_TO_GET_PAY_URL",UNABLE_TO_GET_BUY_STATUS:"UNABLE_TO_GET_BUY_STATUS",UNABLE_TO_GET_TOKEN_BALANCES:"UNABLE_TO_GET_TOKEN_BALANCES",UNABLE_TO_GET_QUOTE:"UNABLE_TO_GET_QUOTE",UNABLE_TO_GET_QUOTE_STATUS:"UNABLE_TO_GET_QUOTE_STATUS",INVALID_RECIPIENT_ADDRESS_FOR_ASSET:"INVALID_RECIPIENT_ADDRESS_FOR_ASSET"},oe={[f.INVALID_PAYMENT_CONFIG]:"Invalid payment configuration",[f.INVALID_RECIPIENT]:"Invalid recipient address",[f.INVALID_ASSET]:"Invalid asset specified",[f.INVALID_AMOUNT]:"Invalid payment amount",[f.INVALID_RECIPIENT_ADDRESS_FOR_ASSET]:"Invalid recipient address for the asset selected",[f.UNKNOWN_ERROR]:"Unknown payment error occurred",[f.UNABLE_TO_INITIATE_PAYMENT]:"Unable to initiate payment",[f.INVALID_CHAIN_NAMESPACE]:"Invalid chain namespace",[f.GENERIC_PAYMENT_ERROR]:"Unable to process payment",[f.UNABLE_TO_GET_EXCHANGES]:"Unable to get exchanges",[f.ASSET_NOT_SUPPORTED]:"Asset not supported by the selected exchange",[f.UNABLE_TO_GET_PAY_URL]:"Unable to get payment URL",[f.UNABLE_TO_GET_BUY_STATUS]:"Unable to get buy status",[f.UNABLE_TO_GET_TOKEN_BALANCES]:"Unable to get token balances",[f.UNABLE_TO_GET_QUOTE]:"Unable to get quote. Please choose a different token",[f.UNABLE_TO_GET_QUOTE_STATUS]:"Unable to get quote status"},y=class Lt extends Error{get message(){return oe[this.code]}constructor(t,i){super(oe[t]),this.name="AppKitPayError",this.code=t,this.details=i,Error.captureStackTrace&&Error.captureStackTrace(this,Lt)}},gi="https://rpc.walletconnect.org/v1/json-rpc",bt="reown_test";function fi(){const{chainNamespace:e}=C.parseCaipNetworkId(p.state.paymentAsset.network);if(!F.isAddress(p.state.recipient,e))throw new y(f.INVALID_RECIPIENT_ADDRESS_FOR_ASSET,`Provide valid recipient address for namespace "${e}"`)}async function yi(e,t,i){if(t!==E.CHAIN.EVM)throw new y(f.INVALID_CHAIN_NAMESPACE);if(!i.fromAddress)throw new y(f.INVALID_PAYMENT_CONFIG,"fromAddress is required for native EVM payments.");const r=typeof i.amount=="string"?parseFloat(i.amount):i.amount;if(isNaN(r))throw new y(f.INVALID_PAYMENT_CONFIG);const a=e.metadata?.decimals??18,o=W.parseUnits(r.toString(),a);if(typeof o!="bigint")throw new y(f.GENERIC_PAYMENT_ERROR);return await W.sendTransaction({chainNamespace:t,to:i.recipient,address:i.fromAddress,value:o,data:"0x"})??void 0}async function vi(e,t){if(!t.fromAddress)throw new y(f.INVALID_PAYMENT_CONFIG,"fromAddress is required for ERC20 EVM payments.");const i=e.asset,r=t.recipient,a=Number(e.metadata.decimals),o=W.parseUnits(t.amount.toString(),a);if(o===void 0)throw new y(f.GENERIC_PAYMENT_ERROR);return await W.writeContract({fromAddress:t.fromAddress,tokenAddress:i,args:[r,o],method:"transfer",abi:Gt.getERC20Abi(i),chainNamespace:E.CHAIN.EVM})??void 0}async function bi(e,t){if(e!==E.CHAIN.SOLANA)throw new y(f.INVALID_CHAIN_NAMESPACE);if(!t.fromAddress)throw new y(f.INVALID_PAYMENT_CONFIG,"fromAddress is required for Solana payments.");const i=typeof t.amount=="string"?parseFloat(t.amount):t.amount;if(isNaN(i)||i<=0)throw new y(f.INVALID_PAYMENT_CONFIG,"Invalid payment amount.");try{if(!Yt.getProvider(e))throw new y(f.GENERIC_PAYMENT_ERROR,"No Solana provider available.");const r=await W.sendTransaction({chainNamespace:E.CHAIN.SOLANA,to:t.recipient,value:i,tokenMint:t.tokenMint});if(!r)throw new y(f.GENERIC_PAYMENT_ERROR,"Transaction failed.");return r}catch(r){throw r instanceof y?r:new y(f.GENERIC_PAYMENT_ERROR,`Solana payment failed: ${r}`)}}async function xi({sourceToken:e,toToken:t,amount:i,recipient:r}){const a=W.parseUnits(i,e.metadata.decimals),o=W.parseUnits(i,t.metadata.decimals);return Promise.resolve({type:At,origin:{amount:a?.toString()??"0",currency:e},destination:{amount:o?.toString()??"0",currency:t},fees:[{id:"service",label:"Service Fee",amount:"0",currency:t}],steps:[{requestId:At,type:"deposit",deposit:{amount:a?.toString()??"0",currency:e.asset,receiver:r}}],timeInSeconds:6})}function Ze(e){if(!e)return null;const t=e.steps[0];return!t||t.type!=="deposit"?null:t}function Ge(e,t=0){if(!e)return[];const i=e.steps.filter(a=>a.type===Ui),r=i.filter((a,o)=>o+1>t);return i.length>0&&i.length<3?r:[]}var ct=new Vt({baseUrl:F.getApiUrl(),clientId:null}),ki=class extends Error{};function Ti(){return`${gi}?projectId=${S.getSnapshot().projectId}`}function lt(){const{projectId:e,sdkType:t,sdkVersion:i}=S.state;return{projectId:e,st:t||"appkit",sv:i||"html-wagmi-4.2.2"}}async function ut(e,t){const i=Ti(),{sdkType:r,sdkVersion:a,projectId:o}=S.getSnapshot(),n={jsonrpc:"2.0",id:1,method:e,params:{...t||{},st:r,sv:a,projectId:o}},l=await(await fetch(i,{method:"POST",body:JSON.stringify(n),headers:{"Content-Type":"application/json"}})).json();if(l.error)throw new ki(l.error.message);return l}async function xt(e){return(await ut("reown_getExchanges",e)).result}async function kt(e){return(await ut("reown_getExchangePayUrl",e)).result}async function Ai(e){return(await ut("reown_getExchangeBuyStatus",e)).result}async function Si(e){const t=v.bigNumber(e.amount).times(10**e.toToken.metadata.decimals).toString(),{chainId:i,chainNamespace:r}=C.parseCaipNetworkId(e.sourceToken.network),{chainId:a,chainNamespace:o}=C.parseCaipNetworkId(e.toToken.network),n=e.sourceToken.asset==="native"?ft(r):e.sourceToken.asset,l=e.toToken.asset==="native"?ft(o):e.toToken.asset;return await ct.post({path:"/appkit/v1/transfers/quote",body:{user:e.address,originChainId:i.toString(),originCurrency:n,destinationChainId:a.toString(),destinationCurrency:l,recipient:e.recipient,amount:t},params:lt()})}async function Ei(e){const t=V.isLowerCaseMatch(e.sourceToken.network,e.toToken.network),i=V.isLowerCaseMatch(e.sourceToken.asset,e.toToken.asset);return t&&i?xi(e):Si(e)}async function Ii(e){return await ct.get({path:"/appkit/v1/transfers/status",params:{requestId:e.requestId,...lt()}})}async function Ci(e){return await ct.get({path:`/appkit/v1/transfers/assets/exchanges/${e}`,params:lt()})}var Pi=["eip155","solana"],$i={eip155:{native:{assetNamespace:"slip44",assetReference:"60"},defaultTokenNamespace:"erc20"},solana:{native:{assetNamespace:"slip44",assetReference:"501"},defaultTokenNamespace:"token"}};function Ye(e,t){const{chainNamespace:i,chainId:r}=C.parseCaipNetworkId(e),a=$i[i];if(!a)throw new Error(`Unsupported chain namespace for CAIP-19 formatting: ${i}`);let o=a.native.assetNamespace,n=a.native.assetReference;return t!=="native"&&(o=a.defaultTokenNamespace,n=t),`${`${i}:${r}`}/${o}:${n}`}function Ni(e){const{chainNamespace:t}=C.parseCaipNetworkId(e);return Pi.includes(t)}function _i(e){const t=g.getAllRequestedCaipNetworks().find(r=>r.caipNetworkId===e.chainId);let i=e.address;if(!t)throw new Error(`Target network not found for balance chainId "${e.chainId}"`);if(V.isLowerCaseMatch(e.symbol,t.nativeCurrency.symbol))i="native";else if(F.isCaipAddress(i)){const{address:r}=C.parseCaipAddress(i);i=r}else if(!i)throw new Error(`Balance address not found for balance symbol "${e.symbol}"`);return{network:t.caipNetworkId,asset:i,metadata:{name:e.name,symbol:e.symbol,decimals:Number(e.quantity.decimals),logoURI:e.iconUrl},amount:e.quantity.numeric}}function Ri(e){return{chainId:e.network,address:`${e.network}:${e.asset}`,symbol:e.metadata.symbol,name:e.metadata.name,iconUrl:e.metadata.logoURI||"",price:0,quantity:{numeric:"0",decimals:e.metadata.decimals.toString()}}}function Le(e){const t=v.bigNumber(e,{safe:!0});return t.lt(.001)?"<0.001":t.round(4).toString()}function Oi(e){const t=g.getAllRequestedCaipNetworks().find(i=>i.caipNetworkId===e.network);return t?!!t.testnet:!1}var Tt=0,Ke="unknown",At="direct-transfer";var Ui="transaction",u=rt({paymentAsset:{network:"eip155:1",asset:"0x0",metadata:{name:"0x0",symbol:"0x0",decimals:0}},recipient:"0x0",amount:0,isConfigured:!1,error:null,isPaymentInProgress:!1,exchanges:[],isLoading:!1,openInNewTab:!0,redirectUrl:void 0,payWithExchange:void 0,currentPayment:void 0,analyticsSet:!1,paymentId:void 0,choice:"pay",tokenBalances:{[E.CHAIN.EVM]:[],[E.CHAIN.SOLANA]:[]},isFetchingTokenBalances:!1,selectedPaymentAsset:null,quote:void 0,quoteStatus:"waiting",quoteError:null,isFetchingQuote:!1,selectedExchange:void 0,exchangeUrlForQuote:void 0,requestId:void 0}),p={state:u,subscribe(e){return at(u,()=>e(u))},subscribeKey(e,t){return ot(u,e,t)},async handleOpenPay(e){this.resetState(),this.setPaymentConfig(e),this.initializeAnalytics(),fi(),await this.prepareTokenLogo(),u.isConfigured=!0,D.sendEvent({type:"track",event:"PAY_MODAL_OPEN",properties:{exchanges:u.exchanges,configuration:{network:u.paymentAsset.network,asset:u.paymentAsset.asset,recipient:u.recipient,amount:u.amount}}}),await O.open({view:"Pay"})},resetState(){u.paymentAsset={network:"eip155:1",asset:"0x0",metadata:{name:"0x0",symbol:"0x0",decimals:0}},u.recipient="0x0",u.amount=0,u.isConfigured=!1,u.error=null,u.isPaymentInProgress=!1,u.isLoading=!1,u.currentPayment=void 0,u.selectedExchange=void 0,u.exchangeUrlForQuote=void 0,u.requestId=void 0},resetQuoteState(){u.quote=void 0,u.quoteStatus="waiting",u.quoteError=null,u.isFetchingQuote=!1,u.requestId=void 0},setPaymentConfig(e){if(!e.paymentAsset)throw new y(f.INVALID_PAYMENT_CONFIG);try{u.choice=e.choice??"pay",u.paymentAsset=e.paymentAsset,u.recipient=e.recipient,u.amount=e.amount,u.openInNewTab=e.openInNewTab??!0,u.redirectUrl=e.redirectUrl,u.payWithExchange=e.payWithExchange,u.error=null}catch(t){throw new y(f.INVALID_PAYMENT_CONFIG,t.message)}},setSelectedPaymentAsset(e){u.selectedPaymentAsset=e},setSelectedExchange(e){u.selectedExchange=e},setRequestId(e){u.requestId=e},setPaymentInProgress(e){u.isPaymentInProgress=e},getPaymentAsset(){return u.paymentAsset},getExchanges(){return u.exchanges},async fetchExchanges(){try{u.isLoading=!0,u.exchanges=(await xt({page:Tt})).exchanges.slice(0,2)}catch{throw A.showError(oe.UNABLE_TO_GET_EXCHANGES),new y(f.UNABLE_TO_GET_EXCHANGES)}finally{u.isLoading=!1}},async getAvailableExchanges(e){try{const t=e?.asset&&e?.network?Ye(e.network,e.asset):void 0;return await xt({page:e?.page??Tt,asset:t,amount:e?.amount?.toString()})}catch{throw new y(f.UNABLE_TO_GET_EXCHANGES)}},async getPayUrl(e,t,i=!1){try{const r=Number(t.amount),a=await kt({exchangeId:e,asset:Ye(t.network,t.asset),amount:r.toString(),recipient:`${t.network}:${t.recipient}`});return D.sendEvent({type:"track",event:"PAY_EXCHANGE_SELECTED",properties:{source:"pay",exchange:{id:e},configuration:{network:t.network,asset:t.asset,recipient:t.recipient,amount:r},currentPayment:{type:"exchange",exchangeId:e},headless:i}}),i&&(this.initiatePayment(),D.sendEvent({type:"track",event:"PAY_INITIATED",properties:{source:"pay",paymentId:u.paymentId||Ke,configuration:{network:t.network,asset:t.asset,recipient:t.recipient,amount:r},currentPayment:{type:"exchange",exchangeId:e}}})),a}catch(r){throw r instanceof Error&&r.message.includes("is not supported")?new y(f.ASSET_NOT_SUPPORTED):new Error(r.message)}},async generateExchangeUrlForQuote({exchangeId:e,paymentAsset:t,amount:i,recipient:r}){const a=await kt({exchangeId:e,asset:Ye(t.network,t.asset),amount:i.toString(),recipient:r});u.exchangeSessionId=a.sessionId,u.exchangeUrlForQuote=a.url},async openPayUrl(e,t,i=!1){try{const r=await this.getPayUrl(e.exchangeId,t,i);if(!r)throw new y(f.UNABLE_TO_GET_PAY_URL);const a=e.openInNewTab??!0?"_blank":"_self";return F.openHref(r.url,a),r}catch(r){throw r instanceof y?u.error=r.message:u.error=oe.GENERIC_PAYMENT_ERROR,new y(f.UNABLE_TO_GET_PAY_URL)}},async onTransfer({chainNamespace:e,fromAddress:t,toAddress:i,amount:r,paymentAsset:a}){if(u.currentPayment={type:"wallet",status:"IN_PROGRESS"},!u.isPaymentInProgress)try{this.initiatePayment();const o=g.getAllRequestedCaipNetworks().find(l=>l.caipNetworkId===a.network);if(!o)throw new Error("Target network not found");const n=g.state.activeCaipNetwork;switch(V.isLowerCaseMatch(n?.caipNetworkId,o.caipNetworkId)||await g.switchActiveNetwork(o),e){case E.CHAIN.EVM:a.asset==="native"&&(u.currentPayment.result=await yi(a,e,{recipient:i,amount:r,fromAddress:t})),a.asset.startsWith("0x")&&(u.currentPayment.result=await vi(a,{recipient:i,amount:r,fromAddress:t})),u.currentPayment.status="SUCCESS";break;case E.CHAIN.SOLANA:u.currentPayment.result=await bi(e,{recipient:i,amount:r,fromAddress:t,tokenMint:a.asset==="native"?void 0:a.asset}),u.currentPayment.status="SUCCESS";break;default:throw new y(f.INVALID_CHAIN_NAMESPACE)}}catch(o){throw o instanceof y?u.error=o.message:u.error=oe.GENERIC_PAYMENT_ERROR,u.currentPayment.status="FAILED",A.showError(u.error),o}finally{u.isPaymentInProgress=!1}},async onSendTransaction(e){try{const{namespace:t,transactionStep:i}=e;p.initiatePayment();const r=g.getAllRequestedCaipNetworks().find(o=>o.caipNetworkId===u.paymentAsset?.network);if(!r)throw new Error("Target network not found");const a=g.state.activeCaipNetwork;if(V.isLowerCaseMatch(a?.caipNetworkId,r.caipNetworkId)||await g.switchActiveNetwork(r),t===E.CHAIN.EVM){const{from:o,to:n,data:l,value:_}=i.transaction;await W.sendTransaction({address:o,to:n,data:l,value:BigInt(_),chainNamespace:t})}else if(t===E.CHAIN.SOLANA){const{instructions:o}=i.transaction;await W.writeSolanaTransaction({instructions:o})}}catch(t){throw t instanceof y?u.error=t.message:u.error=oe.GENERIC_PAYMENT_ERROR,A.showError(u.error),t}finally{u.isPaymentInProgress=!1}},getExchangeById(e){return u.exchanges.find(t=>t.id===e)},validatePayConfig(e){const{paymentAsset:t,recipient:i,amount:r}=e;if(!t)throw new y(f.INVALID_PAYMENT_CONFIG);if(!i)throw new y(f.INVALID_RECIPIENT);if(!t.asset)throw new y(f.INVALID_ASSET);if(r==null||r<=0)throw new y(f.INVALID_AMOUNT)},async handlePayWithExchange(e){try{u.currentPayment={type:"exchange",exchangeId:e};const{network:t,asset:i}=u.paymentAsset,r={network:t,asset:i,amount:u.amount,recipient:u.recipient},a=await this.getPayUrl(e,r);if(!a)throw new y(f.UNABLE_TO_INITIATE_PAYMENT);return u.currentPayment.sessionId=a.sessionId,u.currentPayment.status="IN_PROGRESS",u.currentPayment.exchangeId=e,this.initiatePayment(),{url:a.url,openInNewTab:u.openInNewTab}}catch(t){return t instanceof y?u.error=t.message:u.error=oe.GENERIC_PAYMENT_ERROR,u.isPaymentInProgress=!1,A.showError(u.error),null}},async getBuyStatus(e,t){try{const i=await Ai({sessionId:t,exchangeId:e});return(i.status==="SUCCESS"||i.status==="FAILED")&&D.sendEvent({type:"track",event:i.status==="SUCCESS"?"PAY_SUCCESS":"PAY_ERROR",properties:{message:i.status==="FAILED"?F.parseError(u.error):void 0,source:"pay",paymentId:u.paymentId||Ke,configuration:{network:u.paymentAsset.network,asset:u.paymentAsset.asset,recipient:u.recipient,amount:u.amount},currentPayment:{type:"exchange",exchangeId:u.currentPayment?.exchangeId,sessionId:u.currentPayment?.sessionId,result:i.txHash}}}),i}catch{throw new y(f.UNABLE_TO_GET_BUY_STATUS)}},async fetchTokensFromEOA({caipAddress:e,caipNetwork:t,namespace:i}){if(!e)return[];const{address:r}=C.parseCaipAddress(e);let a=t;return i===E.CHAIN.EVM&&(a=void 0),await _t.getMyTokensWithBalance({address:r,caipNetwork:a})},async fetchTokensFromExchange(){if(!u.selectedExchange)return[];const e=await Ci(u.selectedExchange.id),t=Object.values(e.assets).flat();return await Promise.all(t.map(async i=>{const r=Ri(i),{chainNamespace:a}=C.parseCaipNetworkId(r.chainId);let o=r.address;if(F.isCaipAddress(o)){const{address:n}=C.parseCaipAddress(o);o=n}return r.iconUrl=await L.getImageByToken(o??"",a).catch(()=>{})??"",r}))},async fetchTokens({caipAddress:e,caipNetwork:t,namespace:i}){try{u.isFetchingTokenBalances=!0;const r=await(u.selectedExchange?this.fetchTokensFromExchange():this.fetchTokensFromEOA({caipAddress:e,caipNetwork:t,namespace:i}));u.tokenBalances={...u.tokenBalances,[i]:r}}catch(r){const a=r instanceof Error?r.message:"Unable to get token balances";A.showError(a)}finally{u.isFetchingTokenBalances=!1}},async fetchQuote({amount:e,address:t,sourceToken:i,toToken:r,recipient:a}){try{p.resetQuoteState(),u.isFetchingQuote=!0;const o=await Ei({amount:e,address:u.selectedExchange?void 0:t,sourceToken:i,toToken:r,recipient:a});if(u.selectedExchange){const n=Ze(o);if(n){const l=`${i.network}:${n.deposit.receiver}`,_=v.formatNumber(n.deposit.amount,{decimals:i.metadata.decimals??0,round:8});await p.generateExchangeUrlForQuote({exchangeId:u.selectedExchange.id,paymentAsset:i,amount:_.toString(),recipient:l})}}u.quote=o}catch(o){let n=oe.UNABLE_TO_GET_QUOTE;if(o instanceof Error&&o.cause&&o.cause instanceof Response)try{const l=await o.cause.json();l.error&&typeof l.error=="string"&&(n=l.error)}catch{}throw u.quoteError=n,A.showError(n),new y(f.UNABLE_TO_GET_QUOTE)}finally{u.isFetchingQuote=!1}},async fetchQuoteStatus({requestId:e}){try{if(e==="direct-transfer"){const i=u.selectedExchange,r=u.exchangeSessionId;if(i&&r){switch((await this.getBuyStatus(i.id,r)).status){case"IN_PROGRESS":u.quoteStatus="waiting";break;case"SUCCESS":u.quoteStatus="success",u.isPaymentInProgress=!1;break;case"FAILED":u.quoteStatus="failure",u.isPaymentInProgress=!1;break;case"UNKNOWN":u.quoteStatus="waiting";break;default:u.quoteStatus="waiting";break}return}u.quoteStatus="success";return}const{status:t}=await Ii({requestId:e});u.quoteStatus=t}catch{throw u.quoteStatus="failure",new y(f.UNABLE_TO_GET_QUOTE_STATUS)}},initiatePayment(){u.isPaymentInProgress=!0,u.paymentId=crypto.randomUUID()},initializeAnalytics(){u.analyticsSet||(u.analyticsSet=!0,this.subscribeKey("isPaymentInProgress",e=>{if(u.currentPayment?.status&&u.currentPayment.status!=="UNKNOWN"){const t={IN_PROGRESS:"PAY_INITIATED",SUCCESS:"PAY_SUCCESS",FAILED:"PAY_ERROR"}[u.currentPayment.status];D.sendEvent({type:"track",event:t,properties:{message:u.currentPayment.status==="FAILED"?F.parseError(u.error):void 0,source:"pay",paymentId:u.paymentId||Ke,configuration:{network:u.paymentAsset.network,asset:u.paymentAsset.asset,recipient:u.recipient,amount:u.amount},currentPayment:{type:u.currentPayment.type,exchangeId:u.currentPayment.exchangeId,sessionId:u.currentPayment.sessionId,result:u.currentPayment.result}}})}}))},async prepareTokenLogo(){if(!u.paymentAsset.metadata.logoURI)try{const{chainNamespace:e}=C.parseCaipNetworkId(u.paymentAsset.network),t=await L.getImageByToken(u.paymentAsset.asset,e);u.paymentAsset.metadata.logoURI=t}catch{}}},Wi=T`
  wui-separator {
    margin: var(--apkt-spacing-3) calc(var(--apkt-spacing-3) * -1) var(--apkt-spacing-2)
      calc(var(--apkt-spacing-3) * -1);
    width: calc(100% + var(--apkt-spacing-3) * 2);
  }

  .token-display {
    padding: var(--apkt-spacing-3) var(--apkt-spacing-3);
    border-radius: var(--apkt-borderRadius-5);
    background-color: var(--apkt-tokens-theme-backgroundPrimary);
    margin-top: var(--apkt-spacing-3);
    margin-bottom: var(--apkt-spacing-3);
  }

  .token-display wui-text {
    text-transform: none;
  }

  wui-loading-spinner {
    padding: var(--apkt-spacing-2);
  }

  .left-image-container {
    position: relative;
    justify-content: center;
    align-items: center;
  }

  .token-image {
    border-radius: ${({borderRadius:e})=>e.round};
    width: 40px;
    height: 40px;
  }

  .chain-image {
    position: absolute;
    width: 20px;
    height: 20px;
    bottom: -3px;
    right: -5px;
    border-radius: ${({borderRadius:e})=>e.round};
    border: 2px solid ${({tokens:e})=>e.theme.backgroundPrimary};
  }

  .payment-methods-container {
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    border-top-right-radius: ${({borderRadius:e})=>e[8]};
    border-top-left-radius: ${({borderRadius:e})=>e[8]};
  }
`,ce=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},K=class extends k{constructor(){super(),this.unsubscribe=[],this.amount=p.state.amount,this.namespace=void 0,this.paymentAsset=p.state.paymentAsset,this.activeConnectorIds=U.state.activeConnectorIds,this.caipAddress=void 0,this.exchanges=p.state.exchanges,this.isLoading=p.state.isLoading,this.initializeNamespace(),this.unsubscribe.push(p.subscribeKey("amount",t=>this.amount=t)),this.unsubscribe.push(U.subscribeKey("activeConnectorIds",t=>this.activeConnectorIds=t)),this.unsubscribe.push(p.subscribeKey("exchanges",t=>this.exchanges=t)),this.unsubscribe.push(p.subscribeKey("isLoading",t=>this.isLoading=t)),p.fetchExchanges(),p.setSelectedExchange(void 0)}disconnectedCallback(){this.unsubscribe.forEach(t=>t())}render(){return s`
      <wui-flex flexDirection="column">
        ${this.paymentDetailsTemplate()} ${this.paymentMethodsTemplate()}
      </wui-flex>
    `}paymentMethodsTemplate(){return s`
      <wui-flex flexDirection="column" padding="3" gap="2" class="payment-methods-container">
        ${this.payWithWalletTemplate()} ${this.templateSeparator()}
        ${this.templateExchangeOptions()}
      </wui-flex>
    `}initializeNamespace(){const t=g.state.activeChain;this.namespace=t,this.caipAddress=g.getAccountData(t)?.caipAddress,this.unsubscribe.push(g.subscribeChainProp("accountState",i=>{this.caipAddress=i?.caipAddress},t))}paymentDetailsTemplate(){const t=g.getAllRequestedCaipNetworks().find(i=>i.caipNetworkId===this.paymentAsset.network);return s`
      <wui-flex
        alignItems="center"
        justifyContent="space-between"
        .padding=${["6","8","6","8"]}
        gap="2"
      >
        <wui-flex alignItems="center" gap="1">
          <wui-text variant="h1-regular" color="primary">
            ${Le(this.amount||"0")}
          </wui-text>

          <wui-flex flexDirection="column">
            <wui-text variant="h6-regular" color="secondary">
              ${this.paymentAsset.metadata.symbol||"Unknown"}
            </wui-text>
            <wui-text variant="md-medium" color="secondary"
              >on ${t?.name||"Unknown"}</wui-text
            >
          </wui-flex>
        </wui-flex>

        <wui-flex class="left-image-container">
          <wui-image
            src=${x(this.paymentAsset.metadata.logoURI)}
            class="token-image"
          ></wui-image>
          <wui-image
            src=${x(L.getNetworkImage(t))}
            class="chain-image"
          ></wui-image>
        </wui-flex>
      </wui-flex>
    `}payWithWalletTemplate(){return Ni(this.paymentAsset.network)?this.caipAddress?this.connectedWalletTemplate():this.disconnectedWalletTemplate():s``}connectedWalletTemplate(){const{name:t,image:i}=this.getWalletProperties({namespace:this.namespace});return s`
      <wui-flex flexDirection="column" gap="3">
        <wui-list-item
          type="secondary"
          boxColor="foregroundSecondary"
          @click=${this.onWalletPayment}
          .boxed=${!1}
          ?chevron=${!0}
          ?fullSize=${!1}
          ?rounded=${!0}
          data-testid="wallet-payment-option"
          imageSrc=${x(i)}
          imageSize="3xl"
        >
          <wui-text variant="lg-regular" color="primary">Pay with ${t}</wui-text>
        </wui-list-item>

        <wui-list-item
          type="secondary"
          icon="power"
          iconColor="error"
          @click=${this.onDisconnect}
          data-testid="disconnect-button"
          ?chevron=${!1}
          boxColor="foregroundSecondary"
        >
          <wui-text variant="lg-regular" color="secondary">Disconnect</wui-text>
        </wui-list-item>
      </wui-flex>
    `}disconnectedWalletTemplate(){return s`<wui-list-item
      type="secondary"
      boxColor="foregroundSecondary"
      variant="icon"
      iconColor="default"
      iconVariant="overlay"
      icon="wallet"
      @click=${this.onWalletPayment}
      ?chevron=${!0}
      data-testid="wallet-payment-option"
    >
      <wui-text variant="lg-regular" color="primary">Pay with wallet</wui-text>
    </wui-list-item>`}templateExchangeOptions(){if(this.isLoading)return s`<wui-flex justifyContent="center" alignItems="center">
        <wui-loading-spinner size="md"></wui-loading-spinner>
      </wui-flex>`;const t=this.exchanges.filter(i=>Oi(this.paymentAsset)?i.id===bt:i.id!==bt);return t.length===0?s`<wui-flex justifyContent="center" alignItems="center">
        <wui-text variant="md-medium" color="primary">No exchanges available</wui-text>
      </wui-flex>`:t.map(i=>s`
        <wui-list-item
          type="secondary"
          boxColor="foregroundSecondary"
          @click=${()=>this.onExchangePayment(i)}
          data-testid="exchange-option-${i.id}"
          ?chevron=${!0}
          imageSrc=${x(i.imageUrl)}
        >
          <wui-text flexGrow="1" variant="lg-regular" color="primary">
            Pay with ${i.name}
          </wui-text>
        </wui-list-item>
      `)}templateSeparator(){return s`<wui-separator text="or" bgColor="secondary"></wui-separator>`}async onWalletPayment(){if(!this.namespace)throw new Error("Namespace not found");this.caipAddress?m.push("PayQuote"):(await U.connect(),await O.open({view:"PayQuote"}))}onExchangePayment(t){p.setSelectedExchange(t),m.push("PayQuote")}async onDisconnect(){try{await W.disconnect(),await O.open({view:"Pay"})}catch{console.error("Failed to disconnect"),A.showError("Failed to disconnect")}}getWalletProperties({namespace:t}){if(!t)return{name:void 0,image:void 0};const i=this.activeConnectorIds[t];if(!i)return{name:void 0,image:void 0};const r=U.getConnector({id:i,namespace:t});if(!r)return{name:void 0,image:void 0};const a=L.getConnectorImage(r);return{name:r.name,image:a}}};K.styles=Wi;ce([h()],K.prototype,"amount",void 0);ce([h()],K.prototype,"namespace",void 0);ce([h()],K.prototype,"paymentAsset",void 0);ce([h()],K.prototype,"activeConnectorIds",void 0);ce([h()],K.prototype,"caipAddress",void 0);ce([h()],K.prototype,"exchanges",void 0);ce([h()],K.prototype,"isLoading",void 0);K=ce([b("w3m-pay-view")],K);var Di=T`
  :host {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .pulse-container {
    position: relative;
    width: var(--pulse-size);
    height: var(--pulse-size);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .pulse-rings {
    position: absolute;
    inset: 0;
    pointer-events: none;
  }

  .pulse-ring {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 2px solid var(--pulse-color);
    opacity: 0;
    animation: pulse var(--pulse-duration, 2s) ease-out infinite;
  }

  .pulse-content {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  @keyframes pulse {
    0% {
      transform: scale(0.5);
      opacity: var(--pulse-opacity, 0.3);
    }
    50% {
      opacity: calc(var(--pulse-opacity, 0.3) * 0.5);
    }
    100% {
      transform: scale(1.2);
      opacity: 0;
    }
  }
`,ge=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},Li=3,Bi=2,zi=.3,Fi="200px",ji={"accent-primary":xe.tokens.core.backgroundAccentPrimary},ne=class extends k{constructor(){super(...arguments),this.rings=Li,this.duration=Bi,this.opacity=zi,this.size=Fi,this.variant="accent-primary"}render(){const t=ji[this.variant];return this.style.cssText=`
      --pulse-size: ${this.size};
      --pulse-duration: ${this.duration}s;
      --pulse-color: ${t};
      --pulse-opacity: ${this.opacity};
    `,s`
      <div class="pulse-container">
        <div class="pulse-rings">${Array.from({length:this.rings},(i,r)=>this.renderRing(r,this.rings))}</div>
        <div class="pulse-content">
          <slot></slot>
        </div>
      </div>
    `}renderRing(t,i){return s`<div class="pulse-ring" style=${`animation-delay: ${t/i*this.duration}s;`}></div>`}};ne.styles=[X,Di];ge([d({type:Number})],ne.prototype,"rings",void 0);ge([d({type:Number})],ne.prototype,"duration",void 0);ge([d({type:Number})],ne.prototype,"opacity",void 0);ge([d()],ne.prototype,"size",void 0);ge([d()],ne.prototype,"variant",void 0);ne=ge([b("wui-pulse")],ne);var St=[{id:"received",title:"Receiving funds",icon:"dollar"},{id:"processing",title:"Swapping asset",icon:"recycleHorizontal"},{id:"sending",title:"Sending asset to the recipient address",icon:"send"}],Et=["success","submitted","failure","timeout","refund"],Mi=T`
  :host {
    display: block;
    height: 100%;
    width: 100%;
  }

  wui-image {
    border-radius: ${({borderRadius:e})=>e.round};
  }

  .token-badge-container {
    position: absolute;
    bottom: 6px;
    left: 50%;
    transform: translateX(-50%);
    border-radius: ${({borderRadius:e})=>e[4]};
    z-index: 3;
    min-width: 105px;
  }

  .token-badge-container.loading {
    background-color: ${({tokens:e})=>e.theme.backgroundPrimary};
    border: 3px solid ${({tokens:e})=>e.theme.backgroundPrimary};
  }

  .token-badge-container.success {
    background-color: ${({tokens:e})=>e.theme.backgroundPrimary};
    border: 3px solid ${({tokens:e})=>e.theme.backgroundPrimary};
  }

  .token-image-container {
    position: relative;
  }

  .token-image {
    border-radius: ${({borderRadius:e})=>e.round};
    width: 64px;
    height: 64px;
  }

  .token-image.success {
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
  }

  .token-image.error {
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
  }

  .token-image.loading {
    background: ${({colors:e})=>e.accent010};
  }

  .token-image wui-icon {
    width: 32px;
    height: 32px;
  }

  .token-badge {
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    border: 1px solid ${({tokens:e})=>e.theme.foregroundSecondary};
    border-radius: ${({borderRadius:e})=>e[4]};
  }

  .token-badge wui-text {
    white-space: nowrap;
  }

  .payment-lifecycle-container {
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    border-top-right-radius: ${({borderRadius:e})=>e[6]};
    border-top-left-radius: ${({borderRadius:e})=>e[6]};
  }

  .payment-step-badge {
    padding: ${({spacing:e})=>e[1]} ${({spacing:e})=>e[2]};
    border-radius: ${({borderRadius:e})=>e[1]};
  }

  .payment-step-badge.loading {
    background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
  }

  .payment-step-badge.error {
    background-color: ${({tokens:e})=>e.core.backgroundError};
  }

  .payment-step-badge.success {
    background-color: ${({tokens:e})=>e.core.backgroundSuccess};
  }

  .step-icon-container {
    position: relative;
    height: 40px;
    width: 40px;
    border-radius: ${({borderRadius:e})=>e.round};
    background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
  }

  .step-icon-box {
    position: absolute;
    right: -4px;
    bottom: -1px;
    padding: 2px;
    border-radius: ${({borderRadius:e})=>e.round};
    border: 2px solid ${({tokens:e})=>e.theme.backgroundPrimary};
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
  }

  .step-icon-box.success {
    background-color: ${({tokens:e})=>e.core.backgroundSuccess};
  }
`,Z=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},qi={received:["pending","success","submitted"],processing:["success","submitted"],sending:["success","submitted"]},Vi=3e3,j=class extends k{constructor(){super(),this.unsubscribe=[],this.pollingInterval=null,this.paymentAsset=p.state.paymentAsset,this.quoteStatus=p.state.quoteStatus,this.quote=p.state.quote,this.amount=p.state.amount,this.namespace=void 0,this.caipAddress=void 0,this.profileName=null,this.activeConnectorIds=U.state.activeConnectorIds,this.selectedExchange=p.state.selectedExchange,this.initializeNamespace(),this.unsubscribe.push(p.subscribeKey("quoteStatus",t=>this.quoteStatus=t),p.subscribeKey("quote",t=>this.quote=t),U.subscribeKey("activeConnectorIds",t=>this.activeConnectorIds=t),p.subscribeKey("selectedExchange",t=>this.selectedExchange=t))}connectedCallback(){super.connectedCallback(),this.startPolling()}disconnectedCallback(){super.disconnectedCallback(),this.stopPolling(),this.unsubscribe.forEach(t=>t())}render(){return s`
      <wui-flex flexDirection="column" .padding=${["3","0","0","0"]} gap="2">
        ${this.tokenTemplate()} ${this.paymentTemplate()} ${this.paymentLifecycleTemplate()}
      </wui-flex>
    `}tokenTemplate(){const t=Le(this.amount||"0"),i=this.paymentAsset.metadata.symbol??"Unknown",r=g.getAllRequestedCaipNetworks().find(o=>o.caipNetworkId===this.paymentAsset.network),a=this.quoteStatus==="failure"||this.quoteStatus==="timeout"||this.quoteStatus==="refund";return this.quoteStatus==="success"||this.quoteStatus==="submitted"?s`<wui-flex alignItems="center" justifyContent="center">
        <wui-flex justifyContent="center" alignItems="center" class="token-image success">
          <wui-icon name="checkmark" color="success" size="inherit"></wui-icon>
        </wui-flex>
      </wui-flex>`:a?s`<wui-flex alignItems="center" justifyContent="center">
        <wui-flex justifyContent="center" alignItems="center" class="token-image error">
          <wui-icon name="close" color="error" size="inherit"></wui-icon>
        </wui-flex>
      </wui-flex>`:s`
      <wui-flex alignItems="center" justifyContent="center">
        <wui-flex class="token-image-container">
          <wui-pulse size="125px" rings="3" duration="4" opacity="0.5" variant="accent-primary">
            <wui-flex justifyContent="center" alignItems="center" class="token-image loading">
              <wui-icon name="paperPlaneTitle" color="accent-primary" size="inherit"></wui-icon>
            </wui-flex>
          </wui-pulse>

          <wui-flex
            justifyContent="center"
            alignItems="center"
            class="token-badge-container loading"
          >
            <wui-flex
              alignItems="center"
              justifyContent="center"
              gap="01"
              padding="1"
              class="token-badge"
            >
              <wui-image
                src=${x(L.getNetworkImage(r))}
                class="chain-image"
                size="mdl"
              ></wui-image>

              <wui-text variant="lg-regular" color="primary">${t} ${i}</wui-text>
            </wui-flex>
          </wui-flex>
        </wui-flex>
      </wui-flex>
    `}paymentTemplate(){return s`
      <wui-flex flexDirection="column" gap="2" .padding=${["0","6","0","6"]}>
        ${this.renderPayment()}
        <wui-separator></wui-separator>
        ${this.renderWallet()}
      </wui-flex>
    `}paymentLifecycleTemplate(){const t=this.getStepsWithStatus();return s`
      <wui-flex flexDirection="column" padding="4" gap="2" class="payment-lifecycle-container">
        <wui-flex alignItems="center" justifyContent="space-between">
          <wui-text variant="md-regular" color="secondary">PAYMENT CYCLE</wui-text>

          ${this.renderPaymentCycleBadge()}
        </wui-flex>

        <wui-flex flexDirection="column" gap="5" .padding=${["2","0","2","0"]}>
          ${t.map(i=>this.renderStep(i))}
        </wui-flex>
      </wui-flex>
    `}renderPaymentCycleBadge(){const t=this.quoteStatus==="failure"||this.quoteStatus==="timeout"||this.quoteStatus==="refund",i=this.quoteStatus==="success"||this.quoteStatus==="submitted";return t?s`
        <wui-flex
          justifyContent="center"
          alignItems="center"
          class="payment-step-badge error"
          gap="1"
        >
          <wui-icon name="close" color="error" size="xs"></wui-icon>
          <wui-text variant="sm-regular" color="error">Failed</wui-text>
        </wui-flex>
      `:i?s`
        <wui-flex
          justifyContent="center"
          alignItems="center"
          class="payment-step-badge success"
          gap="1"
        >
          <wui-icon name="checkmark" color="success" size="xs"></wui-icon>
          <wui-text variant="sm-regular" color="success">Completed</wui-text>
        </wui-flex>
      `:s`
      <wui-flex alignItems="center" justifyContent="space-between" gap="3">
        <wui-flex
          justifyContent="center"
          alignItems="center"
          class="payment-step-badge loading"
          gap="1"
        >
          <wui-icon name="clock" color="default" size="xs"></wui-icon>
          <wui-text variant="sm-regular" color="primary">Est. ${this.quote?.timeInSeconds??0} sec</wui-text>
        </wui-flex>

        <wui-icon name="chevronBottom" color="default" size="xxs"></wui-icon>
      </wui-flex>
    `}renderPayment(){const t=g.getAllRequestedCaipNetworks().find(i=>{const r=this.quote?.origin.currency.network;if(!r)return!1;const{chainId:a}=C.parseCaipNetworkId(r);return V.isLowerCaseMatch(i.id.toString(),a.toString())});return s`
      <wui-flex
        alignItems="flex-start"
        justifyContent="space-between"
        .padding=${["3","0","3","0"]}
      >
        <wui-text variant="lg-regular" color="secondary">Payment Method</wui-text>

        <wui-flex flexDirection="column" alignItems="flex-end" gap="1">
          <wui-flex alignItems="center" gap="01">
            <wui-text variant="lg-regular" color="primary">${Le(v.formatNumber(this.quote?.origin.amount||"0",{decimals:this.quote?.origin.currency.metadata.decimals??0}).toString())}</wui-text>
            <wui-text variant="lg-regular" color="secondary">${this.quote?.origin.currency.metadata.symbol??"Unknown"}</wui-text>
          </wui-flex>

          <wui-flex alignItems="center" gap="1">
            <wui-text variant="md-regular" color="secondary">on</wui-text>
            <wui-image
              src=${x(L.getNetworkImage(t))}
              size="xs"
            ></wui-image>
            <wui-text variant="md-regular" color="secondary">${t?.name}</wui-text>
          </wui-flex>
        </wui-flex>
      </wui-flex>
    `}renderWallet(){return s`
      <wui-flex
        alignItems="flex-start"
        justifyContent="space-between"
        .padding=${["3","0","3","0"]}
      >
        <wui-text variant="lg-regular" color="secondary">Wallet</wui-text>

        ${this.renderWalletText()}
      </wui-flex>
    `}renderWalletText(){const{image:t}=this.getWalletProperties({namespace:this.namespace}),{address:i}=this.caipAddress?C.parseCaipAddress(this.caipAddress):{},r=this.selectedExchange?.name;return this.selectedExchange?s`
        <wui-flex alignItems="center" justifyContent="flex-end" gap="1">
          <wui-text variant="lg-regular" color="primary">${r}</wui-text>
          <wui-image src=${x(this.selectedExchange.imageUrl)} size="mdl"></wui-image>
        </wui-flex>
      `:s`
      <wui-flex alignItems="center" justifyContent="flex-end" gap="1">
        <wui-text variant="lg-regular" color="primary">
          ${Ve.getTruncateString({string:this.profileName||i||r||"",charsStart:this.profileName?16:4,charsEnd:this.profileName?0:6,truncate:this.profileName?"end":"middle"})}
        </wui-text>

        <wui-image src=${x(t)} size="mdl"></wui-image>
      </wui-flex>
    `}getStepsWithStatus(){return this.quoteStatus==="failure"||this.quoteStatus==="timeout"||this.quoteStatus==="refund"?St.map(t=>({...t,status:"failed"})):St.map(t=>{const i=(qi[t.id]??[]).includes(this.quoteStatus)?"completed":"pending";return{...t,status:i}})}renderStep({title:t,icon:i,status:r}){return s`
      <wui-flex alignItems="center" gap="3">
        <wui-flex justifyContent="center" alignItems="center" class="step-icon-container">
          <wui-icon name=${i} color="default" size="mdl"></wui-icon>

          <wui-flex alignItems="center" justifyContent="center" class=${Ot({"step-icon-box":!0,success:r==="completed"})}>
            ${this.renderStatusIndicator(r)}
          </wui-flex>
        </wui-flex>

        <wui-text variant="md-regular" color="primary">${t}</wui-text>
      </wui-flex>
    `}renderStatusIndicator(t){return t==="completed"?s`<wui-icon size="sm" color="success" name="checkmark"></wui-icon>`:t==="failed"?s`<wui-icon size="sm" color="error" name="close"></wui-icon>`:t==="pending"?s`<wui-loading-spinner color="accent-primary" size="sm"></wui-loading-spinner>`:null}startPolling(){this.pollingInterval||(this.fetchQuoteStatus(),this.pollingInterval=setInterval(()=>{this.fetchQuoteStatus()},Vi))}stopPolling(){this.pollingInterval&&(clearInterval(this.pollingInterval),this.pollingInterval=null)}async fetchQuoteStatus(){const t=p.state.requestId;if(!t||Et.includes(this.quoteStatus))this.stopPolling();else try{await p.fetchQuoteStatus({requestId:t}),Et.includes(this.quoteStatus)&&this.stopPolling()}catch{this.stopPolling()}}initializeNamespace(){const t=g.state.activeChain;this.namespace=t,this.caipAddress=g.getAccountData(t)?.caipAddress,this.profileName=g.getAccountData(t)?.profileName??null,this.unsubscribe.push(g.subscribeChainProp("accountState",i=>{this.caipAddress=i?.caipAddress,this.profileName=i?.profileName??null},t))}getWalletProperties({namespace:t}){if(!t)return{name:void 0,image:void 0};const i=this.activeConnectorIds[t];if(!i)return{name:void 0,image:void 0};const r=U.getConnector({id:i,namespace:t});if(!r)return{name:void 0,image:void 0};const a=L.getConnectorImage(r);return{name:r.name,image:a}}};j.styles=Mi;Z([h()],j.prototype,"paymentAsset",void 0);Z([h()],j.prototype,"quoteStatus",void 0);Z([h()],j.prototype,"quote",void 0);Z([h()],j.prototype,"amount",void 0);Z([h()],j.prototype,"namespace",void 0);Z([h()],j.prototype,"caipAddress",void 0);Z([h()],j.prototype,"profileName",void 0);Z([h()],j.prototype,"activeConnectorIds",void 0);Z([h()],j.prototype,"selectedExchange",void 0);j=Z([b("w3m-pay-loading-view")],j);var Hi=T`
  button {
    display: flex;
    align-items: center;
    height: 40px;
    padding: ${({spacing:e})=>e[2]};
    border-radius: ${({borderRadius:e})=>e[4]};
    column-gap: ${({spacing:e})=>e[1]};
    background-color: transparent;
    transition: background-color ${({durations:e})=>e.lg}
      ${({easings:e})=>e["ease-out-power-2"]};
    will-change: background-color;
  }

  wui-image,
  .icon-box {
    width: ${({spacing:e})=>e[6]};
    height: ${({spacing:e})=>e[6]};
    border-radius: ${({borderRadius:e})=>e[4]};
  }

  wui-text {
    flex: 1;
  }

  .icon-box {
    position: relative;
  }

  .icon-box[data-active='true'] {
    background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
  }

  .circle {
    position: absolute;
    left: 16px;
    top: 15px;
    width: 8px;
    height: 8px;
    background-color: ${({tokens:e})=>e.core.textSuccess};
    box-shadow: 0 0 0 2px ${({tokens:e})=>e.theme.foregroundPrimary};
    border-radius: 50%;
  }

  /* -- Hover & Active states ----------------------------------------------------------- */
  @media (hover: hover) {
    button:hover:enabled,
    button:active:enabled {
      background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    }
  }
`,H=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},B=class extends k{constructor(){super(...arguments),this.address="",this.profileName="",this.alt="",this.imageSrc="",this.icon=void 0,this.iconSize="md",this.enableGreenCircle=!0,this.loading=!1,this.charsStart=4,this.charsEnd=6}render(){return s`
      <button>
        ${this.leftImageTemplate()} ${this.textTemplate()} ${this.rightImageTemplate()}
      </button>
    `}leftImageTemplate(){const t=this.icon?s`<wui-icon
          size=${x(this.iconSize)}
          color="default"
          name=${this.icon}
          class="icon"
        ></wui-icon>`:s`<wui-image src=${this.imageSrc} alt=${this.alt}></wui-image>`;return s`
      <wui-flex
        alignItems="center"
        justifyContent="center"
        class="icon-box"
        data-active=${!!this.icon}
      >
        ${t}
        ${this.enableGreenCircle?s`<wui-flex class="circle"></wui-flex>`:null}
      </wui-flex>
    `}textTemplate(){return s`
      <wui-text variant="lg-regular" color="primary">
        ${Ve.getTruncateString({string:this.profileName||this.address,charsStart:this.profileName?16:this.charsStart,charsEnd:this.profileName?0:this.charsEnd,truncate:this.profileName?"end":"middle"})}
      </wui-text>
    `}rightImageTemplate(){return s`<wui-icon name="chevronBottom" size="sm" color="default"></wui-icon>`}};B.styles=[X,qe,Hi];H([d()],B.prototype,"address",void 0);H([d()],B.prototype,"profileName",void 0);H([d()],B.prototype,"alt",void 0);H([d()],B.prototype,"imageSrc",void 0);H([d()],B.prototype,"icon",void 0);H([d()],B.prototype,"iconSize",void 0);H([d({type:Boolean})],B.prototype,"enableGreenCircle",void 0);H([d({type:Boolean})],B.prototype,"loading",void 0);H([d({type:Number})],B.prototype,"charsStart",void 0);H([d({type:Number})],B.prototype,"charsEnd",void 0);B=H([b("wui-wallet-switch")],B);var Gi=Me`
  :host {
    display: block;
  }
`,Yi=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},Je=class extends k{render(){return s`
      <wui-flex flexDirection="column" gap="4">
        <wui-flex alignItems="center" justifyContent="space-between">
          <wui-text variant="md-regular" color="secondary">Pay</wui-text>
          <wui-shimmer width="60px" height="16px" borderRadius="4xs" variant="light"></wui-shimmer>
        </wui-flex>

        <wui-flex alignItems="center" justifyContent="space-between">
          <wui-text variant="md-regular" color="secondary">Network Fee</wui-text>

          <wui-flex flexDirection="column" alignItems="flex-end" gap="2">
            <wui-shimmer
              width="75px"
              height="16px"
              borderRadius="4xs"
              variant="light"
            ></wui-shimmer>

            <wui-flex alignItems="center" gap="01">
              <wui-shimmer width="14px" height="14px" rounded variant="light"></wui-shimmer>
              <wui-shimmer
                width="49px"
                height="14px"
                borderRadius="4xs"
                variant="light"
              ></wui-shimmer>
            </wui-flex>
          </wui-flex>
        </wui-flex>

        <wui-flex alignItems="center" justifyContent="space-between">
          <wui-text variant="md-regular" color="secondary">Service Fee</wui-text>
          <wui-shimmer width="75px" height="16px" borderRadius="4xs" variant="light"></wui-shimmer>
        </wui-flex>
      </wui-flex>
    `}};Je.styles=[Gi];Je=Yi([b("w3m-pay-fees-skeleton")],Je);var Ki=T`
  :host {
    display: block;
  }

  wui-image {
    border-radius: ${({borderRadius:e})=>e.round};
  }
`,Bt=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},Be=class extends k{constructor(){super(),this.unsubscribe=[],this.quote=p.state.quote,this.unsubscribe.push(p.subscribeKey("quote",t=>this.quote=t))}disconnectedCallback(){this.unsubscribe.forEach(t=>t())}render(){return s`
      <wui-flex flexDirection="column" gap="4">
        <wui-flex alignItems="center" justifyContent="space-between">
          <wui-text variant="md-regular" color="secondary">Pay</wui-text>
          <wui-text variant="md-regular" color="primary">
            ${v.formatNumber(this.quote?.origin.amount||"0",{decimals:this.quote?.origin.currency.metadata.decimals??0,round:6}).toString()} ${this.quote?.origin.currency.metadata.symbol||"Unknown"}
          </wui-text>
        </wui-flex>

        ${this.quote&&this.quote.fees.length>0?this.quote.fees.map(t=>this.renderFee(t)):null}
      </wui-flex>
    `}renderFee(t){const i=t.id==="network",r=v.formatNumber(t.amount||"0",{decimals:t.currency.metadata.decimals??0,round:6}).toString();if(i){const a=g.getAllRequestedCaipNetworks().find(o=>V.isLowerCaseMatch(o.caipNetworkId,t.currency.network));return s`
        <wui-flex alignItems="center" justifyContent="space-between">
          <wui-text variant="md-regular" color="secondary">${t.label}</wui-text>

          <wui-flex flexDirection="column" alignItems="flex-end" gap="2">
            <wui-text variant="md-regular" color="primary">
              ${r} ${t.currency.metadata.symbol||"Unknown"}
            </wui-text>

            <wui-flex alignItems="center" gap="01">
              <wui-image
                src=${x(L.getNetworkImage(a))}
                size="xs"
              ></wui-image>
              <wui-text variant="sm-regular" color="secondary">
                ${a?.name||"Unknown"}
              </wui-text>
            </wui-flex>
          </wui-flex>
        </wui-flex>
      `}return s`
      <wui-flex alignItems="center" justifyContent="space-between">
        <wui-text variant="md-regular" color="secondary">${t.label}</wui-text>
        <wui-text variant="md-regular" color="primary">
          ${r} ${t.currency.metadata.symbol||"Unknown"}
        </wui-text>
      </wui-flex>
    `}};Be.styles=[Ki];Bt([h()],Be.prototype,"quote",void 0);Be=Bt([b("w3m-pay-fees")],Be);var Qi=T`
  :host {
    display: block;
    width: 100%;
  }

  .disabled-container {
    padding: ${({spacing:e})=>e[2]};
    min-height: 168px;
  }

  wui-icon {
    width: ${({spacing:e})=>e[8]};
    height: ${({spacing:e})=>e[8]};
  }

  wui-flex > wui-text {
    max-width: 273px;
  }
`,zt=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},ze=class extends k{constructor(){super(),this.unsubscribe=[],this.selectedExchange=p.state.selectedExchange,this.unsubscribe.push(p.subscribeKey("selectedExchange",t=>this.selectedExchange=t))}disconnectedCallback(){this.unsubscribe.forEach(t=>t())}render(){return s`
      <wui-flex
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        gap="3"
        class="disabled-container"
      >
        <wui-icon name="coins" color="default" size="inherit"></wui-icon>

        <wui-text variant="md-regular" color="primary" align="center">
          You don't have enough funds to complete this transaction
        </wui-text>

        ${this.selectedExchange?null:s`<wui-button
              size="md"
              variant="neutral-secondary"
              @click=${this.dispatchConnectOtherWalletEvent.bind(this)}
              >Connect other wallet</wui-button
            >`}
      </wui-flex>
    `}dispatchConnectOtherWalletEvent(){this.dispatchEvent(new CustomEvent("connectOtherWallet",{detail:!0,bubbles:!0,composed:!0}))}};ze.styles=[Qi];zt([d({type:Array})],ze.prototype,"selectedExchange",void 0);ze=zt([b("w3m-pay-options-empty")],ze);var Xi=T`
  :host {
    display: block;
    width: 100%;
  }

  .pay-options-container {
    max-height: 196px;
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-width: none;
  }

  .pay-options-container::-webkit-scrollbar {
    display: none;
  }

  .pay-option-container {
    border-radius: ${({borderRadius:e})=>e[4]};
    padding: ${({spacing:e})=>e[3]};
    min-height: 60px;
  }

  .token-images-container {
    position: relative;
    justify-content: center;
    align-items: center;
  }

  .chain-image {
    position: absolute;
    bottom: -3px;
    right: -5px;
    border: 2px solid ${({tokens:e})=>e.theme.foregroundSecondary};
  }
`,Zi=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},et=class extends k{render(){return s`
      <wui-flex flexDirection="column" gap="2" class="pay-options-container">
        ${this.renderOptionEntry()} ${this.renderOptionEntry()} ${this.renderOptionEntry()}
      </wui-flex>
    `}renderOptionEntry(){return s`
      <wui-flex
        alignItems="center"
        justifyContent="space-between"
        gap="2"
        class="pay-option-container"
      >
        <wui-flex alignItems="center" gap="2">
          <wui-flex class="token-images-container">
            <wui-shimmer
              width="32px"
              height="32px"
              rounded
              variant="light"
              class="token-image"
            ></wui-shimmer>
            <wui-shimmer
              width="16px"
              height="16px"
              rounded
              variant="light"
              class="chain-image"
            ></wui-shimmer>
          </wui-flex>

          <wui-flex flexDirection="column" gap="1">
            <wui-shimmer
              width="74px"
              height="16px"
              borderRadius="4xs"
              variant="light"
            ></wui-shimmer>
            <wui-shimmer
              width="46px"
              height="14px"
              borderRadius="4xs"
              variant="light"
            ></wui-shimmer>
          </wui-flex>
        </wui-flex>
      </wui-flex>
    `}};et.styles=[Xi];et=Zi([b("w3m-pay-options-skeleton")],et);var Ji=T`
  :host {
    display: block;
    width: 100%;
  }

  .pay-options-container {
    max-height: 196px;
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-width: none;
    mask-image: var(--options-mask-image);
    -webkit-mask-image: var(--options-mask-image);
  }

  .pay-options-container::-webkit-scrollbar {
    display: none;
  }

  .pay-option-container {
    cursor: pointer;
    border-radius: ${({borderRadius:e})=>e[4]};
    padding: ${({spacing:e})=>e[3]};
    transition: background-color ${({durations:e})=>e.lg}
      ${({easings:e})=>e["ease-out-power-1"]};
    will-change: background-color;
  }

  .token-images-container {
    position: relative;
    justify-content: center;
    align-items: center;
  }

  .token-image {
    border-radius: ${({borderRadius:e})=>e.round};
    width: 32px;
    height: 32px;
  }

  .chain-image {
    position: absolute;
    width: 16px;
    height: 16px;
    bottom: -3px;
    right: -5px;
    border-radius: ${({borderRadius:e})=>e.round};
    border: 2px solid ${({tokens:e})=>e.theme.backgroundPrimary};
  }

  @media (hover: hover) and (pointer: fine) {
    .pay-option-container:hover {
      background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    }
  }
`,He=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},eo=300,he=class extends k{constructor(){super(),this.unsubscribe=[],this.options=[],this.selectedPaymentAsset=null}disconnectedCallback(){this.unsubscribe.forEach(t=>t()),this.resizeObserver?.disconnect(),this.shadowRoot?.querySelector(".pay-options-container")?.removeEventListener("scroll",this.handleOptionsListScroll.bind(this))}firstUpdated(){const t=this.shadowRoot?.querySelector(".pay-options-container");t&&(requestAnimationFrame(this.handleOptionsListScroll.bind(this)),t?.addEventListener("scroll",this.handleOptionsListScroll.bind(this)),this.resizeObserver=new ResizeObserver(()=>{this.handleOptionsListScroll()}),this.resizeObserver?.observe(t),this.handleOptionsListScroll())}render(){return s`
      <wui-flex flexDirection="column" gap="2" class="pay-options-container">
        ${this.options.map(t=>this.payOptionTemplate(t))}
      </wui-flex>
    `}payOptionTemplate(t){const{network:i,metadata:r,asset:a,amount:o="0"}=t,n=g.getAllRequestedCaipNetworks().find(Ne=>Ne.caipNetworkId===i),l=`${i}:${a}`==`${this.selectedPaymentAsset?.network}:${this.selectedPaymentAsset?.asset}`,_=v.bigNumber(o,{safe:!0}),$e=_.gt(0);return s`
      <wui-flex
        alignItems="center"
        justifyContent="space-between"
        gap="2"
        @click=${()=>this.onSelect?.(t)}
        class="pay-option-container"
      >
        <wui-flex alignItems="center" gap="2">
          <wui-flex class="token-images-container">
            <wui-image
              src=${x(r.logoURI)}
              class="token-image"
              size="3xl"
            ></wui-image>
            <wui-image
              src=${x(L.getNetworkImage(n))}
              class="chain-image"
              size="md"
            ></wui-image>
          </wui-flex>

          <wui-flex flexDirection="column" gap="1">
            <wui-text variant="lg-regular" color="primary">${r.symbol}</wui-text>
            ${$e?s`<wui-text variant="sm-regular" color="secondary">
                  ${_.round(6).toString()} ${r.symbol}
                </wui-text>`:null}
          </wui-flex>
        </wui-flex>

        ${l?s`<wui-icon name="checkmark" size="md" color="success"></wui-icon>`:null}
      </wui-flex>
    `}handleOptionsListScroll(){const t=this.shadowRoot?.querySelector(".pay-options-container");t&&(t.scrollHeight>eo?(t.style.setProperty("--options-mask-image",`linear-gradient(
          to bottom,
          rgba(0, 0, 0, calc(1 - var(--options-scroll--top-opacity))) 0px,
          rgba(200, 200, 200, calc(1 - var(--options-scroll--top-opacity))) 1px,
          black 50px,
          black calc(100% - 50px),
          rgba(155, 155, 155, calc(1 - var(--options-scroll--bottom-opacity))) calc(100% - 1px),
          rgba(0, 0, 0, calc(1 - var(--options-scroll--bottom-opacity))) 100%
        )`),t.style.setProperty("--options-scroll--top-opacity",yt.interpolate([0,50],[0,1],t.scrollTop).toString()),t.style.setProperty("--options-scroll--bottom-opacity",yt.interpolate([0,50],[0,1],t.scrollHeight-t.scrollTop-t.offsetHeight).toString())):(t.style.setProperty("--options-mask-image","none"),t.style.setProperty("--options-scroll--top-opacity","0"),t.style.setProperty("--options-scroll--bottom-opacity","0")))}};he.styles=[Ji];He([d({type:Array})],he.prototype,"options",void 0);He([d()],he.prototype,"selectedPaymentAsset",void 0);He([d()],he.prototype,"onSelect",void 0);he=He([b("w3m-pay-options")],he);var to=T`
  .payment-methods-container {
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    border-top-right-radius: ${({borderRadius:e})=>e[5]};
    border-top-left-radius: ${({borderRadius:e})=>e[5]};
  }

  .pay-options-container {
    background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
    border-radius: ${({borderRadius:e})=>e[5]};
    padding: ${({spacing:e})=>e[1]};
  }

  w3m-tooltip-trigger {
    display: flex;
    align-items: center;
    justify-content: center;
    max-width: fit-content;
  }

  wui-image {
    border-radius: ${({borderRadius:e})=>e.round};
  }

  w3m-pay-options.disabled {
    opacity: 0.5;
    pointer-events: none;
  }
`,$=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},Re={eip155:"ethereum",solana:"solana",bip122:"bitcoin",ton:"ton"},io={eip155:{icon:Re.eip155,label:"EVM"},solana:{icon:Re.solana,label:"Solana"},bip122:{icon:Re.bip122,label:"Bitcoin"},ton:{icon:Re.ton,label:"Ton"}},I=class extends k{constructor(){super(),this.unsubscribe=[],this.profileName=null,this.paymentAsset=p.state.paymentAsset,this.namespace=void 0,this.caipAddress=void 0,this.amount=p.state.amount,this.recipient=p.state.recipient,this.activeConnectorIds=U.state.activeConnectorIds,this.selectedPaymentAsset=p.state.selectedPaymentAsset,this.selectedExchange=p.state.selectedExchange,this.isFetchingQuote=p.state.isFetchingQuote,this.quoteError=p.state.quoteError,this.quote=p.state.quote,this.isFetchingTokenBalances=p.state.isFetchingTokenBalances,this.tokenBalances=p.state.tokenBalances,this.isPaymentInProgress=p.state.isPaymentInProgress,this.exchangeUrlForQuote=p.state.exchangeUrlForQuote,this.completedTransactionsCount=0,this.unsubscribe.push(p.subscribeKey("paymentAsset",t=>this.paymentAsset=t)),this.unsubscribe.push(p.subscribeKey("tokenBalances",t=>this.onTokenBalancesChanged(t))),this.unsubscribe.push(p.subscribeKey("isFetchingTokenBalances",t=>this.isFetchingTokenBalances=t)),this.unsubscribe.push(U.subscribeKey("activeConnectorIds",t=>this.activeConnectorIds=t)),this.unsubscribe.push(p.subscribeKey("selectedPaymentAsset",t=>this.selectedPaymentAsset=t)),this.unsubscribe.push(p.subscribeKey("isFetchingQuote",t=>this.isFetchingQuote=t)),this.unsubscribe.push(p.subscribeKey("quoteError",t=>this.quoteError=t)),this.unsubscribe.push(p.subscribeKey("quote",t=>this.quote=t)),this.unsubscribe.push(p.subscribeKey("amount",t=>this.amount=t)),this.unsubscribe.push(p.subscribeKey("recipient",t=>this.recipient=t)),this.unsubscribe.push(p.subscribeKey("isPaymentInProgress",t=>this.isPaymentInProgress=t)),this.unsubscribe.push(p.subscribeKey("selectedExchange",t=>this.selectedExchange=t)),this.unsubscribe.push(p.subscribeKey("exchangeUrlForQuote",t=>this.exchangeUrlForQuote=t)),this.resetQuoteState(),this.initializeNamespace(),this.fetchTokens()}disconnectedCallback(){super.disconnectedCallback(),this.resetAssetsState(),this.unsubscribe.forEach(t=>t())}updated(t){super.updated(t),t.has("selectedPaymentAsset")&&this.fetchQuote()}render(){return s`
      <wui-flex flexDirection="column">
        ${this.profileTemplate()}

        <wui-flex
          flexDirection="column"
          gap="4"
          class="payment-methods-container"
          .padding=${["4","4","5","4"]}
        >
          ${this.paymentOptionsViewTemplate()} ${this.amountWithFeeTemplate()}

          <wui-flex
            alignItems="center"
            justifyContent="space-between"
            .padding=${["1","0","1","0"]}
          >
            <wui-separator></wui-separator>
          </wui-flex>

          ${this.paymentActionsTemplate()}
        </wui-flex>
      </wui-flex>
    `}profileTemplate(){if(this.selectedExchange){const n=v.formatNumber(this.quote?.origin.amount,{decimals:this.quote?.origin.currency.metadata.decimals??0}).toString();return s`
        <wui-flex
          .padding=${["4","3","4","3"]}
          alignItems="center"
          justifyContent="space-between"
          gap="2"
        >
          <wui-text variant="lg-regular" color="secondary">Paying with</wui-text>

          ${this.quote?s`<wui-text variant="lg-regular" color="primary">
                ${v.bigNumber(n,{safe:!0}).round(6).toString()}
                ${this.quote.origin.currency.metadata.symbol}
              </wui-text>`:s`<wui-shimmer width="80px" height="18px" variant="light"></wui-shimmer>`}
        </wui-flex>
      `}const t=F.getPlainAddress(this.caipAddress)??"",{name:i,image:r}=this.getWalletProperties({namespace:this.namespace}),{icon:a,label:o}=io[this.namespace]??{};return s`
      <wui-flex
        .padding=${["4","3","4","3"]}
        alignItems="center"
        justifyContent="space-between"
        gap="2"
      >
        <wui-wallet-switch
          profileName=${x(this.profileName)}
          address=${x(t)}
          imageSrc=${x(r)}
          alt=${x(i)}
          @click=${this.onConnectOtherWallet.bind(this)}
          data-testid="wui-wallet-switch"
        ></wui-wallet-switch>

        <wui-wallet-switch
          profileName=${x(o)}
          address=${x(t)}
          icon=${x(a)}
          iconSize="xs"
          .enableGreenCircle=${!1}
          alt=${x(o)}
          @click=${this.onConnectOtherWallet.bind(this)}
          data-testid="wui-wallet-switch"
        ></wui-wallet-switch>
      </wui-flex>
    `}initializeNamespace(){const t=g.state.activeChain;this.namespace=t,this.caipAddress=g.getAccountData(t)?.caipAddress,this.profileName=g.getAccountData(t)?.profileName??null,this.unsubscribe.push(g.subscribeChainProp("accountState",i=>this.onAccountStateChanged(i),t))}async fetchTokens(){if(this.namespace){let t;if(this.caipAddress){const{chainId:i,chainNamespace:r}=C.parseCaipAddress(this.caipAddress),a=`${r}:${i}`;t=g.getAllRequestedCaipNetworks().find(o=>o.caipNetworkId===a)}await p.fetchTokens({caipAddress:this.caipAddress,caipNetwork:t,namespace:this.namespace})}}fetchQuote(){if(this.amount&&this.recipient&&this.selectedPaymentAsset&&this.paymentAsset){const{address:t}=this.caipAddress?C.parseCaipAddress(this.caipAddress):{};p.fetchQuote({amount:this.amount.toString(),address:t,sourceToken:this.selectedPaymentAsset,toToken:this.paymentAsset,recipient:this.recipient})}}getWalletProperties({namespace:t}){if(!t)return{name:void 0,image:void 0};const i=this.activeConnectorIds[t];if(!i)return{name:void 0,image:void 0};const r=U.getConnector({id:i,namespace:t});if(!r)return{name:void 0,image:void 0};const a=L.getConnectorImage(r);return{name:r.name,image:a}}paymentOptionsViewTemplate(){return s`
      <wui-flex flexDirection="column" gap="2">
        <wui-text variant="sm-regular" color="secondary">CHOOSE PAYMENT OPTION</wui-text>
        <wui-flex class="pay-options-container">${this.paymentOptionsTemplate()}</wui-flex>
      </wui-flex>
    `}paymentOptionsTemplate(){const t=this.getPaymentAssetFromTokenBalances();return this.isFetchingTokenBalances?s`<w3m-pay-options-skeleton></w3m-pay-options-skeleton>`:t.length===0?s`<w3m-pay-options-empty
        @connectOtherWallet=${this.onConnectOtherWallet.bind(this)}
      ></w3m-pay-options-empty>`:s`<w3m-pay-options
      class=${Ot({disabled:this.isFetchingQuote})}
      .options=${t}
      .selectedPaymentAsset=${x(this.selectedPaymentAsset)}
      .onSelect=${this.onSelectedPaymentAssetChanged.bind(this)}
    ></w3m-pay-options>`}amountWithFeeTemplate(){return this.isFetchingQuote||!this.selectedPaymentAsset||this.quoteError?s`<w3m-pay-fees-skeleton></w3m-pay-fees-skeleton>`:s`<w3m-pay-fees></w3m-pay-fees>`}paymentActionsTemplate(){const t=this.isFetchingQuote||this.isFetchingTokenBalances,i=this.isFetchingQuote||this.isFetchingTokenBalances||!this.selectedPaymentAsset||!!this.quoteError,r=v.formatNumber(this.quote?.origin.amount??0,{decimals:this.quote?.origin.currency.metadata.decimals??0}).toString();return this.selectedExchange?t||i?s`
          <wui-shimmer width="100%" height="48px" variant="light" ?rounded=${!0}></wui-shimmer>
        `:s`<wui-button
        size="lg"
        fullWidth
        variant="accent-secondary"
        @click=${this.onPayWithExchange.bind(this)}
      >
        ${`Continue in ${this.selectedExchange.name}`}

        <wui-icon name="arrowRight" color="inherit" size="sm" slot="iconRight"></wui-icon>
      </wui-button>`:s`
      <wui-flex alignItems="center" justifyContent="space-between">
        <wui-flex flexDirection="column" gap="1">
          <wui-text variant="md-regular" color="secondary">Order Total</wui-text>

          ${t||i?s`<wui-shimmer width="58px" height="32px" variant="light"></wui-shimmer>`:s`<wui-flex alignItems="center" gap="01">
                <wui-text variant="h4-regular" color="primary">${Le(r)}</wui-text>

                <wui-text variant="lg-regular" color="secondary">
                  ${this.quote?.origin.currency.metadata.symbol||"Unknown"}
                </wui-text>
              </wui-flex>`}
        </wui-flex>

        ${this.actionButtonTemplate({isLoading:t,isDisabled:i})}
      </wui-flex>
    `}actionButtonTemplate(t){const i=Ge(this.quote),{isLoading:r,isDisabled:a}=t;let o="Pay";return i.length>1&&this.completedTransactionsCount===0&&(o="Approve"),s`
      <wui-button
        size="lg"
        variant="accent-primary"
        ?loading=${r||this.isPaymentInProgress}
        ?disabled=${a||this.isPaymentInProgress}
        @click=${()=>{i.length>0?this.onSendTransactions():this.onTransfer()}}
      >
        ${o}
        ${r?null:s`<wui-icon
              name="arrowRight"
              color="inherit"
              size="sm"
              slot="iconRight"
            ></wui-icon>`}
      </wui-button>
    `}getPaymentAssetFromTokenBalances(){return this.namespace?(this.tokenBalances[this.namespace]??[]).map(t=>{try{return _i(t)}catch{return null}}).filter(t=>!!t).filter(t=>{const{chainId:i}=C.parseCaipNetworkId(t.network),{chainId:r}=C.parseCaipNetworkId(this.paymentAsset.network);return V.isLowerCaseMatch(t.asset,this.paymentAsset.asset)?!0:this.selectedExchange?!V.isLowerCaseMatch(i.toString(),r.toString()):!0}):[]}onTokenBalancesChanged(t){this.tokenBalances=t;const[i]=this.getPaymentAssetFromTokenBalances();i&&p.setSelectedPaymentAsset(i)}async onConnectOtherWallet(){await U.connect(),await O.open({view:"PayQuote"})}onAccountStateChanged(t){const{address:i}=this.caipAddress?C.parseCaipAddress(this.caipAddress):{};if(this.caipAddress=t?.caipAddress,this.profileName=t?.profileName??null,i){const{address:r}=this.caipAddress?C.parseCaipAddress(this.caipAddress):{};r?V.isLowerCaseMatch(r,i)||(this.resetAssetsState(),this.resetQuoteState(),this.fetchTokens()):O.close()}}onSelectedPaymentAssetChanged(t){this.isFetchingQuote||p.setSelectedPaymentAsset(t)}async onTransfer(){const t=Ze(this.quote);if(t){if(!V.isLowerCaseMatch(this.selectedPaymentAsset?.asset,t.deposit.currency))throw new Error("Quote asset is not the same as the selected payment asset");const i=this.selectedPaymentAsset?.amount??"0",r=v.formatNumber(t.deposit.amount,{decimals:this.selectedPaymentAsset?.metadata.decimals??0}).toString();if(!v.bigNumber(i).gte(r)){A.showError("Insufficient funds");return}if(this.quote&&this.selectedPaymentAsset&&this.caipAddress&&this.namespace){const{address:a}=C.parseCaipAddress(this.caipAddress);await p.onTransfer({chainNamespace:this.namespace,fromAddress:a,toAddress:t.deposit.receiver,amount:r,paymentAsset:this.selectedPaymentAsset}),p.setRequestId(t.requestId),m.push("PayLoading")}}}async onSendTransactions(){const t=this.selectedPaymentAsset?.amount??"0",i=v.formatNumber(this.quote?.origin.amount??0,{decimals:this.selectedPaymentAsset?.metadata.decimals??0}).toString();if(!v.bigNumber(t).gte(i)){A.showError("Insufficient funds");return}const r=Ge(this.quote),[a]=Ge(this.quote,this.completedTransactionsCount);a&&this.namespace&&(await p.onSendTransaction({namespace:this.namespace,transactionStep:a}),this.completedTransactionsCount+=1,this.completedTransactionsCount===r.length&&(p.setRequestId(a.requestId),m.push("PayLoading")))}onPayWithExchange(){if(this.exchangeUrlForQuote){const t=F.returnOpenHref("","popupWindow","scrollbar=yes,width=480,height=720");if(!t)throw new Error("Could not create popup window");t.location.href=this.exchangeUrlForQuote;const i=Ze(this.quote);i&&p.setRequestId(i.requestId),p.initiatePayment(),m.push("PayLoading")}}resetAssetsState(){p.setSelectedPaymentAsset(null)}resetQuoteState(){p.resetQuoteState()}};I.styles=to;$([h()],I.prototype,"profileName",void 0);$([h()],I.prototype,"paymentAsset",void 0);$([h()],I.prototype,"namespace",void 0);$([h()],I.prototype,"caipAddress",void 0);$([h()],I.prototype,"amount",void 0);$([h()],I.prototype,"recipient",void 0);$([h()],I.prototype,"activeConnectorIds",void 0);$([h()],I.prototype,"selectedPaymentAsset",void 0);$([h()],I.prototype,"selectedExchange",void 0);$([h()],I.prototype,"isFetchingQuote",void 0);$([h()],I.prototype,"quoteError",void 0);$([h()],I.prototype,"quote",void 0);$([h()],I.prototype,"isFetchingTokenBalances",void 0);$([h()],I.prototype,"tokenBalances",void 0);$([h()],I.prototype,"isPaymentInProgress",void 0);$([h()],I.prototype,"exchangeUrlForQuote",void 0);$([h()],I.prototype,"completedTransactionsCount",void 0);I=$([b("w3m-pay-quote-view")],I);var oo=T`
  wui-image {
    border-radius: ${({borderRadius:e})=>e.round};
  }

  .transfers-badge {
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    border: 1px solid ${({tokens:e})=>e.theme.foregroundSecondary};
    border-radius: ${({borderRadius:e})=>e[4]};
  }
`,dt=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},Ae=class extends k{constructor(){super(),this.unsubscribe=[],this.paymentAsset=p.state.paymentAsset,this.amount=p.state.amount,this.unsubscribe.push(p.subscribeKey("paymentAsset",t=>{this.paymentAsset=t}),p.subscribeKey("amount",t=>{this.amount=t}))}disconnectedCallback(){this.unsubscribe.forEach(t=>t())}render(){const t=g.getAllRequestedCaipNetworks().find(i=>i.caipNetworkId===this.paymentAsset.network);return s`<wui-flex
      alignItems="center"
      gap="1"
      .padding=${["1","2","1","1"]}
      class="transfers-badge"
    >
      <wui-image src=${x(this.paymentAsset.metadata.logoURI)} size="xl"></wui-image>
      <wui-text variant="lg-regular" color="primary">
        ${this.amount} ${this.paymentAsset.metadata.symbol}
      </wui-text>
      <wui-text variant="sm-regular" color="secondary">
        on ${t?.name??"Unknown"}
      </wui-text>
    </wui-flex>`}};Ae.styles=[oo];dt([d()],Ae.prototype,"paymentAsset",void 0);dt([d()],Ae.prototype,"amount",void 0);Ae=dt([b("w3m-pay-header")],Ae);var ro=T`
  :host {
    height: 60px;
  }

  :host > wui-flex {
    box-sizing: border-box;
    background-color: var(--local-header-background-color);
  }

  wui-text {
    background-color: var(--local-header-background-color);
  }

  wui-flex.w3m-header-title {
    transform: translateY(0);
    opacity: 1;
  }

  wui-flex.w3m-header-title[view-direction='prev'] {
    animation:
      slide-down-out 120ms forwards ${({easings:e})=>e["ease-out-power-2"]},
      slide-down-in 120ms forwards ${({easings:e})=>e["ease-out-power-2"]};
    animation-delay: 0ms, 200ms;
  }

  wui-flex.w3m-header-title[view-direction='next'] {
    animation:
      slide-up-out 120ms forwards ${({easings:e})=>e["ease-out-power-2"]},
      slide-up-in 120ms forwards ${({easings:e})=>e["ease-out-power-2"]};
    animation-delay: 0ms, 200ms;
  }

  wui-icon-button[data-hidden='true'] {
    opacity: 0 !important;
    pointer-events: none;
  }

  @keyframes slide-up-out {
    from {
      transform: translateY(0px);
      opacity: 1;
    }
    to {
      transform: translateY(3px);
      opacity: 0;
    }
  }

  @keyframes slide-up-in {
    from {
      transform: translateY(-3px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  @keyframes slide-down-out {
    from {
      transform: translateY(0px);
      opacity: 1;
    }
    to {
      transform: translateY(-3px);
      opacity: 0;
    }
  }

  @keyframes slide-down-in {
    from {
      transform: translateY(3px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }
`,le=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},ao=["SmartSessionList"],no={PayWithExchange:xe.tokens.theme.foregroundPrimary};function It(){const e=m.state.data?.connector?.name,t=m.state.data?.wallet?.name,i=m.state.data?.network?.name,r=t??e,a=U.getConnectors(),o=a.length===1&&a[0]?.id==="w3m-email",n=g.getAccountData()?.socialProvider,l=n?n.charAt(0).toUpperCase()+n.slice(1):"Connect Social";return{Connect:`Connect ${o?"Email":""} Wallet`,Create:"Create Wallet",ChooseAccountName:void 0,Account:void 0,AccountSettings:void 0,AllWallets:"All Wallets",ApproveTransaction:"Approve Transaction",BuyInProgress:"Buy",UsageExceeded:"Usage Exceeded",ConnectingExternal:r??"Connect Wallet",ConnectingWalletConnect:r??"WalletConnect",ConnectingWalletConnectBasic:"WalletConnect",ConnectingSiwe:"Sign In",Convert:"Convert",ConvertSelectToken:"Select token",ConvertPreview:"Preview Convert",Downloads:r?`Get ${r}`:"Downloads",EmailLogin:"Email Login",EmailVerifyOtp:"Confirm Email",EmailVerifyDevice:"Register Device",GetWallet:"Get a Wallet",Networks:"Choose Network",OnRampProviders:"Choose Provider",OnRampActivity:"Activity",OnRampTokenSelect:"Select Token",OnRampFiatSelect:"Select Currency",Pay:"How you pay",ProfileWallets:"Wallets",SwitchNetwork:i??"Switch Network",Transactions:"Activity",UnsupportedChain:"Switch Network",UpgradeEmailWallet:"Upgrade Your Wallet",UpdateEmailWallet:"Edit Email",UpdateEmailPrimaryOtp:"Confirm Current Email",UpdateEmailSecondaryOtp:"Confirm New Email",WhatIsABuy:"What is Buy?",RegisterAccountName:"Choose Name",RegisterAccountNameSuccess:"",WalletReceive:"Receive",WalletCompatibleNetworks:"Compatible Networks",Swap:"Swap",SwapSelectToken:"Select Token",SwapPreview:"Preview Swap",WalletSend:"Send",WalletSendPreview:"Review Send",WalletSendSelectToken:"Select Token",WalletSendConfirmed:"Confirmed",WhatIsANetwork:"What is a network?",WhatIsAWallet:"What is a Wallet?",ConnectWallets:"Connect Wallet",ConnectSocials:"All Socials",ConnectingSocial:l,ConnectingMultiChain:"Select Chain",ConnectingFarcaster:"Farcaster",SwitchActiveChain:"Switch Chain",SmartSessionCreated:void 0,SmartSessionList:"Smart Sessions",SIWXSignMessage:"Sign In",PayLoading:"Processing payment...",PayQuote:"Payment Quote",DataCapture:"Profile",DataCaptureOtpConfirm:"Confirm Email",FundWallet:"Fund Wallet",PayWithExchange:"Deposit from Exchange",PayWithExchangeSelectAsset:"Select Asset",SmartAccountSettings:"Smart Account Settings"}}var Q=class extends k{constructor(){super(),this.unsubscribe=[],this.heading=It()[m.state.view],this.network=g.state.activeCaipNetwork,this.networkImage=L.getNetworkImage(this.network),this.showBack=!1,this.prevHistoryLength=1,this.view=m.state.view,this.viewDirection="",this.unsubscribe.push(Ht.subscribeNetworkImages(()=>{this.networkImage=L.getNetworkImage(this.network)}),m.subscribeKey("view",t=>{setTimeout(()=>{this.view=t,this.heading=It()[t]},ue.ANIMATION_DURATIONS.HeaderText),this.onViewChange(),this.onHistoryChange()}),g.subscribeKey("activeCaipNetwork",t=>{this.network=t,this.networkImage=L.getNetworkImage(this.network)}))}disconnectCallback(){this.unsubscribe.forEach(t=>t())}render(){const t=no[m.state.view]??xe.tokens.theme.backgroundPrimary;return this.style.setProperty("--local-header-background-color",t),s`
      <wui-flex
        .padding=${["0","4","0","4"]}
        justifyContent="space-between"
        alignItems="center"
      >
        ${this.leftHeaderTemplate()} ${this.titleTemplate()} ${this.rightHeaderTemplate()}
      </wui-flex>
    `}onWalletHelp(){D.sendEvent({type:"track",event:"CLICK_WALLET_HELP"}),m.push("WhatIsAWallet")}async onClose(){await Wt.safeClose()}rightHeaderTemplate(){const t=S?.state?.features?.smartSessions;return m.state.view!=="Account"||!t?this.closeButtonTemplate():s`<wui-flex>
      <wui-icon-button
        icon="clock"
        size="lg"
        iconSize="lg"
        type="neutral"
        variant="primary"
        @click=${()=>m.push("SmartSessionList")}
        data-testid="w3m-header-smart-sessions"
      ></wui-icon-button>
      ${this.closeButtonTemplate()}
    </wui-flex> `}closeButtonTemplate(){return s`
      <wui-icon-button
        icon="close"
        size="lg"
        type="neutral"
        variant="primary"
        iconSize="lg"
        @click=${this.onClose.bind(this)}
        data-testid="w3m-header-close"
      ></wui-icon-button>
    `}titleTemplate(){if(this.view==="PayQuote")return s`<w3m-pay-header></w3m-pay-header>`;const t=ao.includes(this.view);return s`
      <wui-flex
        view-direction="${this.viewDirection}"
        class="w3m-header-title"
        alignItems="center"
        gap="2"
      >
        <wui-text
          display="inline"
          variant="lg-regular"
          color="primary"
          data-testid="w3m-header-text"
        >
          ${this.heading}
        </wui-text>
        ${t?s`<wui-tag variant="accent" size="md">Beta</wui-tag>`:null}
      </wui-flex>
    `}leftHeaderTemplate(){const{view:t}=m.state,i=t==="Connect",r=S.state.enableEmbedded,a=t==="ApproveTransaction",o=t==="ConnectingSiwe",n=t==="Account",l=S.state.enableNetworkSwitch,_=a||o||i&&r;return n&&l?s`<wui-select
        id="dynamic"
        data-testid="w3m-account-select-network"
        active-network=${x(this.network?.name)}
        @click=${this.onNetworks.bind(this)}
        imageSrc=${x(this.networkImage)}
      ></wui-select>`:this.showBack&&!_?s`<wui-icon-button
        data-testid="header-back"
        id="dynamic"
        icon="chevronLeft"
        size="lg"
        iconSize="lg"
        type="neutral"
        variant="primary"
        @click=${this.onGoBack.bind(this)}
      ></wui-icon-button>`:s`<wui-icon-button
      data-hidden=${!i}
      id="dynamic"
      icon="helpCircle"
      size="lg"
      iconSize="lg"
      type="neutral"
      variant="primary"
      @click=${this.onWalletHelp.bind(this)}
    ></wui-icon-button>`}onNetworks(){this.isAllowedNetworkSwitch()&&(D.sendEvent({type:"track",event:"CLICK_NETWORKS"}),m.push("Networks"))}isAllowedNetworkSwitch(){const t=g.getAllRequestedCaipNetworks(),i=t?t.length>1:!1,r=t?.find(({id:a})=>a===this.network?.id);return i||!r}onViewChange(){const{history:t}=m.state;let i=ue.VIEW_DIRECTION.Next;t.length<this.prevHistoryLength&&(i=ue.VIEW_DIRECTION.Prev),this.prevHistoryLength=t.length,this.viewDirection=i}async onHistoryChange(){const{history:t}=m.state,i=this.shadowRoot?.querySelector("#dynamic");t.length>1&&!this.showBack&&i?(await i.animate([{opacity:1},{opacity:0}],{duration:200,fill:"forwards",easing:"ease"}).finished,this.showBack=!0,i.animate([{opacity:0},{opacity:1}],{duration:200,fill:"forwards",easing:"ease"})):t.length<=1&&this.showBack&&i&&(await i.animate([{opacity:1},{opacity:0}],{duration:200,fill:"forwards",easing:"ease"}).finished,this.showBack=!1,i.animate([{opacity:0},{opacity:1}],{duration:200,fill:"forwards",easing:"ease"}))}onGoBack(){m.goBack()}};Q.styles=ro;le([h()],Q.prototype,"heading",void 0);le([h()],Q.prototype,"network",void 0);le([h()],Q.prototype,"networkImage",void 0);le([h()],Q.prototype,"showBack",void 0);le([h()],Q.prototype,"prevHistoryLength",void 0);le([h()],Q.prototype,"view",void 0);le([h()],Q.prototype,"viewDirection",void 0);Q=le([b("w3m-header")],Q);var so=T`
  :host {
    display: flex;
    align-items: center;
    gap: ${({spacing:e})=>e[1]};
    padding: ${({spacing:e})=>e[2]} ${({spacing:e})=>e[3]}
      ${({spacing:e})=>e[2]} ${({spacing:e})=>e[2]};
    border-radius: ${({borderRadius:e})=>e[20]};
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    box-shadow:
      0px 0px 8px 0px rgba(0, 0, 0, 0.1),
      inset 0 0 0 1px ${({tokens:e})=>e.theme.borderPrimary};
    max-width: 320px;
  }

  wui-icon-box {
    border-radius: ${({borderRadius:e})=>e.round} !important;
    overflow: hidden;
  }

  wui-loading-spinner {
    padding: ${({spacing:e})=>e[1]};
    background-color: ${({tokens:e})=>e.core.foregroundAccent010};
    border-radius: ${({borderRadius:e})=>e.round} !important;
  }
`,pt=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},Se=class extends k{constructor(){super(...arguments),this.message="",this.variant="success"}render(){return s`
      ${this.templateIcon()}
      <wui-text variant="lg-regular" color="primary" data-testid="wui-snackbar-message"
        >${this.message}</wui-text
      >
    `}templateIcon(){const t={success:"success",error:"error",warning:"warning",info:"default"},i={success:"checkmark",error:"warning",warning:"warningCircle",info:"info"};return this.variant==="loading"?s`<wui-loading-spinner size="md" color="accent-primary"></wui-loading-spinner>`:s`<wui-icon-box
      size="md"
      color=${t[this.variant]}
      icon=${i[this.variant]}
    ></wui-icon-box>`}};Se.styles=[X,so];pt([d()],Se.prototype,"message",void 0);pt([d()],Se.prototype,"variant",void 0);Se=pt([b("wui-snackbar")],Se);var co=Me`
  :host {
    display: block;
    position: absolute;
    opacity: 0;
    pointer-events: none;
    top: 11px;
    left: 50%;
    width: max-content;
  }
`,Ft=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},Fe=class extends k{constructor(){super(),this.unsubscribe=[],this.timeout=void 0,this.open=A.state.open,this.unsubscribe.push(A.subscribeKey("open",t=>{this.open=t,this.onOpen()}))}disconnectedCallback(){clearTimeout(this.timeout),this.unsubscribe.forEach(t=>t())}render(){const{message:t,variant:i}=A.state;return s` <wui-snackbar message=${t} variant=${i}></wui-snackbar> `}onOpen(){clearTimeout(this.timeout),this.open?(this.animate([{opacity:0,transform:"translateX(-50%) scale(0.85)"},{opacity:1,transform:"translateX(-50%) scale(1)"}],{duration:150,fill:"forwards",easing:"ease"}),this.timeout&&clearTimeout(this.timeout),A.state.autoClose&&(this.timeout=setTimeout(()=>A.hide(),2500))):this.animate([{opacity:1,transform:"translateX(-50%) scale(1)"},{opacity:0,transform:"translateX(-50%) scale(0.85)"}],{duration:150,fill:"forwards",easing:"ease"})}};Fe.styles=co;Ft([h()],Fe.prototype,"open",void 0);Fe=Ft([b("w3m-snackbar")],Fe);var lo=Me`
  :host {
    width: 100%;
    display: block;
  }
`,ht=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},Ee=class extends k{constructor(){super(),this.unsubscribe=[],this.text="",this.open=z.state.open,this.unsubscribe.push(m.subscribeKey("view",()=>{z.hide()}),O.subscribeKey("open",t=>{t||z.hide()}),z.subscribeKey("open",t=>{this.open=t}))}disconnectedCallback(){this.unsubscribe.forEach(t=>t()),z.hide()}render(){return s`
      <div
        @pointermove=${this.onMouseEnter.bind(this)}
        @pointerleave=${this.onMouseLeave.bind(this)}
      >
        ${this.renderChildren()}
      </div>
    `}renderChildren(){return s`<slot></slot> `}onMouseEnter(){const t=this.getBoundingClientRect();if(!this.open){const i=document.querySelector("w3m-modal"),r={width:t.width,height:t.height,left:t.left,top:t.top};if(i){const a=i.getBoundingClientRect();r.left=t.left-(window.innerWidth-a.width)/2,r.top=t.top-(window.innerHeight-a.height)/2}z.showTooltip({message:this.text,triggerRect:r,variant:"shade"})}}onMouseLeave(t){this.contains(t.relatedTarget)||z.hide()}};Ee.styles=[lo];ht([d()],Ee.prototype,"text",void 0);ht([h()],Ee.prototype,"open",void 0);Ee=ht([b("w3m-tooltip-trigger")],Ee);var uo=T`
  :host {
    pointer-events: none;
  }

  :host > wui-flex {
    display: var(--w3m-tooltip-display);
    opacity: var(--w3m-tooltip-opacity);
    padding: 9px ${({spacing:e})=>e[3]} 10px ${({spacing:e})=>e[3]};
    border-radius: ${({borderRadius:e})=>e[3]};
    color: ${({tokens:e})=>e.theme.backgroundPrimary};
    position: absolute;
    top: var(--w3m-tooltip-top);
    left: var(--w3m-tooltip-left);
    transform: translate(calc(-50% + var(--w3m-tooltip-parent-width)), calc(-100% - 8px));
    max-width: calc(var(--apkt-modal-width) - ${({spacing:e})=>e[5]});
    transition: opacity ${({durations:e})=>e.lg}
      ${({easings:e})=>e["ease-out-power-2"]};
    will-change: opacity;
    opacity: 0;
    animation-duration: ${({durations:e})=>e.xl};
    animation-timing-function: ${({easings:e})=>e["ease-out-power-2"]};
    animation-name: fade-in;
    animation-fill-mode: forwards;
  }

  :host([data-variant='shade']) > wui-flex {
    background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
  }

  :host([data-variant='shade']) > wui-flex > wui-text {
    color: ${({tokens:e})=>e.theme.textSecondary};
  }

  :host([data-variant='fill']) > wui-flex {
    background-color: ${({tokens:e})=>e.theme.backgroundPrimary};
    border: 1px solid ${({tokens:e})=>e.theme.borderPrimary};
  }

  wui-icon {
    position: absolute;
    width: 12px !important;
    height: 4px !important;
    color: ${({tokens:e})=>e.theme.foregroundPrimary};
  }

  wui-icon[data-placement='top'] {
    bottom: 0px;
    left: 50%;
    transform: translate(-50%, 95%);
  }

  wui-icon[data-placement='bottom'] {
    top: 0;
    left: 50%;
    transform: translate(-50%, -95%) rotate(180deg);
  }

  wui-icon[data-placement='right'] {
    top: 50%;
    left: 0;
    transform: translate(-65%, -50%) rotate(90deg);
  }

  wui-icon[data-placement='left'] {
    top: 50%;
    right: 0%;
    transform: translate(65%, -50%) rotate(270deg);
  }

  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
`,Pe=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},de=class extends k{constructor(){super(),this.unsubscribe=[],this.open=z.state.open,this.message=z.state.message,this.triggerRect=z.state.triggerRect,this.variant=z.state.variant,this.unsubscribe.push(z.subscribe(t=>{this.open=t.open,this.message=t.message,this.triggerRect=t.triggerRect,this.variant=t.variant}))}disconnectedCallback(){this.unsubscribe.forEach(t=>t())}render(){this.dataset.variant=this.variant;const t=this.triggerRect.top,i=this.triggerRect.left;return this.style.cssText=`
    --w3m-tooltip-top: ${t}px;
    --w3m-tooltip-left: ${i}px;
    --w3m-tooltip-parent-width: ${this.triggerRect.width/2}px;
    --w3m-tooltip-display: ${this.open?"flex":"none"};
    --w3m-tooltip-opacity: ${this.open?1:0};
    `,s`<wui-flex>
      <wui-icon data-placement="top" size="inherit" name="cursor"></wui-icon>
      <wui-text color="primary" variant="sm-regular">${this.message}</wui-text>
    </wui-flex>`}};de.styles=[uo];Pe([h()],de.prototype,"open",void 0);Pe([h()],de.prototype,"message",void 0);Pe([h()],de.prototype,"triggerRect",void 0);Pe([h()],de.prototype,"variant",void 0);de=Pe([b("w3m-tooltip")],de);var be={getTabsByNamespace(e){return e&&e===E.CHAIN.EVM?S.state.remoteFeatures?.activity===!1?ue.ACCOUNT_TABS.filter(t=>t.label!=="Activity"):ue.ACCOUNT_TABS:[]},isValidReownName(e){return/^[a-zA-Z0-9]+$/gu.test(e)},isValidEmail(e){return/^[^\s@]+@[^\s@]+\.[^\s@]+$/gu.test(e)},validateReownName(e){return e.replace(/\^/gu,"").toLowerCase().replace(/[^a-zA-Z0-9]/gu,"")},hasFooter(){const e=m.state.view;if(ue.VIEWS_WITH_LEGAL_FOOTER.includes(e)){const{termsConditionsUrl:t,privacyPolicyUrl:i}=S.state,r=S.state.features?.legalCheckbox;return!(!t&&!i||r)}return ue.VIEWS_WITH_DEFAULT_FOOTER.includes(e)}},po=T`
  :host wui-ux-by-reown {
    padding-top: 0;
  }

  :host wui-ux-by-reown.branding-only {
    padding-top: ${({spacing:e})=>e[3]};
  }

  a {
    text-decoration: none;
    color: ${({tokens:e})=>e.core.textAccentPrimary};
    font-weight: 500;
  }
`,jt=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},je=class extends k{constructor(){super(),this.unsubscribe=[],this.remoteFeatures=S.state.remoteFeatures,this.unsubscribe.push(S.subscribeKey("remoteFeatures",t=>this.remoteFeatures=t))}disconnectedCallback(){this.unsubscribe.forEach(t=>t())}render(){const{termsConditionsUrl:t,privacyPolicyUrl:i}=S.state,r=S.state.features?.legalCheckbox;return!t&&!i||r?s`
        <wui-flex flexDirection="column"> ${this.reownBrandingTemplate(!0)} </wui-flex>
      `:s`
      <wui-flex flexDirection="column">
        <wui-flex .padding=${["4","3","3","3"]} justifyContent="center">
          <wui-text color="secondary" variant="md-regular" align="center">
            By connecting your wallet, you agree to our <br />
            ${this.termsTemplate()} ${this.andTemplate()} ${this.privacyTemplate()}
          </wui-text>
        </wui-flex>
        ${this.reownBrandingTemplate()}
      </wui-flex>
    `}andTemplate(){const{termsConditionsUrl:t,privacyPolicyUrl:i}=S.state;return t&&i?"and":""}termsTemplate(){const{termsConditionsUrl:t}=S.state;return t?s`<a href=${t} target="_blank" rel="noopener noreferrer"
      >Terms of Service</a
    >`:null}privacyTemplate(){const{privacyPolicyUrl:t}=S.state;return t?s`<a href=${t} target="_blank" rel="noopener noreferrer"
      >Privacy Policy</a
    >`:null}reownBrandingTemplate(t=!1){return this.remoteFeatures?.reownBranding?t?s`<wui-ux-by-reown class="branding-only"></wui-ux-by-reown>`:s`<wui-ux-by-reown></wui-ux-by-reown>`:null}};je.styles=[po];jt([h()],je.prototype,"remoteFeatures",void 0);je=jt([b("w3m-legal-footer")],je);var ho=Me``,mo=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},tt=class extends k{render(){const{termsConditionsUrl:t,privacyPolicyUrl:i}=S.state;return!t&&!i?null:s`
      <wui-flex
        .padding=${["4","3","3","3"]}
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        gap="3"
      >
        <wui-text color="secondary" variant="md-regular" align="center">
          We work with the best providers to give you the lowest fees and best support. More options
          coming soon!
        </wui-text>

        ${this.howDoesItWorkTemplate()}
      </wui-flex>
    `}howDoesItWorkTemplate(){return s` <wui-link @click=${this.onWhatIsBuy.bind(this)}>
      <wui-icon size="xs" color="accent-primary" slot="iconLeft" name="helpCircle"></wui-icon>
      How does it work?
    </wui-link>`}onWhatIsBuy(){D.sendEvent({type:"track",event:"SELECT_WHAT_IS_A_BUY",properties:{isSmartAccount:Oe(g.state.activeChain)===Ue.ACCOUNT_TYPES.SMART_ACCOUNT}}),m.push("WhatIsABuy")}};tt.styles=[ho];tt=mo([b("w3m-onramp-providers-footer")],tt);var wo=T`
  :host {
    display: block;
  }

  div.container {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    overflow: hidden;
    height: auto;
    display: block;
  }

  div.container[status='hide'] {
    animation: fade-out;
    animation-duration: var(--apkt-duration-dynamic);
    animation-timing-function: ${({easings:e})=>e["ease-out-power-2"]};
    animation-fill-mode: both;
    animation-delay: 0s;
  }

  div.container[status='show'] {
    animation: fade-in;
    animation-duration: var(--apkt-duration-dynamic);
    animation-timing-function: ${({easings:e})=>e["ease-out-power-2"]};
    animation-fill-mode: both;
    animation-delay: var(--apkt-duration-dynamic);
  }

  @keyframes fade-in {
    from {
      opacity: 0;
      filter: blur(6px);
    }
    to {
      opacity: 1;
      filter: blur(0px);
    }
  }

  @keyframes fade-out {
    from {
      opacity: 1;
      filter: blur(0px);
    }
    to {
      opacity: 0;
      filter: blur(6px);
    }
  }
`,mt=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},Ie=class extends k{constructor(){super(...arguments),this.resizeObserver=void 0,this.unsubscribe=[],this.status="hide",this.view=m.state.view}firstUpdated(){this.status=be.hasFooter()?"show":"hide",this.unsubscribe.push(m.subscribeKey("view",t=>{this.view=t,this.status=be.hasFooter()?"show":"hide",this.status==="hide"&&document.documentElement.style.setProperty("--apkt-footer-height","0px")})),this.resizeObserver=new ResizeObserver(t=>{for(const i of t)if(i.target===this.getWrapper()){const r=`${i.contentRect.height}px`;document.documentElement.style.setProperty("--apkt-footer-height",r)}}),this.resizeObserver.observe(this.getWrapper())}render(){return s`
      <div class="container" status=${this.status}>${this.templatePageContainer()}</div>
    `}templatePageContainer(){return be.hasFooter()?s` ${this.templateFooter()}`:null}templateFooter(){switch(this.view){case"Networks":return this.templateNetworksFooter();case"Connect":case"ConnectWallets":case"OnRampFiatSelect":case"OnRampTokenSelect":return s`<w3m-legal-footer></w3m-legal-footer>`;case"OnRampProviders":return s`<w3m-onramp-providers-footer></w3m-onramp-providers-footer>`;default:return null}}templateNetworksFooter(){return s` <wui-flex
      class="footer-in"
      padding="3"
      flexDirection="column"
      gap="3"
      alignItems="center"
    >
      <wui-text variant="md-regular" color="secondary" align="center">
        Your connected wallet may not support some of the networks available for this dApp
      </wui-text>
      <wui-link @click=${this.onNetworkHelp.bind(this)}>
        <wui-icon size="sm" color="accent-primary" slot="iconLeft" name="helpCircle"></wui-icon>
        What is a network
      </wui-link>
    </wui-flex>`}onNetworkHelp(){D.sendEvent({type:"track",event:"CLICK_NETWORK_HELP"}),m.push("WhatIsANetwork")}getWrapper(){return this.shadowRoot?.querySelector("div.container")}};Ie.styles=[wo];mt([h()],Ie.prototype,"status",void 0);mt([h()],Ie.prototype,"view",void 0);Ie=mt([b("w3m-footer")],Ie);var go=T`
  :host {
    display: block;
    width: inherit;
  }
`,wt=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},Ce=class extends k{constructor(){super(),this.unsubscribe=[],this.viewState=m.state.view,this.history=m.state.history.join(","),this.unsubscribe.push(m.subscribeKey("view",()=>{this.history=m.state.history.join(","),document.documentElement.style.setProperty("--apkt-duration-dynamic","var(--apkt-durations-lg)")}))}disconnectedCallback(){this.unsubscribe.forEach(t=>t()),document.documentElement.style.setProperty("--apkt-duration-dynamic","0s")}render(){return s`${this.templatePageContainer()}`}templatePageContainer(){return s`<w3m-router-container
      history=${this.history}
      .setView=${()=>{this.viewState=m.state.view}}
    >
      ${this.viewTemplate(this.viewState)}
    </w3m-router-container>`}viewTemplate(t){switch(t){case"AccountSettings":return s`<w3m-account-settings-view></w3m-account-settings-view>`;case"Account":return s`<w3m-account-view></w3m-account-view>`;case"AllWallets":return s`<w3m-all-wallets-view></w3m-all-wallets-view>`;case"ApproveTransaction":return s`<w3m-approve-transaction-view></w3m-approve-transaction-view>`;case"BuyInProgress":return s`<w3m-buy-in-progress-view></w3m-buy-in-progress-view>`;case"ChooseAccountName":return s`<w3m-choose-account-name-view></w3m-choose-account-name-view>`;case"Connect":return s`<w3m-connect-view></w3m-connect-view>`;case"Create":return s`<w3m-connect-view walletGuide="explore"></w3m-connect-view>`;case"ConnectingWalletConnect":return s`<w3m-connecting-wc-view></w3m-connecting-wc-view>`;case"ConnectingWalletConnectBasic":return s`<w3m-connecting-wc-basic-view></w3m-connecting-wc-basic-view>`;case"ConnectingExternal":return s`<w3m-connecting-external-view></w3m-connecting-external-view>`;case"ConnectingSiwe":return s`<w3m-connecting-siwe-view></w3m-connecting-siwe-view>`;case"ConnectWallets":return s`<w3m-connect-wallets-view></w3m-connect-wallets-view>`;case"ConnectSocials":return s`<w3m-connect-socials-view></w3m-connect-socials-view>`;case"ConnectingSocial":return s`<w3m-connecting-social-view></w3m-connecting-social-view>`;case"DataCapture":return s`<w3m-data-capture-view></w3m-data-capture-view>`;case"DataCaptureOtpConfirm":return s`<w3m-data-capture-otp-confirm-view></w3m-data-capture-otp-confirm-view>`;case"Downloads":return s`<w3m-downloads-view></w3m-downloads-view>`;case"EmailLogin":return s`<w3m-email-login-view></w3m-email-login-view>`;case"EmailVerifyOtp":return s`<w3m-email-verify-otp-view></w3m-email-verify-otp-view>`;case"EmailVerifyDevice":return s`<w3m-email-verify-device-view></w3m-email-verify-device-view>`;case"GetWallet":return s`<w3m-get-wallet-view></w3m-get-wallet-view>`;case"Networks":return s`<w3m-networks-view></w3m-networks-view>`;case"SwitchNetwork":return s`<w3m-network-switch-view></w3m-network-switch-view>`;case"ProfileWallets":return s`<w3m-profile-wallets-view></w3m-profile-wallets-view>`;case"Transactions":return s`<w3m-transactions-view></w3m-transactions-view>`;case"OnRampProviders":return s`<w3m-onramp-providers-view></w3m-onramp-providers-view>`;case"OnRampTokenSelect":return s`<w3m-onramp-token-select-view></w3m-onramp-token-select-view>`;case"OnRampFiatSelect":return s`<w3m-onramp-fiat-select-view></w3m-onramp-fiat-select-view>`;case"UpgradeEmailWallet":return s`<w3m-upgrade-wallet-view></w3m-upgrade-wallet-view>`;case"UpdateEmailWallet":return s`<w3m-update-email-wallet-view></w3m-update-email-wallet-view>`;case"UpdateEmailPrimaryOtp":return s`<w3m-update-email-primary-otp-view></w3m-update-email-primary-otp-view>`;case"UpdateEmailSecondaryOtp":return s`<w3m-update-email-secondary-otp-view></w3m-update-email-secondary-otp-view>`;case"UnsupportedChain":return s`<w3m-unsupported-chain-view></w3m-unsupported-chain-view>`;case"Swap":return s`<w3m-swap-view></w3m-swap-view>`;case"SwapSelectToken":return s`<w3m-swap-select-token-view></w3m-swap-select-token-view>`;case"SwapPreview":return s`<w3m-swap-preview-view></w3m-swap-preview-view>`;case"WalletSend":return s`<w3m-wallet-send-view></w3m-wallet-send-view>`;case"WalletSendSelectToken":return s`<w3m-wallet-send-select-token-view></w3m-wallet-send-select-token-view>`;case"WalletSendPreview":return s`<w3m-wallet-send-preview-view></w3m-wallet-send-preview-view>`;case"WalletSendConfirmed":return s`<w3m-send-confirmed-view></w3m-send-confirmed-view>`;case"WhatIsABuy":return s`<w3m-what-is-a-buy-view></w3m-what-is-a-buy-view>`;case"WalletReceive":return s`<w3m-wallet-receive-view></w3m-wallet-receive-view>`;case"WalletCompatibleNetworks":return s`<w3m-wallet-compatible-networks-view></w3m-wallet-compatible-networks-view>`;case"WhatIsAWallet":return s`<w3m-what-is-a-wallet-view></w3m-what-is-a-wallet-view>`;case"ConnectingMultiChain":return s`<w3m-connecting-multi-chain-view></w3m-connecting-multi-chain-view>`;case"WhatIsANetwork":return s`<w3m-what-is-a-network-view></w3m-what-is-a-network-view>`;case"ConnectingFarcaster":return s`<w3m-connecting-farcaster-view></w3m-connecting-farcaster-view>`;case"SwitchActiveChain":return s`<w3m-switch-active-chain-view></w3m-switch-active-chain-view>`;case"RegisterAccountName":return s`<w3m-register-account-name-view></w3m-register-account-name-view>`;case"RegisterAccountNameSuccess":return s`<w3m-register-account-name-success-view></w3m-register-account-name-success-view>`;case"SmartSessionCreated":return s`<w3m-smart-session-created-view></w3m-smart-session-created-view>`;case"SmartSessionList":return s`<w3m-smart-session-list-view></w3m-smart-session-list-view>`;case"SIWXSignMessage":return s`<w3m-siwx-sign-message-view></w3m-siwx-sign-message-view>`;case"Pay":return s`<w3m-pay-view></w3m-pay-view>`;case"PayLoading":return s`<w3m-pay-loading-view></w3m-pay-loading-view>`;case"PayQuote":return s`<w3m-pay-quote-view></w3m-pay-quote-view>`;case"FundWallet":return s`<w3m-fund-wallet-view></w3m-fund-wallet-view>`;case"PayWithExchange":return s`<w3m-deposit-from-exchange-view></w3m-deposit-from-exchange-view>`;case"PayWithExchangeSelectAsset":return s`<w3m-deposit-from-exchange-select-asset-view></w3m-deposit-from-exchange-select-asset-view>`;case"UsageExceeded":return s`<w3m-usage-exceeded-view></w3m-usage-exceeded-view>`;case"SmartAccountSettings":return s`<w3m-smart-account-settings-view></w3m-smart-account-settings-view>`;default:return s`<w3m-connect-view></w3m-connect-view>`}}};Ce.styles=[go];wt([h()],Ce.prototype,"viewState",void 0);wt([h()],Ce.prototype,"history",void 0);Ce=wt([b("w3m-router")],Ce);var fo=T`
  :host {
    z-index: ${({tokens:e})=>e.core.zIndex};
    display: block;
    backface-visibility: hidden;
    will-change: opacity;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    opacity: 0;
    background-color: ${({tokens:e})=>e.theme.overlay};
    backdrop-filter: blur(0px);
    transition:
      opacity ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-2"]},
      backdrop-filter ${({durations:e})=>e.lg}
        ${({easings:e})=>e["ease-out-power-2"]};
    will-change: opacity;
  }

  :host(.open) {
    opacity: 1;
    backdrop-filter: blur(8px);
  }

  :host(.appkit-modal) {
    position: relative;
    pointer-events: unset;
    background: none;
    width: 100%;
    opacity: 1;
  }

  wui-card {
    max-width: var(--apkt-modal-width);
    width: 100%;
    position: relative;
    outline: none;
    transform: translateY(4px);
    box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.05);
    transition:
      transform ${({durations:e})=>e.lg}
        ${({easings:e})=>e["ease-out-power-2"]},
      border-radius ${({durations:e})=>e.lg}
        ${({easings:e})=>e["ease-out-power-1"]},
      background-color ${({durations:e})=>e.lg}
        ${({easings:e})=>e["ease-out-power-1"]},
      box-shadow ${({durations:e})=>e.lg}
        ${({easings:e})=>e["ease-out-power-1"]};
    will-change: border-radius, background-color, transform, box-shadow;
    background-color: ${({tokens:e})=>e.theme.backgroundPrimary};
    padding: var(--local-modal-padding);
    box-sizing: border-box;
  }

  :host(.open) wui-card {
    transform: translateY(0px);
  }

  wui-card::before {
    z-index: 1;
    pointer-events: none;
    content: '';
    position: absolute;
    inset: 0;
    border-radius: clamp(0px, var(--apkt-borderRadius-8), 44px);
    transition: box-shadow ${({durations:e})=>e.lg}
      ${({easings:e})=>e["ease-out-power-2"]};
    transition-delay: ${({durations:e})=>e.md};
    will-change: box-shadow;
  }

  :host([data-mobile-fullscreen='true']) wui-card::before {
    border-radius: 0px;
  }

  :host([data-border='true']) wui-card::before {
    box-shadow: inset 0px 0px 0px 4px ${({tokens:e})=>e.theme.foregroundSecondary};
  }

  :host([data-border='false']) wui-card::before {
    box-shadow: inset 0px 0px 0px 1px ${({tokens:e})=>e.theme.borderPrimaryDark};
  }

  :host([data-border='true']) wui-card {
    animation:
      fade-in ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-2"]},
      card-background-border var(--apkt-duration-dynamic)
        ${({easings:e})=>e["ease-out-power-2"]};
    animation-fill-mode: backwards, both;
    animation-delay: var(--apkt-duration-dynamic);
  }

  :host([data-border='false']) wui-card {
    animation:
      fade-in ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-2"]},
      card-background-default var(--apkt-duration-dynamic)
        ${({easings:e})=>e["ease-out-power-2"]};
    animation-fill-mode: backwards, both;
    animation-delay: 0s;
  }

  :host(.appkit-modal) wui-card {
    max-width: var(--apkt-modal-width);
  }

  wui-card[shake='true'] {
    animation:
      fade-in ${({durations:e})=>e.lg} ${({easings:e})=>e["ease-out-power-2"]},
      w3m-shake ${({durations:e})=>e.xl}
        ${({easings:e})=>e["ease-out-power-2"]};
  }

  wui-flex {
    overflow-x: hidden;
    overflow-y: auto;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
  }

  @media (max-height: 700px) and (min-width: 431px) {
    wui-flex {
      align-items: flex-start;
    }

    wui-card {
      margin: var(--apkt-spacing-6) 0px;
    }
  }

  @media (max-width: 430px) {
    :host([data-mobile-fullscreen='true']) {
      height: 100dvh;
    }
    :host([data-mobile-fullscreen='true']) wui-flex {
      align-items: stretch;
    }
    :host([data-mobile-fullscreen='true']) wui-card {
      max-width: 100%;
      height: 100%;
      border-radius: 0;
      border: none;
    }
    :host(:not([data-mobile-fullscreen='true'])) wui-flex {
      align-items: flex-end;
    }

    :host(:not([data-mobile-fullscreen='true'])) wui-card {
      max-width: 100%;
      border-bottom: none;
    }

    :host(:not([data-mobile-fullscreen='true'])) wui-card[data-embedded='true'] {
      border-bottom-left-radius: clamp(0px, var(--apkt-borderRadius-8), 44px);
      border-bottom-right-radius: clamp(0px, var(--apkt-borderRadius-8), 44px);
    }

    :host(:not([data-mobile-fullscreen='true'])) wui-card:not([data-embedded='true']) {
      border-bottom-left-radius: 0px;
      border-bottom-right-radius: 0px;
    }

    wui-card[shake='true'] {
      animation: w3m-shake 0.5s ${({easings:e})=>e["ease-out-power-2"]};
    }
  }

  @keyframes fade-in {
    0% {
      transform: scale(0.99) translateY(4px);
    }
    100% {
      transform: scale(1) translateY(0);
    }
  }

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

  @keyframes card-background-border {
    from {
      background-color: ${({tokens:e})=>e.theme.backgroundPrimary};
    }
    to {
      background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
    }
  }

  @keyframes card-background-default {
    from {
      background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
    }
    to {
      background-color: ${({tokens:e})=>e.theme.backgroundPrimary};
    }
  }
`,J=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},Ct="scroll-lock",yo={PayWithExchange:"0",PayWithExchangeSelectAsset:"0",Pay:"0",PayQuote:"0",PayLoading:"0"},G=class extends k{constructor(){super(),this.unsubscribe=[],this.abortController=void 0,this.hasPrefetched=!1,this.enableEmbedded=S.state.enableEmbedded,this.open=O.state.open,this.caipAddress=g.state.activeCaipAddress,this.caipNetwork=g.state.activeCaipNetwork,this.shake=O.state.shake,this.filterByNamespace=U.state.filterByNamespace,this.padding=xe.spacing[1],this.mobileFullScreen=S.state.enableMobileFullScreen,this.initializeTheming(),_e.prefetchAnalyticsConfig(),this.unsubscribe.push(O.subscribeKey("open",e=>e?this.onOpen():this.onClose()),O.subscribeKey("shake",e=>this.shake=e),g.subscribeKey("activeCaipNetwork",e=>this.onNewNetwork(e)),g.subscribeKey("activeCaipAddress",e=>this.onNewAddress(e)),S.subscribeKey("enableEmbedded",e=>this.enableEmbedded=e),U.subscribeKey("filterByNamespace",e=>{this.filterByNamespace!==e&&!g.getAccountData(e)?.caipAddress&&(_e.fetchRecommendedWallets(),this.filterByNamespace=e)}),m.subscribeKey("view",()=>{this.dataset.border=be.hasFooter()?"true":"false",this.padding=yo[m.state.view]??xe.spacing[1]}))}firstUpdated(){if(this.dataset.border=be.hasFooter()?"true":"false",this.mobileFullScreen&&this.setAttribute("data-mobile-fullscreen","true"),this.caipAddress){if(this.enableEmbedded){O.close(),this.prefetch();return}this.onNewAddress(this.caipAddress)}this.open&&this.onOpen(),this.enableEmbedded&&this.prefetch()}disconnectedCallback(){this.unsubscribe.forEach(e=>e()),this.onRemoveKeyboardListener()}render(){return this.style.setProperty("--local-modal-padding",this.padding),this.enableEmbedded?s`${this.contentTemplate()}
        <w3m-tooltip></w3m-tooltip> `:this.open?s`
          <wui-flex @click=${this.onOverlayClick.bind(this)} data-testid="w3m-modal-overlay">
            ${this.contentTemplate()}
          </wui-flex>
          <w3m-tooltip></w3m-tooltip>
        `:null}contentTemplate(){return s` <wui-card
      shake="${this.shake}"
      data-embedded="${x(this.enableEmbedded)}"
      role="alertdialog"
      aria-modal="true"
      tabindex="0"
      data-testid="w3m-modal-card"
    >
      <w3m-header></w3m-header>
      <w3m-router></w3m-router>
      <w3m-footer></w3m-footer>
      <w3m-snackbar></w3m-snackbar>
      <w3m-alertbar></w3m-alertbar>
    </wui-card>`}async onOverlayClick(e){if(e.target===e.currentTarget){if(this.mobileFullScreen)return;await this.handleClose()}}async handleClose(){await Wt.safeClose()}initializeTheming(){const{themeVariables:e,themeMode:t}=Qt.state;Zt(e,Ve.getColorTheme(t))}onClose(){this.open=!1,this.classList.remove("open"),this.onScrollUnlock(),A.hide(),this.onRemoveKeyboardListener()}onOpen(){this.open=!0,this.classList.add("open"),this.onScrollLock(),this.onAddKeyboardListener()}onScrollLock(){const e=document.createElement("style");e.dataset.w3m=Ct,e.textContent=`
      body {
        touch-action: none;
        overflow: hidden;
        overscroll-behavior: contain;
      }
      w3m-modal {
        pointer-events: auto;
      }
    `,document.head.appendChild(e)}onScrollUnlock(){const e=document.head.querySelector(`style[data-w3m="${Ct}"]`);e&&e.remove()}onAddKeyboardListener(){this.abortController=new AbortController;const e=this.shadowRoot?.querySelector("wui-card");e?.focus(),window.addEventListener("keydown",t=>{if(t.key==="Escape")this.handleClose();else if(t.key==="Tab"){const{tagName:i}=t.target;i&&!i.includes("W3M-")&&!i.includes("WUI-")&&e?.focus()}},this.abortController)}onRemoveKeyboardListener(){this.abortController?.abort(),this.abortController=void 0}async onNewAddress(e){const t=g.state.isSwitchingNamespace,i=m.state.view==="ProfileWallets";!e&&!t&&!i&&O.close(),await Ut.initializeIfEnabled(e),this.caipAddress=e,g.setIsSwitchingNamespace(!1)}onNewNetwork(e){const t=this.caipNetwork?.caipNetworkId?.toString()!==e?.caipNetworkId?.toString(),i=m.state.view==="UnsupportedChain",r=O.state.open;let a=!1;this.enableEmbedded&&m.state.view==="SwitchNetwork"&&(a=!0),t&&w.resetState(),r&&i&&(a=!0),a&&m.state.view!=="SIWXSignMessage"&&m.goBack(),this.caipNetwork=e}prefetch(){this.hasPrefetched||(_e.prefetch(),_e.fetchWalletsByPage({page:1}),this.hasPrefetched=!0)}};G.styles=fo;J([d({type:Boolean})],G.prototype,"enableEmbedded",void 0);J([h()],G.prototype,"open",void 0);J([h()],G.prototype,"caipAddress",void 0);J([h()],G.prototype,"caipNetwork",void 0);J([h()],G.prototype,"shake",void 0);J([h()],G.prototype,"filterByNamespace",void 0);J([h()],G.prototype,"padding",void 0);J([h()],G.prototype,"mobileFullScreen",void 0);var Pt=class extends G{};Pt=J([b("w3m-modal")],Pt);var $t=class extends G{};$t=J([b("appkit-modal")],$t);var vo=T`
  .icon-box {
    width: 64px;
    height: 64px;
    border-radius: ${({borderRadius:e})=>e[5]};
    background-color: ${({colors:e})=>e.semanticError010};
  }
`,bo=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},it=class extends k{constructor(){super()}render(){return s`
      <wui-flex
        flexDirection="column"
        alignItems="center"
        gap="4"
        .padding="${["1","3","4","3"]}"
      >
        <wui-flex justifyContent="center" alignItems="center" class="icon-box">
          <wui-icon size="xxl" color="error" name="warningCircle"></wui-icon>
        </wui-flex>

        <wui-text variant="lg-medium" color="primary" align="center">
          The app isn't responding as expected
        </wui-text>
        <wui-text variant="md-regular" color="secondary" align="center">
          Try again or reach out to the app team for help.
        </wui-text>

        <wui-button
          variant="neutral-secondary"
          size="md"
          @click=${this.onTryAgainClick.bind(this)}
          data-testid="w3m-usage-exceeded-button"
        >
          <wui-icon color="inherit" slot="iconLeft" name="refresh"></wui-icon>
          Try Again
        </wui-button>
      </wui-flex>
    `}onTryAgainClick(){m.goBack()}};it.styles=vo;it=bo([b("w3m-usage-exceeded-view")],it);var xo=T`
  :host {
    width: 100%;
  }
`,N=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},P=class extends k{constructor(){super(...arguments),this.hasImpressionSent=!1,this.walletImages=[],this.imageSrc="",this.name="",this.size="md",this.tabIdx=void 0,this.disabled=!1,this.showAllWallets=!1,this.loading=!1,this.loadingSpinnerColor="accent-100",this.rdnsId="",this.displayIndex=void 0,this.walletRank=void 0,this.namespaces=[]}connectedCallback(){super.connectedCallback()}disconnectedCallback(){super.disconnectedCallback(),this.cleanupIntersectionObserver()}updated(t){super.updated(t),(t.has("name")||t.has("imageSrc")||t.has("walletRank"))&&(this.hasImpressionSent=!1),t.has("walletRank")&&this.walletRank&&!this.intersectionObserver&&this.setupIntersectionObserver()}setupIntersectionObserver(){this.intersectionObserver=new IntersectionObserver(t=>{t.forEach(i=>{i.isIntersecting&&!this.loading&&!this.hasImpressionSent&&this.sendImpressionEvent()})},{threshold:.1}),this.intersectionObserver.observe(this)}cleanupIntersectionObserver(){this.intersectionObserver&&(this.intersectionObserver.disconnect(),this.intersectionObserver=void 0)}sendImpressionEvent(){!this.name||this.hasImpressionSent||!this.walletRank||(this.hasImpressionSent=!0,(this.rdnsId||this.name)&&D.sendWalletImpressionEvent({name:this.name,walletRank:this.walletRank,rdnsId:this.rdnsId,view:m.state.view,displayIndex:this.displayIndex}))}handleGetWalletNamespaces(){return Object.keys(Xt.state.adapters).length>1?this.namespaces:[]}render(){return s`
      <wui-list-wallet
        .walletImages=${this.walletImages}
        imageSrc=${x(this.imageSrc)}
        name=${this.name}
        size=${x(this.size)}
        tagLabel=${x(this.tagLabel)}
        .tagVariant=${this.tagVariant}
        .walletIcon=${this.walletIcon}
        .tabIdx=${this.tabIdx}
        .disabled=${this.disabled}
        .showAllWallets=${this.showAllWallets}
        .loading=${this.loading}
        loadingSpinnerColor=${this.loadingSpinnerColor}
        .namespaces=${this.handleGetWalletNamespaces()}
      ></wui-list-wallet>
    `}};P.styles=xo;N([d({type:Array})],P.prototype,"walletImages",void 0);N([d()],P.prototype,"imageSrc",void 0);N([d()],P.prototype,"name",void 0);N([d()],P.prototype,"size",void 0);N([d()],P.prototype,"tagLabel",void 0);N([d()],P.prototype,"tagVariant",void 0);N([d()],P.prototype,"walletIcon",void 0);N([d()],P.prototype,"tabIdx",void 0);N([d({type:Boolean})],P.prototype,"disabled",void 0);N([d({type:Boolean})],P.prototype,"showAllWallets",void 0);N([d({type:Boolean})],P.prototype,"loading",void 0);N([d({type:String})],P.prototype,"loadingSpinnerColor",void 0);N([d()],P.prototype,"rdnsId",void 0);N([d()],P.prototype,"displayIndex",void 0);N([d()],P.prototype,"walletRank",void 0);N([d({type:Array})],P.prototype,"namespaces",void 0);P=N([b("w3m-list-wallet")],P);var ko=T`
  :host {
    --local-duration-height: 0s;
    --local-duration: ${({durations:e})=>e.lg};
    --local-transition: ${({easings:e})=>e["ease-out-power-2"]};
  }

  .container {
    display: block;
    overflow: hidden;
    overflow: hidden;
    position: relative;
    height: var(--local-container-height);
    transition: height var(--local-duration-height) var(--local-transition);
    will-change: height, padding-bottom;
  }

  .container[data-mobile-fullscreen='true'] {
    overflow: scroll;
  }

  .page {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    width: 100%;
    height: auto;
    width: inherit;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    background-color: ${({tokens:e})=>e.theme.backgroundPrimary};
    border-bottom-left-radius: var(--local-border-bottom-radius);
    border-bottom-right-radius: var(--local-border-bottom-radius);
    transition: border-bottom-left-radius var(--local-duration) var(--local-transition);
  }

  .page[data-mobile-fullscreen='true'] {
    height: 100%;
  }

  .page-content {
    display: flex;
    flex-direction: column;
    min-height: 100%;
  }

  .footer {
    height: var(--apkt-footer-height);
  }

  div.page[view-direction^='prev-'] .page-content {
    animation:
      slide-left-out var(--local-duration) forwards var(--local-transition),
      slide-left-in var(--local-duration) forwards var(--local-transition);
    animation-delay: 0ms, var(--local-duration, ${({durations:e})=>e.lg});
  }

  div.page[view-direction^='next-'] .page-content {
    animation:
      slide-right-out var(--local-duration) forwards var(--local-transition),
      slide-right-in var(--local-duration) forwards var(--local-transition);
    animation-delay: 0ms, var(--local-duration, ${({durations:e})=>e.lg});
  }

  @keyframes slide-left-out {
    from {
      transform: translateX(0px) scale(1);
      opacity: 1;
      filter: blur(0px);
    }
    to {
      transform: translateX(8px) scale(0.99);
      opacity: 0;
      filter: blur(4px);
    }
  }

  @keyframes slide-left-in {
    from {
      transform: translateX(-8px) scale(0.99);
      opacity: 0;
      filter: blur(4px);
    }
    to {
      transform: translateX(0) translateY(0) scale(1);
      opacity: 1;
      filter: blur(0px);
    }
  }

  @keyframes slide-right-out {
    from {
      transform: translateX(0px) scale(1);
      opacity: 1;
      filter: blur(0px);
    }
    to {
      transform: translateX(-8px) scale(0.99);
      opacity: 0;
      filter: blur(4px);
    }
  }

  @keyframes slide-right-in {
    from {
      transform: translateX(8px) scale(0.99);
      opacity: 0;
      filter: blur(4px);
    }
    to {
      transform: translateX(0) translateY(0) scale(1);
      opacity: 1;
      filter: blur(0px);
    }
  }
`,ee=function(e,t,i,r){var a=arguments.length,o=a<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,i):r,n;if(typeof Reflect=="object"&&typeof Reflect.decorate=="function")o=Reflect.decorate(e,t,i,r);else for(var l=e.length-1;l>=0;l--)(n=e[l])&&(o=(a<3?n(o):a>3?n(t,i,o):n(t,i))||o);return a>3&&o&&Object.defineProperty(t,i,o),o},To=60,M=class extends k{constructor(){super(...arguments),this.resizeObserver=void 0,this.transitionDuration="0.15s",this.transitionFunction="",this.history="",this.view="",this.setView=void 0,this.viewDirection="",this.historyState="",this.previousHeight="0px",this.mobileFullScreen=S.state.enableMobileFullScreen,this.onViewportResize=()=>{this.updateContainerHeight()}}updated(t){if(t.has("history")){const i=this.history;this.historyState!==""&&this.historyState!==i&&this.onViewChange(i)}t.has("transitionDuration")&&this.style.setProperty("--local-duration",this.transitionDuration),t.has("transitionFunction")&&this.style.setProperty("--local-transition",this.transitionFunction)}firstUpdated(){this.transitionFunction&&this.style.setProperty("--local-transition",this.transitionFunction),this.style.setProperty("--local-duration",this.transitionDuration),this.historyState=this.history,this.resizeObserver=new ResizeObserver(t=>{for(const i of t)if(i.target===this.getWrapper()){let r=i.contentRect.height;const a=parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--apkt-footer-height")||"0");this.mobileFullScreen?(r=(window.visualViewport?.height||window.innerHeight)-this.getHeaderHeight()-a,this.style.setProperty("--local-border-bottom-radius","0px")):(r=r+a,this.style.setProperty("--local-border-bottom-radius",a?"var(--apkt-borderRadius-5)":"0px")),this.style.setProperty("--local-container-height",`${r}px`),this.previousHeight!=="0px"&&this.style.setProperty("--local-duration-height",this.transitionDuration),this.previousHeight=`${r}px`}}),this.resizeObserver.observe(this.getWrapper()),this.updateContainerHeight(),window.addEventListener("resize",this.onViewportResize),window.visualViewport?.addEventListener("resize",this.onViewportResize)}disconnectedCallback(){const t=this.getWrapper();t&&this.resizeObserver&&this.resizeObserver.unobserve(t),window.removeEventListener("resize",this.onViewportResize),window.visualViewport?.removeEventListener("resize",this.onViewportResize)}render(){return s`
      <div class="container" data-mobile-fullscreen="${x(this.mobileFullScreen)}">
        <div
          class="page"
          data-mobile-fullscreen="${x(this.mobileFullScreen)}"
          view-direction="${this.viewDirection}"
        >
          <div class="page-content">
            <slot></slot>
          </div>
        </div>
      </div>
    `}onViewChange(t){const i=t.split(",").filter(Boolean),r=this.historyState.split(",").filter(Boolean),a=r.length,o=i.length,n=i[i.length-1]||"",l=Ve.cssDurationToNumber(this.transitionDuration);let _="";o>a?_="next":o<a?_="prev":o===a&&i[o-1]!==r[a-1]&&(_="next"),this.viewDirection=`${_}-${n}`,setTimeout(()=>{this.historyState=t,this.setView?.(n)},l),setTimeout(()=>{this.viewDirection=""},l*2)}getWrapper(){return this.shadowRoot?.querySelector("div.page")}updateContainerHeight(){const t=this.getWrapper();if(!t)return;const i=parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--apkt-footer-height")||"0");let r=0;this.mobileFullScreen?(r=(window.visualViewport?.height||window.innerHeight)-this.getHeaderHeight()-i,this.style.setProperty("--local-border-bottom-radius","0px")):(r=t.getBoundingClientRect().height+i,this.style.setProperty("--local-border-bottom-radius",i?"var(--apkt-borderRadius-5)":"0px")),this.style.setProperty("--local-container-height",`${r}px`),this.previousHeight!=="0px"&&this.style.setProperty("--local-duration-height",this.transitionDuration),this.previousHeight=`${r}px`}getHeaderHeight(){return To}};M.styles=[ko];ee([d({type:String})],M.prototype,"transitionDuration",void 0);ee([d({type:String})],M.prototype,"transitionFunction",void 0);ee([d({type:String})],M.prototype,"history",void 0);ee([d({type:String})],M.prototype,"view",void 0);ee([d({attribute:!1})],M.prototype,"setView",void 0);ee([h()],M.prototype,"viewDirection",void 0);ee([h()],M.prototype,"historyState",void 0);ee([h()],M.prototype,"previousHeight",void 0);ee([h()],M.prototype,"mobileFullScreen",void 0);M=ee([b("w3m-router-container")],M);export{$t as AppKitModal,P as W3mListWallet,Pt as W3mModal,G as W3mModalBase,M as W3mRouterContainer,it as W3mUsageExceededView};

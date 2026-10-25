import{n as e,r as t}from"./vue-i18n.BpBlt31e.js";import{A as n,K as r,M as i,N as a,O as o,R as s,T as c,Z as l,_ as u,c as d,d as f,dt as p,f as m,g as h,h as g,l as _,pt as v,r as y,u as b}from"./runtime-core.esm-bundler.WMqPV-cs.js";import{t as ee}from"#entry";import{c as x,d as S,h as C,l as te,m as w,n as T,p as E,s as D,t as O,u as k}from"./NavigationButton.BPdMdLPi.js";var A=``+new URL(`../images/brand/logo.BLeSWZUH.svg`,import.meta.url).href,j=``+new URL(`../images/flags/de.Agp6hujU.svg`,import.meta.url).href,M=``+new URL(`../images/flags/ee.gu2xp-XP.svg`,import.meta.url).href,N=``+new URL(`../images/flags/gb.zz7D-IWQ.svg`,import.meta.url).href,P=``+new URL(`../images/flags/nl.xmOrk5oz.svg`,import.meta.url).href,F=``+new URL(`../images/flags/pl.DYMDE_8e.svg`,import.meta.url).href,I=``+new URL(`../images/flags/se.B90i_7jt.svg`,import.meta.url).href,L=``+new URL(`../images/payments/cryptobot.B3T2TRQa.svg`,import.meta.url).href,R=``+new URL(`../images/payments/heleket.yT2ooKfm.svg`,import.meta.url).href,z=``+new URL(`../images/payments/yookassa.Bv3_g-aM.svg`,import.meta.url).href,B={de:j,ee:M,gb:N,nl:P,pl:F,se:I},V=[{id:`yookassa`,src:z,alt:`ЮKassa`,width:92,height:22},{id:`heleket`,src:R,alt:`Heleket`,width:26,height:26},{id:`cryptobot`,src:L,alt:`CryptoBot`,width:35,height:19}],H=globalThis.setInterval,U={up:`operational`,partial:`partial`,down:`down`};function W(e,t=Date.now()){if(typeof e!=`object`||!e)return`unknown`;let{overall:n,updatedAt:r}=e;return typeof r!=`number`||t-r>3e5||r-t>6e4?`unknown`:typeof n==`string`?U[n]??`unknown`:`unknown`}var G={"aria-live":`polite`,"aria-atomic":`true`},K=Object.assign(C(u({__name:`ServiceStatus`,setup(t){let{t:i}=e(),a=r(`unknown`),u=d(()=>({operational:i(`footer.serviceStates.operational`),partial:i(`footer.serviceStates.partial`),down:i(`footer.serviceStates.down`),unknown:i(`footer.serviceStates.unknown`)})[a.value]),f,p;async function m(){if(document.visibilityState!==`visible`||f)return;let e=new AbortController;f=e;try{let t={signal:e.signal,timeout:5e3,retry:0};a.value=W(await ee(`/api/status/summary`,t))}catch{a.value=`unknown`}finally{f=void 0}}return o(()=>{m(),p=H(m,6e4),document.addEventListener(`visibilitychange`,m)}),c(()=>{clearInterval(p),f?.abort(),document.removeEventListener(`visibilitychange`,m)}),(e,t)=>(n(),b(O,{class:`service-status`,"data-state":l(a),target:l(D),"aria-label":`${l(i)(`footer.status`)}: ${l(u)}`},{default:s(()=>[t[0]||=_(`span`,{class:`service-status__dot`,"aria-hidden":`true`},null,-1),_(`span`,G,v(l(u)),1)]),_:1},8,[`data-state`,`target`,`aria-label`]))}}),[[`__scopeId`,`data-v-f507b49d`]]),{__name:`LayoutServiceStatus`}),q={class:`site-closing`},ne={class:`content-frame`},J={class:`closing-sheet sheet`},Y={class:`site-footer`},X={class:`footer-grid`},Z={class:`footer-brand`},re=[`src`],ie={class:`footer-column`},ae={class:`footer-column`},oe={class:`footer-text`},se={class:`footer-bottom`},ce={class:`footer-legal`},le={class:`footer-tax`},ue=[`aria-label`],de=[`src`,`alt`,`width`,`height`],fe=Object.assign(C(u({__name:`SiteFooter`,setup(r){let{t:o}=e(),c=new Date().getFullYear(),u=[{id:`bot`,labelKey:`footer.links.bot`,href:k},{id:`support`,labelKey:`footer.links.support`,href:te}];return(e,r)=>(n(),m(`div`,q,[_(`div`,ne,[h(S,{side:`left`,class:`closing-field`}),_(`div`,J,[a(e.$slots,`default`,{},void 0,!0),_(`footer`,Y,[_(`div`,X,[_(`div`,Z,[h(O,{class:`footer-logo`,target:`/`,"aria-label":l(o)(`brand.name`)},{default:s(()=>[_(`img`,{src:l(A),alt:``,width:`60`,height:`24`},null,8,re)]),_:1},8,[`aria-label`]),_(`p`,null,v(l(o)(`footer.description`)),1),h(K)]),_(`div`,ie,[_(`h2`,null,v(l(o)(`footer.legalLabel`)),1),(n(!0),m(y,null,i(Object.values(l(t)),e=>(n(),b(O,{key:e.id,class:`footer-link`,target:`/${e.id}`},{default:s(()=>[g(v(e.label),1)]),_:2},1032,[`target`]))),128))]),_(`div`,ae,[_(`h2`,null,v(l(o)(`footer.contactsLabel`)),1),(n(),m(y,null,i(u,e=>h(O,{key:e.id,class:`footer-link`,target:e.href},{default:s(()=>[g(v(l(o)(e.labelKey)),1)]),_:2},1032,[`target`])),64)),_(`span`,oe,v(l(x)),1)])]),_(`div`,se,[_(`div`,ce,[_(`span`,null,[g(v(l(o)(`footer.companyName`))+`, `,1),_(`span`,le,v(l(o)(`footer.taxId`)),1)]),_(`span`,null,`© `+v(l(c))+` `+v(l(o)(`brand.name`)),1)]),_(`ul`,{class:`payment-marks`,"aria-label":l(o)(`footer.paymentsLabel`)},[(n(!0),m(y,null,i(l(V),e=>(n(),m(`li`,{key:e.id},[_(`img`,{src:e.src,alt:e.alt,width:e.width,height:e.height,loading:`lazy`},null,8,de)]))),128))],8,ue)])])])])]))}}),[[`__scopeId`,`data-v-d5f44cad`]]),{__name:`LayoutSiteFooter`}),pe={},me={class:`accent-mark`};function Q(e,t){return n(),m(`span`,me,[a(e.$slots,`default`,{},void 0,!0)])}var he=Object.assign(C(pe,[[`render`,Q],[`__scopeId`,`data-v-a1feb90a`]]),{__name:`UiAccentMark`}),ge=Object.assign(u({__name:`BaseButton`,props:{href:{},variant:{default:`primary`},size:{default:`regular`},icon:{}},setup(e){let t=e,{navigate:r}=T();function i(){r(t.href)}return(t,r)=>(n(),m(`button`,{type:`button`,class:p([`base-button`,[`base-button--${e.variant}`,{"base-button--small":e.size===`small`}]]),onClick:i},[e.icon?(n(),b(w,{key:0,name:e.icon,size:18},null,8,[`name`])):f(``,!0),_(`span`,null,[a(t.$slots,`default`)])],2))}}),{__name:`UiBaseButton`}),_e=`attribute vec2 point; void main() { gl_Position = vec4(point, 0.0, 1.0); }`,ve=`
  precision highp float;
  uniform vec2 resolution;
  uniform vec2 blur;
  uniform float time;
  uniform float glow;
  uniform float lift;
  float random(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(random(i), random(i + vec2(1.0, 0.0)), f.x), mix(random(i + vec2(0.0, 1.0)), random(i + vec2(1.0)), f.x), f.y);
  }
  float fbm(vec2 p, vec2 softness) {
    float value = 0.0;
    float amplitude = 0.5;
    for (int i = 0; i < 4; i++) {
      value += amplitude * (0.5 + (noise(p) - 0.5) * exp(-2.0 * dot(softness, softness)));
      p = p * 2.03 + 17.0;
      softness *= 2.03;
      amplitude *= 0.5;
    }
    return value;
  }
  float grain(vec2 p) {
    vec3 q = fract(p.xyx * 0.1031);
    q += dot(q, q.yzx + 33.33);
    return fract((q.x + q.y) * q.z);
  }
  float fade(float distance, float size) { return smoothstep(-2.0 * size, 2.0 * size, distance); }
  void main() {
    vec2 uv = gl_FragCoord.xy / resolution;
    float y = uv.y * lift;
    vec2 soft = blur * vec2(1.0, lift);
    float drift = 0.45 * (time + 1.2 * sin(time * 0.7)) + 0.06 * sin(time * 2.1);
    float spread = exp(-pow((uv.x - 0.5) / 0.46, 2.0));
    float rise = fbm(vec2(uv.x * 7.0 - drift * 1.75, y * 2.4), soft * vec2(7.0, 2.4));
    float body = 0.0;
    for (int i = 0; i < 2; i++) {
      float x = uv.x + (float(i) * 2.0 - 1.0) * blur.x;
      float crest = (0.18 + 0.44 * pow(fbm(vec2(x * 4.0 - drift, 3.7), vec2(blur.x * 4.0, 0.0)), 1.3)) * (0.45 + 0.55 * exp(-pow((x - 0.5) / 0.46, 2.0)));
      float edge = min(crest + (rise - 0.5) * 0.08, 0.56);
      float reach = sqrt(0.18 * edge * edge + 5.0 * soft.y * soft.y);
      body += 0.5 - 0.5 * smoothstep(0.575 * edge - reach, 0.575 * edge + reach, y);
    }
    float base = exp(-y * 3.0) * (0.35 + 0.45 * spread);
    float haze = sqrt(1.0 - 0.8 * uv.y) * (0.5 + 0.5 * spread);
    float level = body * (0.6 + 0.4 * rise) * spread + base * 0.5 + haze * 0.11;
    float knee = max(0.2 - abs(level - 0.9), 0.0) / 0.2;
    float light = (min(level, 0.9) - knee * knee * 0.05) * fade(uv.x, blur.x) * fade(1.0 - uv.x, blur.x) * fade(uv.y, blur.y) * glow;
    light += (grain(gl_FragCoord.xy) + grain(gl_FragCoord.yx + 0.5) - 1.0) / 255.0 * min(light * 255.0, 1.0);
    gl_FragColor = vec4(vec3(light), light);
  }
`;function ye(e,t){let n=e.getContext(`webgl`,{antialias:!1});if(!n)return;let r=(e,t)=>{let r=n.createShader(e);return n.shaderSource(r,t),n.compileShader(r),r},i=n.createProgram();if(n.attachShader(i,r(n.VERTEX_SHADER,_e)),n.attachShader(i,r(n.FRAGMENT_SHADER,ve)),n.linkProgram(i),!n.getProgramParameter(i,n.LINK_STATUS))return;n.useProgram(i),n.bindBuffer(n.ARRAY_BUFFER,n.createBuffer()),n.bufferData(n.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),n.STATIC_DRAW);let a=n.getAttribLocation(i,`point`);n.enableVertexAttribArray(a),n.vertexAttribPointer(a,2,n.FLOAT,!1,0,0);let o=n.getUniformLocation(i,`resolution`),s=n.getUniformLocation(i,`blur`),c=n.getUniformLocation(i,`time`),l=n.getUniformLocation(i,`glow`),u=n.getUniformLocation(i,`lift`),d=+!!t,f=0;return{resize(t,r,i=r){e.width=Math.max(1,Math.round(t*.5)),e.height=Math.max(1,Math.round(r*.5)),n.viewport(0,0,e.width,e.height),n.uniform2f(o,e.width,e.height),n.uniform2f(s,24/Math.max(1,t),24/Math.max(1,r)),n.uniform1f(u,1.28*r/Math.max(1,i))},draw(e){return f&&(d=Math.min(1,d+Math.min(e-f,1/30)/.2)),f=e,n.uniform1f(l,1-(1-d)**3),n.uniform1f(c,e+40),n.drawArrays(n.TRIANGLES,0,3),d===1}}}var $;function be(){if($===void 0)try{let e=`transferControlToOffscreen`in HTMLCanvasElement.prototype?new OffscreenCanvas(1,1).getContext(`webgl`):null;$=!!e,e?.getExtension(`WEBGL_lose_context`)?.loseContext()}catch{$=!1}return $}var xe=Object.assign(C(u({__name:`LightFlare`,setup(e){let t=r(null);function i(e){let t=matchMedia(`(prefers-reduced-motion: reduce)`).matches,n=new Worker(new URL(``+new URL(`../lightFlare-DBDApq4q.js`,import.meta.url).href,``+import.meta.url),{type:`module`}),r=e.transferControlToOffscreen();n.postMessage({canvas:r,still:t},[r]);let i=!1,a=()=>n.postMessage({playing:i&&document.visibilityState===`visible`}),o=new ResizeObserver(()=>n.postMessage({width:e.clientWidth,height:e.clientHeight})),s=new IntersectionObserver(e=>{i=e.at(-1)?.isIntersecting??!1,a()});return o.observe(e),s.observe(e),document.addEventListener(`visibilitychange`,a),()=>{o.disconnect(),s.disconnect(),document.removeEventListener(`visibilitychange`,a),n.terminate()}}if(be()){let e;o(()=>{t.value&&(e=i(t.value))}),c(()=>e?.())}else{let e;E(t,{stillTime:4,resize(t){e??=ye(t,matchMedia(`(prefers-reduced-motion: reduce)`).matches),e?.resize(t.clientWidth,t.clientHeight)},draw(t){e?.draw(t)}})}return(e,r)=>(n(),m(`canvas`,{ref_key:`canvas`,ref:t,class:`light-flare`,"aria-hidden":`true`},null,512))}}),[[`__scopeId`,`data-v-1c8bf48f`]]),{__name:`UiLightFlare`});export{B as a,fe as i,ge as n,A as o,he as r,xe as t};
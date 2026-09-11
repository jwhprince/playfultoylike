"""Browser smoke/accessibility/performance audit via an existing local Chromium CDP port.
Start a local server on 8080 and headless Chromium with --remote-debugging-port=9222.
Screenshots and machine-readable results go to /tmp/kakoe-audit/.
Only Python standard library is needed. No site data leaves localhost.
"""
import socket, json, base64, os, struct, urllib.request, time
from pathlib import Path
OUT=Path('/tmp/kakoe-audit');OUT.mkdir(exist_ok=True)
class CDP:
    def __init__(self):
        pages=json.load(urllib.request.urlopen('http://127.0.0.1:9222/json'))
        path=next(p for p in pages if p['type']=='page')['webSocketDebuggerUrl'].split('9222')[1]
        self.s=socket.create_connection(('127.0.0.1',9222));self.s.settimeout(30)
        key=base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(f'GET {path} HTTP/1.1\r\nHost: localhost:9222\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nOrigin: http://localhost:9222\r\n\r\n'.encode())
        response=b''
        while b'\r\n\r\n' not in response:response+=self.s.recv(1)
        assert b'HTTP/1.1 101' in response,response
        self.i=0;self.events=[]
    def read(self,n):
        data=b''
        while len(data)<n:data+=self.s.recv(n-len(data))
        return data
    def call(self,method,params=None):
        self.i+=1;payload=json.dumps(dict(id=self.i,method=method,params=params or {})).encode();mask=os.urandom(4);size=len(payload)
        head=bytes([129,128|size]) if size<126 else bytes([129,254])+struct.pack('!H',size)
        self.s.sendall(head+mask+bytes(v^mask[i%4] for i,v in enumerate(payload)))
        while True:
            a,b=self.read(2);n=b&127
            if n==126:n=struct.unpack('!H',self.read(2))[0]
            elif n==127:n=struct.unpack('!Q',self.read(8))[0]
            data=json.loads(self.read(n))
            if data.get('id')==self.i:
                assert 'error' not in data,data
                return data.get('result',{})
            self.events.append(data)
    def js(self,expression):
        r=self.call('Runtime.evaluate',dict(expression=expression,returnByValue=True,awaitPromise=True))
        assert 'exceptionDetails' not in r,r
        return r['result'].get('value')
    def viewport(self,width,height=1000):self.call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':False})
    def key(self,key,code):
        for kind in ['keyDown','keyUp']:self.call('Input.dispatchKeyEvent',{'type':kind,'key':key,'code':key,'windowsVirtualKeyCode':code})
    def shot(self,name,full=False):
        shot=self.call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':full})
        (OUT/f'{name}.png').write_bytes(base64.b64decode(shot['data']))
    def navigate(self):
        self.call('Page.navigate',{'url':'http://127.0.0.1:8080'})
        time.sleep(.7);self.js('document.fonts.ready.then(() => true)')

c=CDP();c.call('Page.enable');c.call('Runtime.enable');c.call('Log.enable');c.call('Network.enable')
c.call('Page.addScriptToEvaluateOnNewDocument',{'source':"if(!window.auditMetrics){window.auditMetrics={lcp:0,cls:0};new PerformanceObserver(l=>l.getEntries().forEach(e=>auditMetrics.lcp=e.startTime)).observe({type:'largest-contentful-paint',buffered:true});new PerformanceObserver(l=>l.getEntries().forEach(e=>{if(!e.hadRecentInput)auditMetrics.cls+=e.value})).observe({type:'layout-shift',buffered:true});}"})
c.navigate();c.js('localStorage.removeItem("kakoe-media-theme")')
c.call('Emulation.setEmulatedMedia',{'features':[{'name':'prefers-color-scheme','value':'light'}]});c.navigate()
assert c.js('document.title.startsWith("Какое-то медиа")')
assert c.js('document.querySelectorAll(".gallery-card").length')==6
assert c.js('document.documentElement.dataset.theme')=='light'
results={'viewports':[],'contrast':{},'checks':[]}
contrast_js=r'''(() => {
 const rgb=s=>(s.match(/[\d.]+/g)||[]).map(Number);
 const lum=c=>c.slice(0,3).map(n=>{n/=255;return n<=.04045?n/12.92:((n+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
 const violations=[];
 for(const el of document.querySelectorAll('body *')) {
  if(![...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())||el.closest('[aria-hidden="true"],.visually-hidden,script,noscript,style')||!el.getClientRects().length)continue;
  const st=getComputedStyle(el),rect=el.getBoundingClientRect();if(st.visibility==='hidden'||rect.width<2)continue;
  let bg=[246,243,233],parent=el;
  while(parent){const col=rgb(getComputedStyle(parent).backgroundColor);if(col.length>=3&&(col.length<4||col[3]===1)){bg=col;break;}parent=parent.parentElement;}
  let fg=rgb(st.color);const alpha=Number(st.opacity)*(fg[3]??1);fg=fg.map((v,i)=>i<3?v*alpha+bg[i]*(1-alpha):v);
  const l1=lum(fg),l2=lum(bg),ratio=(Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05);
  const large=parseFloat(st.fontSize)>=24||(parseFloat(st.fontSize)>=18.66&&Number(st.fontWeight)>=700),needed=large?3:4.5;
  if(ratio<needed-.02)violations.push({text:el.textContent.trim().slice(0,55),class:el.className,ratio:+ratio.toFixed(2),needed});
 }
 return violations;
})()'''
for theme in ['light','dark']:
    if c.js('document.documentElement.dataset.theme')!=theme:c.js('document.querySelector(".theme-toggle").click()')
    time.sleep(.4)
    for width in [320,375,414,640,768,1024,1440]:
        c.viewport(width);c.js('window.scrollTo({top:0,behavior:"instant"})');time.sleep(.2)
        layout=c.js('({width:innerWidth,client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth,broken:[...document.images].filter(i=>i.getAttribute("src")&&i.complete&&!i.naturalWidth).map(i=>i.src),smallTargets:[...document.querySelectorAll("a,button")].filter(e=>e.getClientRects().length&&e.getBoundingClientRect().top>=0&&(e.getBoundingClientRect().width<44||e.getBoundingClientRect().height<44)).map(e=>e.className)})')
        assert layout['scroll']<=layout['client'],layout
        assert not layout['broken'],layout
        results['viewports'].append({'theme':theme,**layout})
        if width in [375,1440]:c.shot(f'{theme}-{width}')
    c.js('Promise.all([...document.images].filter(i=>i.getAttribute("src")).map(i=>{i.loading="eager";return i.decode()}))')
    c.js('document.querySelector("#contact").scrollIntoView({behavior:"instant"})');time.sleep(.8)
    c.shot(f'{theme}-contact')
    c.js('document.querySelector("#about").scrollIntoView({behavior:"instant"})');time.sleep(.8)
    c.shot(f'{theme}-about')
    c.js('window.scrollTo({top:0,behavior:"instant"})');time.sleep(.2);c.shot(f'{theme}-full',True)
    results['contrast'][theme]=c.js(contrast_js)
print('Viewport checks and contrast:',json.dumps({'viewports':results['viewports'],'contrast':results['contrast']},ensure_ascii=False),flush=True)
# Theme survives navigation; system preference follows only without a saved override.
c.navigate();assert c.js('document.documentElement.dataset.theme')=='dark'
c.js('localStorage.removeItem("kakoe-media-theme")');c.call('Emulation.setEmulatedMedia',{'features':[{'name':'prefers-color-scheme','value':'dark'}]});c.navigate();assert c.js('document.documentElement.dataset.theme')=='dark'
c.call('Emulation.setEmulatedMedia',{'features':[{'name':'prefers-color-scheme','value':'light'}]});time.sleep(.1);assert c.js('document.documentElement.dataset.theme')=='light'
for index in range(7):
    c.js(f'document.querySelectorAll(".filter")[{index}].click()')
    assert c.js(f'document.querySelectorAll(".filter")[{index}].getAttribute("aria-pressed")')=='true'
    assert c.js('document.querySelectorAll(".gallery-card").length')>0
c.js('document.querySelector(".filter").click();while(!document.querySelector(".load-more").hidden)document.querySelector(".load-more").click()')
assert c.js('document.querySelectorAll(".gallery-card").length')==40
c.js('document.querySelector(".gallery-image-button").click()');assert c.js('document.querySelector(".lightbox").open')
before=c.js('document.querySelector(".lightbox-image").src');c.key('ArrowLeft',37)
assert c.js('document.querySelector(".lightbox-image").src')!=before
assert c.js('document.querySelector(".lightbox-caption").textContent.includes("40 / 40")')
c.key('ArrowRight',39);assert c.js('document.querySelector(".lightbox-image").src')==before
c.key('Escape',27);time.sleep(.1)
assert c.js('!document.querySelector(".lightbox").open && document.activeElement.classList.contains("gallery-image-button")')
for social in ['Telegram','Instagram']:
    c.js(f'document.querySelector("[data-social={social}]").click()')
    assert c.js('document.querySelector(".contact-dialog").open')
    assert social in c.js('document.querySelector("#contact-dialog-title").textContent')
    c.key('Escape',27)
# Pause, exact loop geometry and reduced motion.
c.js('document.querySelector(".ticker-pause").click()');assert c.js('getComputedStyle(document.querySelector(".ticker-track")).animationPlayState')=='paused'
assert c.js('document.querySelectorAll(".ticker-group")[0].innerHTML===document.querySelectorAll(".ticker-group")[1].innerHTML')
assert c.js('Math.abs(document.querySelector(".ticker-track").getBoundingClientRect().width / 2 - document.querySelector(".ticker-group").getBoundingClientRect().width)')<2
c.call('Emulation.setEmulatedMedia',{'features':[{'name':'prefers-reduced-motion','value':'reduce'}]})
assert c.js('getComputedStyle(document.querySelector(".ticker-track")).animationName')=='none'
# Check swipe direction: vertical gestures must not advance photos.
c.js('document.querySelector(".gallery-image-button").click()')
start=c.js('document.querySelector(".lightbox-image").src')
swipe="""(() => {const el=document.querySelector('.lightbox-image');const touch=(x,y)=>new Touch({identifier:1,target:el,clientX:x,clientY:y});el.dispatchEvent(new TouchEvent('touchstart',{touches:[touch(200,200)]}));el.dispatchEvent(new TouchEvent('touchend',{changedTouches:[touch(X,Y)]}));})()"""
c.js(swipe.replace('X,Y','205,320'));assert c.js('document.querySelector(".lightbox-image").src')==start
c.js(swipe.replace('X,Y','80,205'));assert c.js('document.querySelector(".lightbox-image").src')!=start
c.key('Escape',27)
# Optional localStorage must never break the theme or gallery.
blocked=c.call('Page.addScriptToEvaluateOnNewDocument',{'source':"Object.defineProperty(window,'localStorage',{get(){throw new Error('Storage disabled for audit')}});"})['identifier']
c.navigate();theme=c.js('document.documentElement.dataset.theme');c.js('document.querySelector(".theme-toggle").click()')
assert c.js('document.documentElement.dataset.theme')!=theme
assert c.js('document.querySelectorAll(".gallery-card").length')==6
c.call('Page.removeScriptToEvaluateOnNewDocument',{'identifier':blocked})
results['checks']=['swipes ignore vertical scrolling','storage disabled fallback','40 photos, 6 categories','light/dark at 7 widths','theme persistence and OS preference','modal arrows, wrapping, Escape, focus restoration','Telegram/Instagram placeholders','seamless ticker, pause, reduced motion']
# One repeatable lab sample on throttled mobile; not field Core Web Vitals.
c.viewport(375,812);c.call('Network.setCacheDisabled',{'cacheDisabled':True});c.call('Network.clearBrowserCache')
c.call('Network.emulateNetworkConditions',{'offline':False,'latency':150,'downloadThroughput':200000,'uploadThroughput':93750,'connectionType':'cellular4g'})
c.call('Emulation.setCPUThrottlingRate',{'rate':4});c.navigate();time.sleep(6)
results['performance']=c.js('({metrics:window.auditMetrics,resources:performance.getEntriesByType("resource").map(r=>({name:r.name,bytes:r.transferSize,duration:r.duration})),navigation:performance.getEntriesByType("navigation")[0].toJSON()})')
assert all(r['name'].startswith('http://127.0.0.1:8080/') for r in results['performance']['resources'])
results['errors']=[e for e in c.events if e.get('method')=='Runtime.exceptionThrown' or (e.get('method')=='Log.entryAdded' and e['params']['entry']['level']=='error')]
c.call('Network.emulateNetworkConditions',{'offline':False,'latency':0,'downloadThroughput':-1,'uploadThroughput':-1});c.call('Emulation.setCPUThrottlingRate',{'rate':1});c.call('Network.setCacheDisabled',{'cacheDisabled':False})
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('Checks:',results['checks']);print('Metrics:',results['performance']['metrics']);print('Bytes:',sum(r['bytes'] for r in results['performance']['resources']));print('Errors:',results['errors']);print('Report:',OUT/'results.json')
assert not results['errors'],results['errors']
assert not any(results['contrast'].values()),results['contrast']
assert not any(v['smallTargets'] for v in results['viewports'])
print('PASS')

const {chromium,devices}=require('playwright');
const [,,url,dir,MAX]=process.argv;
(async()=>{const b=await chromium.launch({proxy:{server:process.env.HTTPS_PROXY}});
const c=await b.newContext({...devices['iPhone 13']});const p=await c.newPage();
await p.goto(url,{waitUntil:'domcontentloaded',timeout:60000});await p.waitForTimeout(6000);
let last='',stuck=0,n=0;
for(let i=0;i<(+MAX||120);i++){
  const t=(await p.evaluate(()=>document.body.innerText)).replace(/\s+/g,' ').slice(0,400);
  const key=t.replace(/\d/g,'').slice(0,150);
  if(key===last){stuck++;}else{stuck=0;n++;last=key;console.log(n+' | '+t);await p.screenshot({path:`${dir}/${String(n).padStart(2,'0')}.png`});}
  if(stuck>6)break;
  if(/payment|card number|apple pay|google pay|start trial|get my plan|claim/i.test(t)&&/\$/.test(t)&&stuck>1)break;
  const inp=p.locator('input:visible:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=file])');
  for(let k=0;k<await inp.count();k++){const el=inp.nth(k);const ty=(await el.getAttribute('type'))||'';const ph=(await el.getAttribute('placeholder'))||'';
    let v='65'; if(ty==='email'||/mail/i.test(ph+t.slice(0,120)))v='anna'+Date.now()+'@yopmail.com'; else if(/name/i.test(ph+t.slice(0,80)))v='Anna'; else if(/height|tall|ft|cm/i.test(t.slice(0,150)))v=(k==0?'5':'6');
    try{if(!(await el.inputValue()))await el.fill(v,{timeout:1500})}catch(e){}}
  const fileInp=p.locator('input[type=file]');
  if(await fileInp.count() && stuck>0){ // try skip photo
    const sk=p.getByText(/skip|later|without photo|no photo/i).filter({visible:true}); if(await sk.count()){try{await sk.first().click({timeout:1500})}catch(e){}}}
  const head=t.slice(0,160);
  if(/how tall|your height|your weight|how much do you weigh|target weight/i.test(head)){
    const mt=p.getByText(/^(metric|cm|kg)$/i).filter({visible:true}); if(await mt.count()&&stuck===0){try{await mt.first().click({timeout:1500})}catch(e){}}
    const all=p.locator('input:visible'); const q=await all.count();
    for(let k=0;k<q;k++){const el=all.nth(k);try{await el.click({timeout:1500});await p.keyboard.press('Control+A');await p.keyboard.type(/weigh/i.test(head)?'62':'165',{delay:50})}catch(e){}}
    await p.waitForTimeout(600);
    const cont=p.locator('button:visible').filter({hasText:/continue|next/i}); if(await cont.count()){try{await cont.last().click({timeout:2000})}catch(e){}}
    await p.waitForTimeout(2000); continue;
  }
  const opts=p.locator('button:visible, [role=button]:visible, [role=radio]:visible, [role=checkbox]:visible, label:visible, li:visible');
  const m=await opts.count();let picked=false;
  const skipN = stuck; // try different option when stuck
  let seen=0;
  for(let k=0;k<m&&!picked;k++){const el=opts.nth(k);const tx=(await el.innerText().catch(()=>'')).trim();
    if(!tx||/continue|next|back|skip|privacy|terms|policy|contact|billing|money|menu/i.test(tx)||tx.length>90)continue;
    if(seen++<Math.min(skipN,2))continue;
    try{await el.click({timeout:1500});picked=true}catch(e){}}
  if(!picked&&stuck>=1){const im=p.locator('main img:visible, [class*=option] img:visible, [class*=card] img:visible, button img:visible');const q=await im.count();if(q){try{await im.nth(Math.min(stuck-1,q-1)).click({timeout:1500});picked=true}catch(e){}}}
  if(stuck>=1&&stuck<=3){try{await p.mouse.click(110,240+stuck*40)}catch(e){}}
  const sl=p.locator('input[type=range]:visible'); if(await sl.count()){try{await sl.first().focus();await p.keyboard.press('ArrowRight')}catch(e){}}
  await p.waitForTimeout(800);
  const cont=p.locator('button:visible, a:visible').filter({hasText:/continue|next|get|see|show|start|let|reveal|unlock|save|want|got it|yes|sure|go|try|discover|ok\b|done|view|claim/i});
  const ct=p.getByText(/^\s*(get started|continue|next|next step|start|let's go|got it|ok)\s*$/i).filter({visible:true});
  if(await cont.count()){try{await cont.last().click({timeout:2000})}catch(e){}}
  else if(await ct.count()){try{await ct.last().click({timeout:2000})}catch(e){}}
  else if(stuck>=2){const bb=p.locator('button:visible').filter({hasNotText:/privacy|terms|contact|support|help|assist|policy/i});const q=await bb.count();if(q){try{await bb.nth(q-1).click({timeout:2000})}catch(e){}}}
  await p.waitForTimeout(2200);
}
await b.close()})();

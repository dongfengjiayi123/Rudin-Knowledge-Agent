const {chromium}=require('playwright');
(async()=>{
 for(let i=0;i<40;i++){try{const r=await fetch('http://127.0.0.1:8000/api/status');if(r.ok)break}catch(e){} await new Promise(r=>setTimeout(r,250));}
 const b=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,headless:true,args:['--no-sandbox','--disable-gpu','--disable-dev-shm-usage']});
 const page=await b.newPage({viewport:{width:1480,height:1120}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8000');await page.waitForSelector('.node');await page.evaluate(()=>document.fonts.ready);
 await page.screenshot({path:'docs/preview.png',fullPage:true});
 if(!await page.locator('#detail').textContent().then(t=>t.includes('紧致集')))throw Error('Missing initial detail');
 await page.locator('#search').fill('一致连续');await page.waitForTimeout(500);await page.locator('#list .entry').first().click();
 await page.waitForFunction(()=>document.getElementById('detail').textContent.includes('δ 不能依赖'));
 await page.locator('button[data-tab="ask"]').click();await page.locator('#question').fill('紧致集');await page.locator('#send').click();
 await page.waitForFunction(()=>document.getElementById('answer').textContent.includes('本地检索模式'));
 await page.locator('button[data-tab="review"]').click();await page.waitForFunction(()=>document.getElementById('proposals').textContent.includes('暂无'));
 await page.setViewportSize({width:390,height:844});await page.locator('button[data-tab="atlas"]').click();await page.screenshot({path:'docs/mobile-preview.png',fullPage:true});
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth);
 await b.close();console.log(JSON.stringify({pageErrors:errors,mobileOverflow:overflow}));if(errors.length||overflow)process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});

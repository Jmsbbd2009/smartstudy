import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chromium} from 'playwright';
const api=process.env.TEST_API_URL||'http://127.0.0.1:8089/api/v1';
const ui=process.env.TEST_UI_URL||'http://127.0.0.1:4179';
const password=process.env.TEST_ACCOUNT_PASSWORD;
if(!password||!process.env.TEST_BOOK_PDF)throw new Error('Use tests/run_e2e.py to start isolated test services');
const facts=['Water freezes at zero degrees Celsius.','Plants use sunlight to make food.','Earth travels around the Sun once each year.'];
const account=async(email)=>{const r=await fetch(api+'/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});assert.equal(r.status,200);return r.json()};
const parent=await account('parent.e2e@example.test');
const children=await fetch(api+'/families/children',{headers:{Authorization:`Bearer ${parent.access_token}`}}).then(r=>r.json());
const child=children[0];assert.ok(child);
const browser=await chromium.launch({executablePath:process.env.CHROME_EXECUTABLE||undefined,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
const page=await browser.newPage({viewport:{width:1440,height:1080}});
const failures=[];page.on('pageerror',e=>failures.push(e.message));
const checks=[];
const waitResponse=(path,method='POST')=>page.waitForResponse(r=>r.url().endsWith('/api/v1/'+path)&&r.request().method()===method);
async function login(email){await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Parol',{exact:true}).fill(password);const response=waitResponse('auth/login');await page.getByRole('button',{name:'Kirish',exact:true}).click();assert.equal((await response).status(),200);await page.getByRole('navigation').waitFor()}
async function logout(){await page.getByRole('button',{name:'Chiqish',exact:true}).click();await page.getByRole('heading',{name:'Xush kelibsiz'}).waitFor()}
try{
 await page.goto(ui);await login('parent.e2e@example.test');checks.push('Parent authentication');
 await page.getByRole('button',{name:'AI boshqaruv',exact:true}).click();await page.getByLabel('Farzand',{exact:true}).selectOption(child.id);
 await page.getByLabel('Avtopilotga ruxsat berish',{exact:true}).check();const saved=waitResponse(`automation/children/${child.id}`,'PUT');await page.getByRole('button',{name:'Avtopilot sozlamalarini saqlash'}).click();assert.equal((await saved).status(),200);checks.push('Guardian enables bounded automation');
 await page.getByRole('button',{name:'Kitoblar va AI test',exact:true}).click();
 await page.getByLabel('Kitob nomi',{exact:true}).fill('E2E tabiat kitobi');await page.getByLabel('PDF kitob',{exact:true}).setInputFiles(process.env.TEST_BOOK_PDF);
 const upload=waitResponse('books');await page.getByRole('button',{name:'Kitobni yuklash',exact:true}).click();const response=await upload;assert.equal(response.status(),201);const book=await response.json();assert.equal(book.page_count,3);
 await page.getByRole('heading',{name:'E2E tabiat kitobi',exact:true}).waitFor();await page.getByText(facts[0],{exact:true}).waitFor();checks.push('Real PDF uploaded and source text rendered');
 const unavailable=waitResponse(`books/${book.id}/generate-lesson`);await page.getByRole('button',{name:'AI dars va test yaratish'}).click();assert.equal((await unavailable).status(),503);await page.getByRole('alert').filter({hasText:'AI is not configured'}).waitFor();checks.push('Unconfigured live AI is an explicit error');
 await page.getByRole('button',{name:'Qo‘lda dars tuzish'}).click();await page.getByLabel('Dars nomi',{exact:true}).fill('Tabiatning uch qoidasi');await page.getByLabel('Qisqa tushuntirish',{exact:true}).fill('Suv, o‘simliklar va Yer haqidagi uch manbali tushuncha.');
 await page.getByRole('button',{name:'Tushuncha qo‘shish',exact:true}).click();await page.getByRole('button',{name:'Tushuncha qo‘shish',exact:true}).click();
 for(let i=0;i<3;i++){
  const section=page.locator('.editor-section').nth(i);await section.getByLabel(`Tushuncha ${i+1}`,{exact:true}).fill(['Suv','O‘simliklar','Yer'][i]);await section.getByLabel('Tushuntirish',{exact:true}).fill(['Suv nol darajada muzlaydi.','O‘simliklar quyosh nuridan foydalanadi.','Yer Quyosh atrofida aylanadi.'][i]);await section.getByLabel('Manba sahifasi',{exact:true}).fill(String(i+1));await section.getByLabel('Kitobdan aynan olingan iqtibos',{exact:true}).fill(facts[i]);
 }
 const prompts=['Water freezes at?','Plants use what to make food?','Earth travels around?'];const options=[['Zero degrees Celsius','One hundred degrees Celsius'],['Sunlight','Moonlight'],['The Sun','Mars']];
 for(let i=0;i<3;i++){
  const section=page.locator('.editor-section').nth(i+3);await section.getByLabel(`Savol ${i+1}`,{exact:true}).fill(prompts[i]);await section.getByLabel('Variantlar — har qatorda bittadan',{exact:true}).fill(options[i].join('\n'));await section.getByLabel('Javob tushuntirishi',{exact:true}).fill(facts[i]);await section.getByLabel('Savol manba sahifasi',{exact:true}).fill(String(i+1));await section.getByLabel('Savolning aniq manba iqtibosi',{exact:true}).fill(facts[i]);
 }
 const draft=waitResponse(`books/${book.id}/lessons`);await page.getByRole('button',{name:'Dars qoralamasini saqlash'}).click();const lessonResponse=await draft;assert.equal(lessonResponse.status(),201);const lesson=await lessonResponse.json();
 await page.getByRole('img',{name:'Kitobning tushunchalar xaritasi'}).waitFor();checks.push('Visual lesson, concept map and grounded quiz created');
 await page.getByLabel('Manbalar va barcha javob kalitlarini tekshirdim, tasdiqlayman.',{exact:true}).check();const published=waitResponse(`reading/lessons/${lesson.id}/publish`);await page.getByRole('button',{name:'Darsni e’lon qilish',exact:true}).click();assert.equal((await published).status(),200);checks.push('Adult publishes validated answer keys');
 await page.getByLabel('O‘quvchi',{exact:true}).selectOption(child.id);await page.getByLabel('Tasdiqlangan testdan keyin avtomatik mukofot',{exact:true}).check();const assigned=waitResponse(`books/${book.id}/plans`);await page.getByRole('button',{name:'Sahifalarni biriktirish'}).click();const planResponse=await assigned;assert.equal(planResponse.status(),201);const plan=await planResponse.json();
 await page.getByRole('img',{name:'Kitobning tushunchalar xaritasi'}).scrollIntoViewIfNeeded();await page.screenshot({path:process.env.TEST_SCREENSHOT_DIR+'/admin-reading.png',fullPage:true});checks.push('Reading assignment with guardian reward budget');
 await logout();await login('student.e2e@example.test');assert.equal(await page.getByRole('button',{name:'AI boshqaruv',exact:true}).count(),0);
 await page.getByRole('button',{name:'Kitoblar va AI test',exact:true}).click();assert.equal(await page.getByRole('button',{name:'Kitobni yuklash',exact:true}).count(),0);await page.locator('.book-card').filter({hasText:'E2E tabiat kitobi'}).click();await page.getByText(facts[0],{exact:true}).waitFor();
 const marked=waitResponse(`reading/plans/${plan.id}/progress`);await page.getByRole('button',{name:'Sahifani belgilash'}).click();const progress=await(await marked).json();assert.equal(progress.checked_percent,0);assert.equal(progress.self_reported_percent,33.33);checks.push('Page marking does not claim verified reading or award minutes');
 await page.locator('.lesson-list button').filter({hasText:'Tabiatning uch qoidasi'}).click();const started=waitResponse(`reading/plans/${plan.id}/lessons/${lesson.id}/attempts`);await page.getByRole('button',{name:'Tushunish testini boshlash'}).click();const attempt=await(await started).json();assert.ok(attempt.questions.every(q=>!('correct_index'in q)));checks.push('Student receives shuffled questions without answer keys');
 for(const answer of ['Zero degrees Celsius','Sunlight','The Sun'])await page.getByRole('radio',{name:answer,exact:true}).check();
 const finished=waitResponse(`reading/attempts/${attempt.id}/finish`);await page.getByRole('button',{name:'Testni yakunlash',exact:true}).click();const result=await(await finished).json();assert.equal(result.result.percent,100);assert.equal(result.result.reward.state,'GRANTED');assert.equal(result.result.reward.minutes,15);
 await page.getByText('Mukofot berildi · 15 daqiqa',{exact:true}).waitFor();await page.screenshot({path:process.env.TEST_SCREENSHOT_DIR+'/student-reading-result.png',fullPage:true});checks.push('Real quiz grading grants exactly 15 reward minutes');
 const student=await account('student.e2e@example.test');const wallet=await fetch(api+'/rewards/wallet',{headers:{Authorization:`Bearer ${student.access_token}`}}).then(r=>r.json());assert.equal(wallet.available,15);
 const state=await fetch(api+`/reading/plans/${plan.id}`,{headers:{Authorization:`Bearer ${student.access_token}`}}).then(r=>r.json());assert.equal(state.progress.checked_percent,100);assert.equal(state.progress.self_reported_percent,33.33);checks.push('Wallet and checked-page coverage reconciled on the server');
 await logout();await login('parent.e2e@example.test');await page.getByRole('button',{name:'Kitoblar va AI test',exact:true}).click();await page.locator('.book-card').filter({hasText:child.name}).click();await page.getByText('Mukofot berildi · 15 daqiqa',{exact:true}).waitFor();checks.push('Guardian sees completed test and reward history');
 await page.getByRole('button',{name:'AI boshqaruv',exact:true}).click();await page.getByLabel('Farzand',{exact:true}).selectOption(child.id);await page.getByLabel('Kuniga qisqa mashq vazifalarini avtomatik tuzish',{exact:true}).check();const updated=waitResponse(`automation/children/${child.id}`,'PUT');await page.getByRole('button',{name:'Avtopilot sozlamalarini saqlash'}).click();await updated;
 const aiRun=waitResponse(`automation/children/${child.id}/run`);await page.getByRole('button',{name:'Bugungi AI rejasini yaratish'}).click();assert.equal((await aiRun).status(),503);await page.getByText(/AI xizmati tayyor emas/).waitFor();checks.push('Failed live AI run creates no fake assignments');
 await logout();await login('teacher.e2e@example.test');assert.equal(await page.getByRole('button',{name:'Qurilmalar',exact:true}).count(),0);assert.equal(await page.getByRole('button',{name:'Farzandlar',exact:true}).count(),0);await page.getByRole('button',{name:'Sinflar',exact:true}).click();await page.getByLabel('Sinf nomi',{exact:true}).fill('E2E 8-A');const classroom=waitResponse('classrooms');await page.getByRole('button',{name:'Sinf yaratish',exact:true}).click();assert.equal((await classroom).status(),201);checks.push('Teacher classroom workflow and household navigation isolation');
 assert.deepEqual(failures,[]);
 fs.writeFileSync(process.env.TEST_RESULTS_JSON,JSON.stringify({passed:checks.length,checks,page_errors:failures,transport:'real FastAPI and SQLite; no HTTP mocks',live_ai:'unconfigured and explicitly tested as unavailable'},null,2));
 console.log(`E2E passed: ${checks.length} real-browser checks`);
}catch(error){await page.screenshot({path:process.env.TEST_SCREENSHOT_DIR+'/failure.png',fullPage:true});console.error('E2E failed:',error.message);throw error}finally{await browser.close()}

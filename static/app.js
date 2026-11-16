(() => {
  const $ = (s) => document.querySelector(s);
  const ui = {
    history: $('#chatHistory'), messages: $('#messages'), welcome: $('#welcome'), input: $('#promptInput'),
    send: $('#sendButton'), file: $('#fileInput'), tray: $('#attachmentTray'), live: $('#liveActivity'),
    activity: $('#activityList'), activityTitle: $('#activityTitle'), auth: $('#authModal'),
  };
  const storeKey = 'clarity-local-v1';
  const state = { user: null, chats: [], chatId: null, selectedFile: null, mode: 'text',
    recording: false, recorder: null, chunks: [], audioBlob: null, recordStarted: 0, recordTimer: null, activityNodes: {}, busy: false, authMode: 'signin' };
  const nodeCopy = {
    process_input: ['Reading your message', 'Input prepared for the consultation'],
    understand_context: ['Understanding context', 'Groq is classifying your request and preparing its clinical context'],
    triage: ['Assessing urgency', 'Reviewing symptoms for urgent warning signs'],
    emergency_response: ['Preparing urgent guidance', 'Prioritizing immediate next steps'],
    web_research: ['Searching trusted health sources', 'Looking for relevant medical guidance online'],
    book_research: ['Checking medical references', 'Searching the clinical reference library'],
    root_cause: ['Connecting the evidence', 'Comparing your context with retrieved evidence'],
    synthesis: ['Writing your response', 'Preparing a clear summary and possible next steps'],
    medication_verifier: ['Reviewing medications', 'Checking medication information and cautions'],
    safety_guard: ['Final safety review', 'Reviewing the response for safety'],
  };
  async function api(path, options={}) {
    const response = await fetch(path, { credentials: 'same-origin', ...options,
      headers: { ...(options.body ? {'Content-Type':'application/json'} : {}), ...(options.headers||{}) } });
    const body = await response.json().catch(()=>({}));
    if (!response.ok) { const error=new Error(body.detail || body.message || `Request failed (${response.status})`); error.status=response.status; throw error; }
    return body;
  }

  function localData() { try { return JSON.parse(localStorage.getItem(storeKey) || '{"chats":[]}'); } catch { return { chats: [] }; } }
  function saveLocal(data) { localStorage.setItem(storeKey, JSON.stringify(data)); }
  function chatRecord(id = state.chatId) { return state.chats.find(c => c.id === id); }
  function uid() { return crypto.randomUUID ? crypto.randomUUID() : `chat_${Date.now()}_${Math.random().toString(36).slice(2,8)}`; }
  function escapeHtml(s='') { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function formatTime(s) { return new Date(s || Date.now()).toLocaleDateString(undefined, { month:'short', day:'numeric' }); }
  function toast(msg) { const t=$('#toast'); t.textContent=msg; t.classList.remove('hidden'); setTimeout(()=>t.classList.add('hidden'),3200); }

  async function init() {
    bind();
    try { state.user = (await api('/api/auth/session')).user; } catch { state.user = null; }
    updateAccount(); await loadChats();
    if (state.chats.length) await openChat(state.chats[0].id); else await newChat(false);
  }
  function bind() {
    $('#newChat').onclick=()=>newChat(true); $('#sendButton').onclick=sendMessage;
    ui.input.addEventListener('keydown', e=>{ if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage();} });
    ui.input.addEventListener('input',()=>{ui.input.style.height='auto';ui.input.style.height=Math.min(ui.input.scrollHeight,160)+'px';});
    $('#attachButton').onclick=()=>ui.file.click(); ui.file.onchange=()=>{if(ui.file.files[0])setFile(ui.file.files[0]);};
    ui.tray.onclick=e=>{if(e.target.closest('[data-remove]'))clearFile();};
    $('#textMode').onclick=()=>switchMode('text'); $('#audioMode').onclick=()=>switchMode('audio');
    $('#recordButton').onclick=toggleRecording;
    document.querySelectorAll('.suggestion').forEach(b=>b.onclick=()=>{switchMode('text');ui.input.value=b.dataset.prompt;ui.input.focus();});
    $('#signInTop').onclick=()=>openAuth(); $('#accountButton').onclick=()=>state.user?signOut():openAuth();
    $('#closeAuth').onclick=()=>ui.auth.classList.add('hidden'); ui.auth.onclick=e=>{if(e.target===ui.auth)ui.auth.classList.add('hidden');};
    $('#authSwitch').onclick=()=>setAuthMode(state.authMode==='signin'?'signup':'signin'); $('#authForm').onsubmit=authSubmit;
    $('#openSidebar').onclick=()=>$('#sidebar').classList.add('open'); $('#closeSidebar').onclick=()=>$('#sidebar').classList.remove('open');
    document.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();newChat(true);}});
  }
  function switchMode(mode) {
    if(state.busy)return;
    if(state.recording)stopRecording();
    if(mode==='text')state.audioBlob=null;
    state.mode=mode;
    const textMode=mode==='text';
    $('#textMode').classList.toggle('active',textMode);$('#textMode').setAttribute('aria-selected',String(textMode));
    $('#audioMode').classList.toggle('active',!textMode);$('#audioMode').setAttribute('aria-selected',String(!textMode));
    ui.input.classList.toggle('hidden',!textMode);$('#voiceInput').classList.toggle('hidden',textMode);
    if(textMode){ui.input.placeholder='Describe what’s going on…';}
    else if(!state.audioBlob){$('#voiceStatus').textContent='Tap to record a voice message';}
  }
  function updateAccount() {
    const signed=!!state.user, name=state.user?.email?.split('@')[0]||'Guest session';
    $('#accountName').textContent=name; $('#accountHint').textContent=signed?'Saved to this account':'Sign in to sync chats';
    $('#accountAvatar').textContent=name[0]?.toUpperCase()||'?'; $('#signInTop').textContent=signed?'':'Sign in';
    $('#signInTop').classList.toggle('hidden',signed);
  }
  async function loadChats() {
    if (state.user) {
      try { state.chats=(await api('/api/chats')).map(c=>({...c,messages:[]})); }
      catch { toast('Could not load your saved chats.'); state.chats=[]; }
    } else state.chats=localData().chats;
    renderHistory();
  }
  function renderHistory() {
    ui.history.innerHTML='';
    state.chats.forEach(chat=>{const row=document.createElement('div'); row.className='history-item'+(chat.id===state.chatId?' active':'');
      row.innerHTML=`<button class="history-open" type="button"><span class="history-icon">◷</span><span class="history-name">${escapeHtml(chat.title||'New conversation')}</span></button><button class="history-delete" type="button" aria-label="Delete chat" title="Delete chat">×</button>`;
      row.querySelector('.history-open').onclick=()=>openChat(chat.id); row.querySelector('.history-delete').onclick=()=>deleteChat(chat.id); ui.history.appendChild(row);});
  }
  async function createChat() {
    let chat={id:uid(),title:'New conversation',updated_at:new Date().toISOString(),messages:[]};
    if(state.user){try{chat={...(await api('/api/chats',{method:'POST',body:JSON.stringify({title:chat.title})})),messages:[]};}catch(error){console.error('Chat creation failed:',error);if(error.status===401){state.user=null;updateAccount();openAuth();toast('Your sign-in expired. Sign in again to save this chat.');}else toast(`Could not create a chat: ${error.message}`);return null;}}
    state.chats.unshift(chat); if(!state.user){saveLocal({chats:state.chats});} return chat;
  }
  async function newChat(focus=true) {
    if(state.busy)return;
    state.chatId=null;clearFile();state.audioBlob=null;ui.input.value='';ui.input.style.height='auto';$('#voiceStatus').textContent='Tap to record a voice message';$('#voiceDuration').textContent='';switchMode('text');ui.messages.innerHTML='';ui.welcome.classList.remove('hidden');
    ui.live.classList.add('hidden'); renderHistory(); $('#sidebar').classList.remove('open'); if(focus)ui.input.focus();
  }
  async function openChat(id) {
    state.chatId=id; const chat=chatRecord(id); ui.messages.innerHTML='';
    let messages=chat?.messages||[];
    if(state.user){try{messages=await api(`/api/chats/${encodeURIComponent(id)}/messages`);}catch{messages=[];toast('Could not load this chat.');}}
    if(chat)chat.messages=messages; messages.forEach(m=>renderMessage(m));
    // Older versions saved the user prompt before starting the agent but did
    // not save a failed assistant reply. Make that interrupted state visible
    // when reopening those conversations.
    if(messages.length&&messages[messages.length-1].role==='user')renderMessage({role:'assistant',content:'The previous run stopped before a reply was saved. Your prompt is still here; send it again to retry.',metadata:{failed:true,interrupted:true}});
    ui.welcome.classList.toggle('hidden',messages.length>0); ui.live.classList.add('hidden'); renderHistory();$('#sidebar').classList.remove('open');
  }
  async function deleteChat(id) {
    const chat=chatRecord(id); if(!chat)return;
    if(!confirm(`Delete “${chat.title||'New conversation'}”? This cannot be undone.`))return;
    if(state.user){try{await api(`/api/chats/${encodeURIComponent(id)}`,{method:'DELETE'});}catch(e){toast(`Could not delete chat: ${e.message}`);return;}}
    state.chats=state.chats.filter(c=>c.id!==id);if(!state.user)saveLocal({chats:state.chats});
    if(state.chatId===id){state.chatId=null;ui.messages.innerHTML='';ui.live.classList.add('hidden');ui.welcome.classList.remove('hidden');}
    renderHistory();toast('Chat deleted.');
  }
  async function persistMessage(role,content,metadata={}) {
    const chat=chatRecord(); if(!chat)return false;
    const item={id:uid(),role,content,metadata,created_at:new Date().toISOString()}; chat.messages ||= [];chat.messages.push(item);chat.updated_at=item.created_at;
    if(role==='user'&&chat.title==='New conversation')chat.title=content.slice(0,48)+(content.length>48?'…':'');
    state.chats.sort((a,b)=>new Date(b.updated_at)-new Date(a.updated_at));
    if(state.user){try{const saved=await api(`/api/chats/${encodeURIComponent(chat.id)}/messages`,{method:'POST',body:JSON.stringify({role,content,metadata})});item.id=saved.id;}
      catch{toast('Message could not be saved to chat history.');return false;}}
    else saveLocal({chats:state.chats});
    renderHistory(); return true;
  }
  function addMessage(role,content,meta={}) { const item={role,content,metadata:meta}; renderMessage(item); return item; }
  function renderMessage(item) {
    ui.welcome.classList.add('hidden'); const row=document.createElement('article');row.className=`message-row ${item.role}`;
    if(item.role==='user')row.innerHTML=`<div class="user-bubble">${escapeHtml(item.content).replace(/\n/g,'<br>')}</div>`;
    else row.innerHTML=`<div class="assistant-mark">✳</div><div class="assistant-body"><div class="assistant-label">CLARITY</div><div class="assistant-text">${escapeHtml(item.content||'').replace(/\n/g,'<br>')}</div>${item.metadata?.failed?'<div class="failed-run-label">Run failed · progress saved</div>':''}${item.metadata?.activity?.length?runNotesMarkup(item.metadata.activity):''}${item.metadata?.result?resultMarkup(item.metadata.result):''}</div>`;
    ui.messages.appendChild(row);ui.messages.scrollTop=ui.messages.scrollHeight;return row;
  }
  function runNotesMarkup(steps=[]) {
    const notes=steps.map(step=>`<details class="run-note"><summary><span>${step.failed?'!':'✓'}</span>${escapeHtml(step.title||'Agent phase')}</summary><div class="run-note-copy">${escapeHtml(step.detail||'')}</div>${step.output?`<pre>${escapeHtml(step.output)}</pre>`:''}</details>`).join('');
    return `<details class="run-notes"><summary>View analysis notes <span>${steps.length} phases</span></summary><div class="run-note-list">${notes}</div></details>`;
  }
  function activitySnapshot() {
    return [...ui.activity.children].map(item=>({
      title:item.querySelector('.step-copy strong')?.textContent||'Agent phase',
      detail:item.querySelector('.step-copy small')?.textContent||'',
      output:(item.querySelector('.phase-output pre')?.textContent||item.querySelector('.live-sources')?.textContent||'').trim().slice(0,1600),
      failed:!!item.querySelector('.failed-check'),
    }));
  }
  function resultMarkup(r) {
    const web=r.web_results||[],books=r.book_results||[],causes=r.possible_causes||r.differential?.possible_causes||[];
    const urgency=r.is_emergency?'Emergency':(r.urgency_level||'Routine');
    const fallbackText=r.synthesis_provider==='gemini'?'Groq was rate-limited; Gemini completed this summary.':'Groq was rate-limited and Gemini was unavailable; this summary uses the completed analysis.';
    return `<div class="result-summary"><div class="urgency-tag ${r.is_emergency?'danger':''}"><span>✳</span> ${escapeHtml(urgency)} assessment</div>${r.synthesis_fallback?`<div class="fallback-note">${fallbackText}</div>`:''}${causes.length?`<h3>Possibilities to discuss</h3><div class="possibility-list">${causes.map(c=>`<div class="possibility"><strong>${escapeHtml(c.name||'')}</strong><span>${escapeHtml(c.likelihood||'')}</span><p>${escapeHtml(c.explanation||'')}</p></div>`).join('')}</div>`:''}${r.differential?.care_steps?.length?`<h3>Supportive care</h3><ul>${r.differential.care_steps.map(x=>`<li><b>${escapeHtml(x.title||'')}</b> ${escapeHtml(x.instructions||'')}</li>`).join('')}</ul>`:''}${web.length?`<details class="evidence"><summary>Web research <span>${web.length} sources</span></summary>${web.map(w=>`<a class="evidence-card" href="${safeUrl(w.url)}" target="_blank" rel="noopener"><strong>${escapeHtml(w.title||domain(w.url)||'Health source')}</strong><small>${escapeHtml(domain(w.url))}</small><p>${escapeHtml((w.content||'').slice(0,420))}</p><span>Open source ↗</span></a>`).join('')}</details>`:''}${books.length?`<details class="evidence"><summary>Medical references <span>${books.length} excerpts</span></summary>${books.map((b,i)=>`<div class="evidence-card"><strong>${escapeHtml(b.metadata?.source||b.metadata?.filename||`Reference ${i+1}`)}</strong><p>${escapeHtml(b.content||'')}</p></div>`).join('')}</details>`:''}<div class="medical-note">This AI-generated information is for education and decision support, and does not replace care from a licensed clinician. ${escapeHtml(r.structured_response?.disclaimer||'For severe or rapidly worsening symptoms, contact emergency services.')}</div></div>`;
  }
  function safeUrl(s=''){try{const u=new URL(s);return ['https:','http:'].includes(u.protocol)?escapeHtml(u.href):'#';}catch{return '#';}}
  function domain(s=''){try{return new URL(s).hostname.replace(/^www\./,'');}catch{return '';}}
  function setFile(f){if(f.size>4*1024*1024){toast('Choose a document smaller than 4 MB for Vercel uploads.');ui.file.value='';return;}state.selectedFile=f;ui.tray.classList.remove('hidden');ui.tray.innerHTML=`<span class="file-chip">▧ ${escapeHtml(f.name)} <small>${(f.size/1024/1024).toFixed(1)} MB</small><button data-remove aria-label="Remove attachment">×</button></span>`;}
  function clearFile(){state.selectedFile=null;ui.file.value='';ui.tray.classList.add('hidden');ui.tray.innerHTML='';}
  async function toggleRecording(){
    if(state.recording){stopRecording();return;}
    try{const stream=await navigator.mediaDevices.getUserMedia({audio:true});state.chunks=[];const type=['audio/webm;codecs=opus','audio/webm','audio/mp4'].find(type=>MediaRecorder.isTypeSupported(type))||'';state.recorder=new MediaRecorder(stream,type?{mimeType:type}:undefined);
      state.recorder.ondataavailable=e=>{if(e.data.size)state.chunks.push(e.data);};state.recorder.onstop=()=>{state.recording=false;clearInterval(state.recordTimer);const blob=new Blob(state.chunks,{type:state.recorder.mimeType||'audio/webm'});state.audioBlob=state.mode==='audio'&&blob.size<=4*1024*1024?blob:null;stream.getTracks().forEach(t=>t.stop());$('#recordButton').classList.remove('recording');$('#recordButton').setAttribute('aria-label','Record again');$('#voiceStatus').textContent=blob.size>4*1024*1024?'Recording too large · please record a shorter message':state.audioBlob?'Voice message ready':'Tap to record a voice message';if(blob.size>4*1024*1024)toast('Keep voice messages under 4 MB for Vercel uploads.');};
      state.recorder.start();state.recording=true;state.audioBlob=null;state.recordStarted=Date.now();$('#recordButton').classList.add('recording');$('#recordButton').setAttribute('aria-label','Stop recording');$('#voiceStatus').textContent='Listening… tap to finish';
      state.recordTimer=setInterval(()=>{$('#voiceDuration').textContent=`${Math.floor((Date.now()-state.recordStarted)/1000)}s`;},250);
    }catch(e){toast('Please allow microphone access to record audio.');}
  }
  function stopRecording(){if(state.recorder&&state.recording&&state.recorder.state!=='inactive')state.recorder.stop();}
  async function sendMessage(){
    if(state.busy)return; const text=state.mode==='text'?ui.input.value.trim():'';
    if(state.recording){stopRecording();setTimeout(sendMessage,300);return;}
    if(!text&&!state.selectedFile&&!state.audioBlob){if(state.mode==='audio')toast('Record a voice message or attach a document first.');else ui.input.focus();return;}
    if(!state.chatId){const c=await createChat();if(!c)return;state.chatId=c.id;}
    const userText=text|| (state.audioBlob?'Voice message':`Attached ${state.selectedFile.name}`);
    const previous=chatRecord()?.messages||[]; const context=previous.slice(-12).map(m=>`${m.role==='user'?'User':'Assistant'}: ${m.content}`).join('\n');
    const prompt=context?`Conversation so far:\n${context}\n\nUser: ${text||'Please review my attached document or audio.'}`:text;
    const file=state.selectedFile,audio=state.audioBlob;renderMessage({role:'user',content:userText});await persistMessage('user',userText,{file:file?.name,audio:!!audio});
    ui.input.value='';ui.input.style.height='auto';clearFile();state.audioBlob=null;$('#voiceStatus').textContent='Tap to record a voice message';$('#voiceDuration').textContent='';$('#recordButton').classList.remove('recording');$('#recordButton').setAttribute('aria-label','Start recording');
    state.busy=true;state.runCompleted=false;state.activityNodes={};ui.send.disabled=true;ui.send.classList.add('sending');ui.live.classList.remove('hidden');ui.activity.innerHTML='';ui.activityTitle.textContent='Starting your consultation';$('#livePill').textContent='LIVE';$('#livePill').classList.remove('complete');
    const liveRow=document.createElement('article');liveRow.className='message-row assistant';liveRow.innerHTML='<div class="assistant-mark">✳</div><div class="assistant-body"><div class="assistant-label">CLARITY</div><div class="assistant-text stream-placeholder">Reviewing your message…</div></div>';ui.messages.appendChild(liveRow);ui.messages.scrollTop=ui.messages.scrollHeight;
    const form=new FormData();form.append('chat_id',state.chatId);form.append('prompt',prompt||'Please review the attached input.');form.append('prompt_type',audio?'audio':'text');if(file)form.append('file',file);if(audio)form.append('audio_file',audio, 'consultation.webm');
    try{const response=await fetch('/api/stream',{method:'POST',credentials:'same-origin',body:form});if(!response.ok)throw new Error((await response.text()).slice(0,300)||`HTTP ${response.status}`);
      await readEvents(response,liveRow);
    }catch(e){const content=`I couldn’t complete that request. ${e.message}`,activity=activitySnapshot();liveRow.querySelector('.assistant-body').innerHTML=`<div class="assistant-label">CLARITY</div><div class="assistant-text">${escapeHtml(content).replace(/\n/g,'<br>')}</div>${activity.length?runNotesMarkup(activity):''}`;const saved=await persistMessage('assistant',content,{failed:true,phase:e.phase||null,activity});toast(saved?'Consultation failed. Progress and error saved to this chat.':'Consultation failed. The error could not be saved; check chat storage.');}
    finally{state.busy=false;ui.send.disabled=false;ui.send.classList.remove('sending');ui.activityTitle.textContent=state.runCompleted?'All phases complete':'Run ended';$('#livePill').textContent=state.runCompleted?'COMPLETE':'ATTENTION';$('#livePill').classList.toggle('complete',state.runCompleted);$('.activity-spinner').classList.toggle('done',state.runCompleted);ui.live.classList.add('hidden');ui.messages.scrollTop=ui.messages.scrollHeight;}
  }
  async function readEvents(response,row){
    const reader=response.body.getReader(),decoder=new TextDecoder();let buffer='',result=null;
    while(true){const {done,value}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});let cut;
      while((cut=buffer.indexOf('\n\n'))>=0){const block=buffer.slice(0,cut);buffer=buffer.slice(cut+2);let event='message',data='';for(const line of block.split('\n')){if(line.startsWith('event:'))event=line.slice(6).trim();if(line.startsWith('data:'))data+=line.slice(5).trim();}
        if(!data)continue;const payload=JSON.parse(data);if(event==='activity')showActivity(payload);else if(event==='step')showStep(payload);else if(event==='result')result=payload;else if(event==='error'){showFailure(payload);const error=new Error(payload.message||'Agent run failed');error.phase=payload.phase;throw error;}
      }
    }
    if(!result)throw new Error('The server closed the progress stream before returning a result.');
    const content=result.response||'I couldn’t find a response for this request.', activity=activitySnapshot();row.querySelector('.assistant-body').innerHTML=`<div class="assistant-label">CLARITY</div><div class="assistant-text">${escapeHtml(content).replace(/\n/g,'<br>')}</div>${activity.length?runNotesMarkup(activity):''}${result.is_medical===false?'<div class="medical-note">This assistant can only help with health-related questions.</div>':resultMarkup(result)}`;
    await persistMessage('assistant',content,{result,activity});state.runCompleted=true;
  }
  function showStep(e){
    const [title,detail]=state.mode==='audio'&&e.node==='process_input'?['Voice transcription complete','Preparing your transcribed message for review']:nodeCopy[e.node]||[e.node.replaceAll('_',' '),'Working on this part of your consultation'];
    ui.activityTitle.textContent=title;
    const item=state.activityNodes[e.node]||document.createElement('div');item.className='activity-step';item.innerHTML=`<span class="step-check">✓</span><span class="step-copy"><strong>${escapeHtml(title)}</strong><small>${escapeHtml(detail)}</small></span>`;
    // Show actual retrieved evidence immediately as each research branch completes.
    const out=e.output||{};
    const provider=out.provider_used||(e.node==='synthesis'?out.synthesis_provider:null);
    const providerNote=provider==='gemini'?'Provider: Gemini fallback\n\n':provider==='rules'?'Provider: local safety rules\n\n':provider==='local'?'Provider: local safety fallback\n\n':'';
    const phaseText=providerNote+phaseOutputText(e.node,out);
    if(phaseText){const result=document.createElement('div');result.className='phase-output';result.innerHTML='<strong>Phase output</strong><pre></pre>';result.querySelector('pre').textContent=phaseText;item.appendChild(result);item.classList.add('with-sources');}
    if(e.node==='web_research'&&out.web_results?.length){const sources=out.web_results;item.classList.add('with-sources');item.innerHTML+=`<div class="live-sources"><div class="live-source-label">${sources.length} pages found</div>${sources.slice(0,4).map(s=>`<a href="${safeUrl(s.url)}" target="_blank" rel="noopener"><strong>${escapeHtml(s.title||domain(s.url)||'Source')}</strong><small>${escapeHtml(domain(s.url))}</small><p>${escapeHtml((s.content||'').slice(0,190))}${(s.content||'').length>190?'…':''}</p></a>`).join('')}</div>`;}
    if(e.node==='book_research'&&out.book_results?.length){item.classList.add('with-sources');item.innerHTML+=`<div class="live-sources"><div class="live-source-label">${out.book_results.length} reference excerpts</div>${out.book_results.slice(0,4).map((b,i)=>`<div class="live-book"><strong>${escapeHtml(b.metadata?.source||b.metadata?.filename||`Reference ${i+1}`)}</strong><p>${escapeHtml((b.content||'').slice(0,220))}${(b.content||'').length>220?'…':''}</p></div>`).join('')}</div>`;}
    const retrievalError=out.web_research_error||out.book_research_error;
    if(retrievalError){item.classList.add('with-sources');item.innerHTML+=`<small class="live-research-error">${escapeHtml(retrievalError)} The consultation will continue.</small>`;}
    const expandable=[...item.querySelectorAll(':scope > .phase-output, :scope > .live-sources, :scope > .live-research-error')];
    if(expandable.length){const details=document.createElement('details');details.className='phase-details';const summary=document.createElement('summary');summary.textContent=e.node==='web_research'?'View retrieved pages':e.node==='book_research'?'View reference excerpts':'View phase notes';details.appendChild(summary);expandable.forEach(node=>details.appendChild(node));item.appendChild(details);}
    if(!item.isConnected)ui.activity.appendChild(item);state.activityNodes[e.node]=item;
    ui.messages.scrollTop=ui.messages.scrollHeight;
  }
  function phaseOutputText(node,out){
    if(node==='process_input'&&out.transcription)return `Voice transcript\n${out.transcription}`;
    if(node==='understand_context')return out.is_medical===false?(out.response||'This request is not health related.'):(out.structured_prompt||'');
    if(node==='triage'&&out.triage){const t=out.triage;return [`Urgency: ${t.urgency_level||'unknown'}`,t.reasoning||'',...(t.flags||[]).map(f=>`• ${f.category||'Flag'}: ${f.flag||''}`),t.emergency_guidance||''].filter(Boolean).join('\n');}
    if(node==='emergency_response'&&out.final_response)return out.final_response;
    if(node==='root_cause'&&out.differential){const d=out.differential;return [`${d.primary_impression||'Differential assessment'}`,...(d.possible_causes||[]).map(c=>`• ${c.name} (${c.likelihood}) — ${c.explanation}`),...(d.care_steps||[]).map(c=>`Care: ${c.title} — ${c.instructions}`)].join('\n');}
    if(node==='synthesis'&&out.draft_response)return `${out.synthesis_fallback&&out.synthesis_provider==='local'?'Gemini was unavailable too; this summary uses completed analysis.\n\n':''}${out.draft_response}`;
    if(node==='medication_verifier'&&out.medication_check){const m=out.medication_check;return [`Medications mentioned: ${m.has_medication_mention?'yes':'no'}`,...(m.medicines_identified||[]).map(x=>`• ${x.brand_name||x.generic_name}: ${x.generic_name} (${x.drug_class})`),...(m.warnings||[]).map(w=>`Caution (${w.severity}): ${w.message}`),m.pharmacist_note||''].filter(Boolean).join('\n');}
    if(node==='safety_guard'&&out.safety_review){const s=out.safety_review;return [`Safety review: ${s.is_safe?'passed':'changes applied'}`,...(s.modifications_made||[]).map(x=>`• ${x}`),out.final_structured_response?.summary||''].filter(Boolean).join('\n');}
    return '';
  }
  function showActivity(e){
    const audio=state.mode==='audio'&&e.node==='process_input';
    const [title,detail]=audio?['Transcribing your voice message','Converting the recording to text']:nodeCopy[e.node]||['Working on your message','Preparing the consultation'];
    ui.activityTitle.textContent=title;
    if(!state.activityNodes[e.node]){const item=document.createElement('div');item.className='activity-step active';item.innerHTML=`<span class="step-check"></span><span class="step-copy"><strong>${escapeHtml(title)}</strong><small>${escapeHtml(detail)}</small></span>`;ui.activity.appendChild(item);state.activityNodes[e.node]=item;}
    ui.messages.scrollTop=ui.messages.scrollHeight;
  }
  function showFailure(e){
    const title=(e.phase||'Agent').replaceAll('_',' '), item=state.activityNodes[e.phase];
    if(item){item.classList.remove('active');const check=item.querySelector('.step-check');if(check){check.textContent='!';check.classList.add('failed-check');}}
    const target=item||document.createElement('div');if(!item){target.className='activity-step failed-step';target.innerHTML=`<span class="step-check failed-check">!</span><span class="step-copy"><strong>${escapeHtml(title)}</strong><small>This phase could not finish.</small></span>`;ui.activity.appendChild(target);}
    const output=document.createElement('div');output.className='phase-output';output.innerHTML='<strong>Phase error</strong><pre></pre>';output.querySelector('pre').textContent=e.message||'The phase failed.';target.appendChild(output);
  }
  function openAuth(){ui.auth.classList.remove('hidden');}
  function setAuthMode(mode){state.authMode=mode;const sign=mode==='signin';$('#authTitle').textContent=sign?'Welcome to Clarity':'Create your account';$('#authSubtitle').textContent=sign?'Sign in to securely save and revisit your conversations.':'Create a private space for your health conversations.';$('#authSubmit').textContent=sign?'Sign in':'Create account';$('#authSwitch').textContent=sign?'New here? Create an account':'Already have an account? Sign in';$('#authFeedback').textContent='';}
  async function authSubmit(e){e.preventDefault();const feedback=$('#authFeedback');feedback.textContent='';const email=$('#authEmail').value,password=$('#authPassword').value;
    try{const data=await api(`/api/auth/${state.authMode==='signin'?'login':'signup'}`,{method:'POST',body:JSON.stringify({email,password})});
      state.user=data.user;ui.auth.classList.add('hidden');updateAccount();await loadChats();await newChat(false);toast(state.authMode==='signin'?'Signed in successfully.':'Account created.');}
    catch(error){feedback.textContent=error.message;}
  }
  async function signOut(){try{await api('/api/auth/logout',{method:'POST'});}catch{}state.user=null;state.chats=[];state.chatId=null;updateAccount();await loadChats();await newChat(false);toast('You’re signed out.');}
  init();
})();

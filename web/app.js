const $ = id => document.getElementById(id);
let history = [], busy = false;
function state(value, label) { $('mirror').dataset.state = value; $('status').textContent = label; }
function browserVoice(text) {
  return new Promise(resolve => {
    if (!('speechSynthesis' in window)) return resolve();
    const speech = new SpeechSynthesisUtterance(text);
    speech.rate = .88; speech.pitch = .7;
    speech.onstart = () => state('speaking', 'The mirror speaks');
    speech.onend = speech.onerror = resolve;
    window.speechSynthesis.speak(speech);
  });
}
async function speak(text) {
  let url;
  try {
    const response = await fetch('/api/tts', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text})});
    if (!response.ok) throw new Error('Use browser voice');
    url = URL.createObjectURL(await response.blob());
    const audio = new Audio(url);
    await new Promise((resolve,reject) => {audio.onended=resolve; audio.onerror=reject; audio.onplaying=()=>state('speaking','The mirror speaks');audio.play().catch(reject);});
  } catch { await browserVoice(text); }
  finally { if(url) URL.revokeObjectURL(url); }
}
$('form').onsubmit = async event => {
  event.preventDefault(); if(busy) return;
  const question = $('question').value.trim(); if(!question) return;
  busy = true; $('ask').disabled = $('listen').disabled = $('reset').disabled = true;
  state('thinking', 'The mirror is pondering…'); $('answer').textContent = '';
  try {
    const messages = [...history, {role:'user', content:question}].slice(-19);
    const response = await fetch('/api/chat', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages})});
    const result = await response.json(); if(!response.ok) throw new Error(result.error);
    history = [...messages,{role:'assistant',content:result.text}].slice(-18);
    $('answer').textContent = result.text; $('question').value = '';
    await speak(result.text); state('idle','Awaiting your question');
  } catch(error) { state('idle','Unable to reach the mirror'); $('answer').textContent = error.message; }
  finally { busy=false; $('ask').disabled=$('listen').disabled=$('reset').disabled=false; }
};
$('reset').onclick = () => {history=[];$('answer').textContent='';state('idle','A new tale begins');};
$('full').onclick = () => document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen().catch(()=>{});
const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if(Recognition){
  const recognition = new Recognition(); recognition.lang='en-US'; recognition.interimResults=false;
  $('listen').onclick = () => {if(!busy){try{recognition.start();state('listening','Listening…');}catch{state('idle','Microphone already active');}}};
  recognition.onresult = event => {$('question').value=event.results[0][0].transcript;$('form').requestSubmit();};
  recognition.onerror = event => state('idle',`Microphone: ${event.error}. Please type your question.`);
  recognition.onend = () => {if(!busy) state('idle','Awaiting your question');};
} else { $('listen').hidden=true; }

import test from 'node:test';import assert from 'node:assert/strict';
import worker from '../worker.mjs';
const BEARER='testsecret'.repeat(5);
function mkKV(){const m=new Map();return {get:async k=>JSON.parse(m.get(k)||'null'),put:async(k,v)=>m.set(k,v),store:m}}
function setup({privacy='private',channelId='UCCorrectChannel'}={}){
 const calls=[];const kv=mkKV();const env={MCP_API_KEY:BEARER,GOOGLE_CLIENT_ID:'id',GOOGLE_CLIENT_SECRET:'secret',GOOGLE_REFRESH_TOKEN:'refresh',EXPECTED_CHANNEL_ID:'UCCorrectChannel',UPLOADS_KV:kv};
 const old=globalThis.fetch;globalThis.fetch=async(url,init={})=>{
  url=String(url);calls.push({url,method:init.method||'GET'});
  const data=(o,status=200,h={})=>new Response(JSON.stringify(o),{status,headers:{'Content-Type':'application/json',...h}});
  if(url.includes('oauth2.googleapis.com/token'))return data({access_token:'access'});
  if(url.includes('/youtube/v3/channels?'))return data({items:[{id:channelId,snippet:{title:'Test channel'},contentDetails:{relatedPlaylists:{uploads:'UU123'}}}]});
  if(url.includes('/drive/v3/files/')&&!url.includes('alt=media'))return data({id:'1234567890',name:'x.mp4',size:'5',mimeType:'video/mp4',trashed:false});
  if(url.includes('/drive/v3/files/')&&url.includes('alt=media'))return new Response(Buffer.from('HELLO'),{status:206,headers:{'Content-Type':'video/mp4'}});
  if(url.includes('uploadType=resumable'))return new Response('',{status:200,headers:{Location:'https://www.googleapis.com/upload/youtube/v3/videos?upload_id=x'}});
  if(url.includes('upload_id=x'))return data({id:'YT123'});
  if(url.includes('/youtube/v3/videos?part=status'))return data({items:[{status:{privacyStatus:privacy}}]});
  if(url.includes('/youtube/v3/playlistItems?'))return data({items:[{contentDetails:{videoId:'YT123'}}]});
  if(url.includes('/youtube/v3/videos?part=snippet'))return data({items:[{id:'YT123',snippet:{title:'Test'},status:{privacyStatus:'private'}}]});
  throw Error('Unexpected URL '+url);
 };
 return {env,calls,kv,restore(){globalThis.fetch=old}};
}
const call=(env,id,name,args)=>worker.fetch(new Request('https://dummy.example/mcp',{method:'POST',headers:{Authorization:'Bearer '+BEARER,'Content-Type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id,method:'tools/call',params:{name,arguments:args}})}),env).then(x=>x.json());
const args={drive_file_id:'1234567890',title:'AD&C Test',description:'',made_for_kids:false,request_key:'ADNC_test_20261020'};
test('unauthenticated requests are blocked',async()=>{const t=setup();try{const r=await worker.fetch(new Request('https://dummy.example/mcp',{method:'POST'}),t.env);assert.equal(r.status,401)}finally{t.restore()}});
test('chat upload is verified private, recorded once, and not duplicated',async()=>{const t=setup();try{const r=await call(t.env,1,'upload_private_from_drive',args);assert.equal(r.result.structuredContent.state,'private_verified');assert.equal(r.result.structuredContent.url,'https://www.youtube.com/watch?v=YT123');
const again=await call(t.env,2,'upload_private_from_drive',args);assert.equal(again.result.structuredContent.state,'private_verified');assert.equal(t.calls.filter(x=>x.url.includes('uploadType=resumable')).length,1);}
finally{t.restore()}});
test('channel mismatch aborts before upload',async()=>{const t=setup({channelId:'UCOtherChannel'});try{const r=await call(t.env,1,'upload_private_from_drive',args);assert.equal(r.result.isError,true);assert.match(r.result.content[0].text,/does not match/);assert.equal(t.calls.filter(x=>x.url.includes('uploadType=resumable')).length,0)}finally{t.restore()}});
test('if not private, never report success and never retry using same key',async()=>{const t=setup({privacy:'unlisted'});try{const r=await call(t.env,1,'upload_private_from_drive',args);assert.equal(r.result.isError,true);assert.match(r.result.content[0].text,/visibility verification failed/);
const retry=await call(t.env,2,'upload_private_from_drive',args);assert.equal(retry.result.structuredContent.state,'needs_manual_check');assert.equal(t.calls.filter(x=>x.url.includes('uploadType=resumable')).length,1)}finally{t.restore()}});
test('list tool returns video status and link',async()=>{const t=setup();try{const r=await call(t.env,1,'list_uploaded_videos',{limit:10});assert.equal(r.result.structuredContent.videos[0].url,'https://www.youtube.com/watch?v=YT123')}finally{t.restore()}});

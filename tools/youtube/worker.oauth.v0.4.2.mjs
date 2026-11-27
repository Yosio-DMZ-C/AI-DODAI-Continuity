/** AD&C YouTube MCP bridge v0.1. Private upload from owner's Drive, never publishes. */
const BASE='https://www.googleapis.com';
const CHUNK=8*1024*1024; // YouTube resumable upload uses 256KiB-aligned chunks.
const MAX_FILE=128*1024*1024;
const PROTOCOL='2025-03-26';
const json=(obj,status=200,extra={})=>new Response(JSON.stringify(obj),{status,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store',...extra}});
const rpc=(id,result)=>json({jsonrpc:'2.0',id,result});
const rpcError=(id,code,message)=>json({jsonrpc:'2.0',id,error:{code,message}});
const bad=(message)=>({content:[{type:'text',text:'ERROR: '+message}],isError:true});
const ok=(data)=>({content:[{type:'text',text:JSON.stringify(data,null,2)}],structuredContent:data,isError:false});
const esc=(s)=>encodeURIComponent(s);
const valid=(s,n=120)=>typeof s==='string'&&s.length>=1&&s.length<=n;
function validGoogleId(s){return typeof s==='string'&&/^[\w-]{10,120}$/.test(s)}
function checkAuth(req,env){const auth=req.headers.get('Authorization')||'';const expected=env.MCP_API_KEY;if(!expected||expected.length<32||!auth.startsWith('Bearer '))return false;const x=auth.slice(7);if(x.length!==expected.length)return false;let diff=0;for(let i=0;i<x.length;i++)diff|=x.charCodeAt(i)^expected.charCodeAt(i);return diff===0;}
async function token(env){if(!env.GOOGLE_CLIENT_ID||!env.GOOGLE_CLIENT_SECRET||!env.GOOGLE_REFRESH_TOKEN)throw Error('Google OAuth secrets are not configured');
 const r=await fetch('https://oauth2.googleapis.com/token',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({client_id:env.GOOGLE_CLIENT_ID,client_secret:env.GOOGLE_CLIENT_SECRET,refresh_token:env.GOOGLE_REFRESH_TOKEN,grant_type:'refresh_token'})});
 const data=await r.json();if(!r.ok||!data.access_token)throw Error('Google refresh token rejected: '+(data.error||r.status));return data.access_token;}
async function google(url,tok,init={}){const r=await fetch(url,{...init,headers:{Authorization:'Bearer '+tok,...(init.headers||{})}});if(!r.ok){let detail='';try{detail=(await r.json()).error?.message||''}catch{}throw Error('Google HTTP '+r.status+': '+detail)}return r.json()}
async function verifyVideo(id,tok){const x=await google(`${BASE}/youtube/v3/videos?part=status&id=${esc(id)}`,tok);return x.items?.[0]?.status?.privacyStatus||null}
async function uploadPrivate(args,env){
 const {drive_file_id,title,description='',made_for_kids,request_key}=args||{};
 if(!validGoogleId(drive_file_id)||!valid(title,100)||typeof description!=='string'||description.length>5000||typeof made_for_kids!=='boolean'||!valid(request_key,100)||!/^[a-zA-Z0-9_-]{8,100}$/.test(request_key))
  throw Error('invalid arguments: drive_file_id, title, made_for_kids, request_key are required');
 if(!env.UPLOADS_KV)throw Error('UPLOADS_KV binding missing. Idempotency protection is required');
 if(!env.EXPECTED_CHANNEL_ID)throw Error('EXPECTED_CHANNEL_ID must be configured before uploading');
 const key='upload:'+request_key;const exists=await env.UPLOADS_KV.get(key,'json');
 if(exists){if(exists.drive_file_id!==drive_file_id)throw Error('request_key already used for another file');return {state:exists.state,drive_file_id,request_key,video_id:exists.video_id||null,url:exists.video_id?`https://www.youtube.com/watch?v=${exists.video_id}`:null,detail:exists.detail||'Previous request recorded. Reuse same key only after investigation.'}}
 // Do not risk a duplicate by automatically retrying an upload after network uncertainty.
 await env.UPLOADS_KV.put(key,JSON.stringify({state:'started',drive_file_id,started:new Date().toISOString()}));
 try{
  const tok=await token(env);
  const mine=await google(`${BASE}/youtube/v3/channels?mine=true&part=id,snippet`,tok);
  const currentChannel=mine.items?.[0];
  if(!currentChannel?.id||currentChannel.id!==env.EXPECTED_CHANNEL_ID)throw Error('Authenticated YouTube channel does not match EXPECTED_CHANNEL_ID: '+(currentChannel?.id||'not found'));
  const meta=await google(`${BASE}/drive/v3/files/${esc(drive_file_id)}?fields=id,name,mimeType,size,trashed&supportsAllDrives=true`,tok);
  const size=Number(meta.size);
  if(meta.trashed||!Number.isSafeInteger(size)||size<1||size>MAX_FILE||!String(meta.mimeType).startsWith('video/'))throw Error('Drive file must be an untrashed video file of 1–128 MiB');
  const init=await fetch(`${BASE}/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status`,{method:'POST',headers:{Authorization:'Bearer '+tok,'Content-Type':'application/json','X-Upload-Content-Length':String(size),'X-Upload-Content-Type':meta.mimeType},body:JSON.stringify({snippet:{title,description,categoryId:'28'},status:{privacyStatus:'private',selfDeclaredMadeForKids:made_for_kids}})});
  if(!init.ok)throw Error('YouTube init HTTP '+init.status);
  const location=init.headers.get('Location');if(!location)throw Error('YouTube resumable upload missing Location');
  const u=new URL(location);if(u.protocol!=='https:'||!['www.googleapis.com','youtube.googleapis.com'].includes(u.hostname)||!u.pathname.startsWith('/upload/youtube/'))throw Error('unexpected YouTube upload host');
  let output=null;
  for(let start=0;start<size;start+=CHUNK){const end=Math.min(start+CHUNK,size)-1;
   const chunk=await fetch(`${BASE}/drive/v3/files/${esc(drive_file_id)}?alt=media`,{headers:{Authorization:'Bearer '+tok,Range:`bytes=${start}-${end}`}});
   if(chunk.status!==206 && !(chunk.status===200 && start===0 && size<=CHUNK))throw Error('Drive range request failed: HTTP '+chunk.status+'; avoid blind retry');
   const bytes=await chunk.arrayBuffer();if(bytes.byteLength!==end-start+1)throw Error('Drive returned unexpected byte range size');
   const push=await fetch(location,{method:'PUT',headers:{Authorization:'Bearer '+tok,'Content-Type':meta.mimeType,'Content-Range':`bytes ${start}-${end}/${size}`},body:bytes});
   if(push.status===308){if(end===size-1)throw Error('final YouTube chunk incomplete');continue}
   if(push.ok){output=await push.json();if(end!==size-1)throw Error('YouTube ended upload early');break}
   throw Error('YouTube chunk failed: HTTP '+push.status+'; review existing upload before retry');
  }
  if(!output?.id)throw Error('YouTube video id not returned');
  // A response alone is not sufficient: verify actual current visibility via videos.list.
  const privacy=await verifyVideo(output.id,tok);
  if(privacy!=='private')throw Error('YouTube visibility verification failed: '+privacy);
  const record={state:'private_verified',drive_file_id,video_id:output.id,request_key,verified:new Date().toISOString()};
  await env.UPLOADS_KV.put(key,JSON.stringify(record));return {...record,url:`https://www.youtube.com/watch?v=${output.id}`,channel_id:currentChannel.id,manage_url:env.MANAGEMENT_URL?.startsWith('https://')?env.MANAGEMENT_URL:null,after_upload:'この画面から更新してください（公開範囲は必ず人間が管理ページで変更）'};
 }catch(e){await env.UPLOADS_KV.put(key,JSON.stringify({state:'needs_manual_check',drive_file_id,detail:String(e.message),request_key,failed:new Date().toISOString()}));throw e}
}
async function checkConnection(env){
 const missing=['GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET','GOOGLE_REFRESH_TOKEN','MCP_API_KEY','EXPECTED_CHANNEL_ID'].filter(k=>!env[k]);
 if(!env.UPLOADS_KV)missing.push('UPLOADS_KV');
 if(missing.length)return {state:'not_ready',missing,action:'初回認証手順書を表示し、Google CloudとCloudflareの設定を案内してください。'};
 const tok=await token(env);
 const x=await google(`${BASE}/youtube/v3/channels?mine=true&part=id,snippet`,tok);
 const c=x.items?.[0];
 if(!c?.id)return {state:'not_ready',reason:'authenticated_youtube_channel_not_found'};
 if(c.id!==env.EXPECTED_CHANNEL_ID)return {state:'channel_mismatch',actual_channel_id:c.id,expected_channel_id:env.EXPECTED_CHANNEL_ID,action:'チャンネルIDが一致するまでアップロード不可'};
 return {state:'ready',channel_id:c.id,channel_name:c.snippet?.title||'',upload_mode:'private_only',human_publication_required:true,management_url:env.MANAGEMENT_URL?.startsWith('https://')?env.MANAGEMENT_URL:null};
}
async function listVideos(args,env){const tok=await token(env);const ch=await google(`${BASE}/youtube/v3/channels?mine=true&part=snippet,contentDetails`,tok);const item=ch.items?.[0];
 if(!item?.id)throw Error('YouTube channel not found');if(!env.EXPECTED_CHANNEL_ID||item.id!==env.EXPECTED_CHANNEL_ID)throw Error('Channel mismatch or EXPECTED_CHANNEL_ID missing');const pl=item.contentDetails?.relatedPlaylists?.uploads;if(!pl)throw Error('uploads playlist not found');
 const limit=Math.min(50,Math.max(1,Number(args?.limit||20)));const response=await google(`${BASE}/youtube/v3/playlistItems?part=contentDetails&maxResults=${limit}&playlistId=${esc(pl)}`,tok);
 const ids=(response.items||[]).map(x=>x.contentDetails?.videoId).filter(Boolean);if(!ids.length)return {channel:item.snippet?.title||'',channel_id:item.id,videos:[]};
 const videos=await google(`${BASE}/youtube/v3/videos?part=snippet,status&id=${esc(ids.join(','))}`,tok);
 return {channel:item.snippet?.title||'',channel_id:item.id,manage_url:env.MANAGEMENT_URL?.startsWith('https://')?env.MANAGEMENT_URL:null,videos:(videos.items||[]).map(x=>({id:x.id,title:x.snippet?.title,privacy_status:x.status?.privacyStatus,upload_status:x.status?.uploadStatus,url:`https://www.youtube.com/watch?v=${x.id}`})),has_more:Boolean(response.nextPageToken)};
}
const defs=[{name:'upload_private_from_drive',title:'Drive動画をYouTubeへ非公開登録',description:'Upload an existing Google Drive video to the authorized YouTube channel. ALWAYS private; never unlisted/public. Requires explicit user instruction. request_key is stable across retried chat tool calls.',inputSchema:{type:'object',additionalProperties:false,required:['drive_file_id','title','made_for_kids','request_key'],properties:{drive_file_id:{type:'string',description:'Owned Google Drive video file ID (not an arbitrary URL)'},title:{type:'string',maxLength:100},description:{type:'string',maxLength:5000},made_for_kids:{type:'boolean',description:'True only when user says the video is made for kids'},request_key:{type:'string',pattern:'^[a-zA-Z0-9_-]{8,100}$',description:'User-task unique stable idempotency key'}}}},
{name:'check_connection',title:'初回認証・接続状態の確認',description:'Check OAuth, Worker secrets, KV and the expected YouTube channel without uploading or changing publication status. Returns only non-secret status.',inputSchema:{type:'object',properties:{},additionalProperties:false}},
{name:'list_uploaded_videos',title:'YouTube登録済み動画一覧',description:'List owned channel recent videos, visibility, URL. No visibility changes.',inputSchema:{type:'object',properties:{limit:{type:'integer',minimum:1,maximum:50}},additionalProperties:false}}];
export default {async fetch(req,env){const u=new URL(req.url);
 const authReply=await handleGoogleBrowserOAuth(req,env);if(authReply)return authReply;
 if(u.pathname==='/health'&&req.method==='GET')return json({name:'ADNC YouTube MCP',version:'0.1.0',status:'unconfigured_or_configured_not_disclosed'});
 if(u.pathname!=='/mcp')return json({error:'not_found'},404);
 if(!checkAuth(req,env))return json({error:'unauthorized'},401,{'WWW-Authenticate':'Bearer'});
 if(req.method!=='POST')return json({error:'method_not_allowed'},405,{'Allow':'POST'});
 if(Number(req.headers.get('Content-Length')||0)>65536)return json({error:'request_too_large'},413);
 let data;try{data=await req.json()}catch{return rpcError(null,-32700,'Invalid JSON')};
 const {id,method,params}=data||{};
 if(method==='notifications/initialized')return new Response(null,{status:202});
 if(method==='initialize')return rpc(id,{protocolVersion:PROTOCOL,capabilities:{tools:{}},serverInfo:{name:'adnc-youtube',version:'0.3.0'}});
 if(method==='ping')return rpc(id,{});
 if(method==='tools/list')return rpc(id,{tools:defs});
 if(method==='tools/call'){
  try{const args=params?.arguments||{};let v;if(params?.name==='upload_private_from_drive')v=await uploadPrivate(args,env);else if(params?.name==='list_uploaded_videos')v=await listVideos(args,env);else if(params?.name==='check_connection')v=await checkConnection(env);else return rpc(id,bad('Unknown tool'));
   return rpc(id,ok(v));}catch(e){return rpc(id,bad(e.message))}
 }
 return rpcError(id??null,-32601,'Method not found');
 }};

/* OAuth Web bootstrap: separate setup secret; no changes to existing /mcp or /health. */
/**
 * AD&C Google OAuth web bootstrap for a Cloudflare Worker (v0.1).
 * Append to the existing single-file Worker and call handleGoogleBrowserOAuth(req,env)
 * before /mcp routing.  No Google credential or token is ever logged.
 *
 * Configuration: GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / AUTH_SETUP_KEY as
 * Cloudflare secrets; AUTH_REDIRECT_URI as a plain Worker variable; UPLOADS_KV
 * and EXPECTED_CHANNEL_ID are retained from the existing deployment.
 */
const ADNC_AUTH_SCOPE = [
  'https://www.googleapis.com/auth/youtube.force-ssl',
  'https://www.googleapis.com/auth/drive.readonly',
].join(' ');
const ADNC_AUTH_HEADER = Object.freeze({
  'Cache-Control': 'no-store, max-age=0',
  'Pragma': 'no-cache',
  'Referrer-Policy': 'no-referrer',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
});
const enc = new TextEncoder();
function oauthB64(bytes) { return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, ''); }
function oauthRandom(n=24) { return oauthB64(crypto.getRandomValues(new Uint8Array(n))); }
function oauthHtmlEscape(x) { return String(x).replace(/[&<>"']/g, v => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[v])); }
function oauthPage(body, js='') {
  const nonce = oauthRandom(18);
  const html = `<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AD&C YouTube認証</title><style nonce="${nonce}">body{font:16px system-ui,sans-serif;max-width:42rem;margin:3rem auto;padding:0 1rem;line-height:1.7}input,button{font:inherit;padding:.65rem;max-width:100%;margin:.35rem}input{min-width:19rem}button{cursor:pointer}code{background:#eee;padding:.2rem}</style></head><body>${body}${js?`<script nonce="${nonce}">${js}</script>`:''}</body></html>`;
  return new Response(html,{status:200,headers:{...ADNC_AUTH_HEADER,'Content-Type':'text/html; charset=utf-8','Content-Security-Policy':`default-src 'none'; script-src 'nonce-${nonce}'; style-src 'nonce-${nonce}'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'`}});
}
function oauthErr(message,status=400) { return new Response(message,{status,headers:{...ADNC_AUTH_HEADER,'Content-Type':'text/plain; charset=utf-8'}}); }
function oauthValidConfig(env,url) {
  if(!env.GOOGLE_CLIENT_ID||!env.GOOGLE_CLIENT_SECRET||!env.AUTH_SETUP_KEY||env.AUTH_SETUP_KEY.length<32||!env.EXPECTED_CHANNEL_ID||!env.AUTH_REDIRECT_URI) return false;
  try{const v=new URL(env.AUTH_REDIRECT_URI);return v.protocol==='https:' && v.origin===url.origin && v.pathname==='/auth/callback'&&!v.search&&!v.hash;}catch{return false;}
}
function oauthKeyEquals(a,b){
  if(typeof a!=='string'||typeof b!=='string'||a.length!==b.length)return false;
  let diff=0;for(let i=0;i<a.length;i++)diff|=a.charCodeAt(i)^b.charCodeAt(i);return diff===0;
}
async function oauthSign(input,secret){
  const key=await crypto.subtle.importKey('raw',enc.encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign']);
  return oauthB64(new Uint8Array(await crypto.subtle.sign('HMAC',key,enc.encode(input))));
}
// PKCE S256: derive a per-request verifier from a server-only secret and the nonce.
async function oauthVerifier(nonce,env){return oauthSign('pkce-v1:'+nonce,env.AUTH_SETUP_KEY);}
async function oauthChallenge(verifier){return oauthB64(new Uint8Array(await crypto.subtle.digest('SHA-256',enc.encode(verifier))));}
async function handleGoogleBrowserOAuth(req,env){
  const url = new URL(req.url);
  if(url.pathname!=='/auth/start'&&url.pathname!=='/auth/callback')return null;
  if(!oauthValidConfig(env,url))return oauthErr('OAuth Web設定が未完了です。管理者に連絡してください。',503);
  if(url.pathname==='/auth/start'){
    if(req.method==='GET'){
      return oauthPage('<h1>AD&C YouTube 初回認証</h1><p>既存のDrive動画をYouTubeへ移す試験のため、YouTube操作権限とGoogle Driveの読み取り権限を求めます。アップロード先は認証後にチャンネルIDで検証します。</p><p><strong>Cloudflare Secretに登録したAUTH_SETUP_KEYをここに入力してください。チャットには送らないでください。</strong></p><p><input type="password" id="key" autocomplete="off" aria-label="接続キー"><button id="start">Googleで認証する</button></p><p id="state"></p>',
`document.getElementById('start').addEventListener('click',async()=>{const key=document.getElementById('key').value;const st=document.getElementById('state');st.textContent='認証ページを準備しています…';try{const r=await fetch('/auth/start',{method:'POST',headers:{Authorization:'Bearer '+key}});if(!r.ok)throw Error('設定キーを確認してください（HTTP '+r.status+'）');const data=await r.json();document.getElementById('key').value='';location.assign(data.authorization_url);}catch(e){st.textContent=e.message;}});`);
    }
    if(req.method!=='POST')return oauthErr('Method not allowed',405);
    const header=req.headers.get('Authorization')||'';
    const key=header.startsWith('Bearer ')?header.slice(7):'';
    if(!oauthKeyEquals(key,env.AUTH_SETUP_KEY))return oauthErr('Unauthorized',401);
    const cookie=oauthRandom();const ts=Math.floor(Date.now()/1000);const pre=ts+'.'+cookie;
    const state=pre+'.'+await oauthSign(pre,env.GOOGLE_CLIENT_SECRET);
    const auth=new URL('https://accounts.google.com/o/oauth2/v2/auth');
    auth.searchParams.set('client_id',env.GOOGLE_CLIENT_ID);
    auth.searchParams.set('redirect_uri',env.AUTH_REDIRECT_URI);
    auth.searchParams.set('response_type','code');
    auth.searchParams.set('scope',ADNC_AUTH_SCOPE);
    auth.searchParams.set('access_type','offline');
    auth.searchParams.set('prompt','consent');
    auth.searchParams.set('state',state);
    auth.searchParams.set('code_challenge_method','S256');
    auth.searchParams.set('code_challenge',await oauthChallenge(await oauthVerifier(cookie,env)));
    return new Response(JSON.stringify({authorization_url:auth.toString()}),{headers:{...ADNC_AUTH_HEADER,'Content-Type':'application/json','Set-Cookie':`adnc_oauth_nonce=${cookie}; Max-Age=600; Path=/auth/callback; HttpOnly; Secure; SameSite=Lax`}});
  }
  if(req.method!=='GET')return oauthErr('Method not allowed',405);
  const state=url.searchParams.get('state')||'';
  const rawCookie=(req.headers.get('Cookie')||'').split(';').map(s=>s.trim()).find(s=>s.startsWith('adnc_oauth_nonce='));
  const nonce=rawCookie?.slice('adnc_oauth_nonce='.length)||'';
  const [tsStr,nonceState,sig,...extra]=state.split('.');
  const ts=Number(tsStr),now=Math.floor(Date.now()/1000);
  if(extra.length||!nonce||!nonceState||!oauthKeyEquals(nonce,nonceState)||!Number.isSafeInteger(ts)||now-ts<0||now-ts>600||!sig)return oauthErr('OAuth state/cookie mismatch or expired. Start again.',400);
  const expect=await oauthSign(tsStr+'.'+nonceState,env.GOOGLE_CLIENT_SECRET);
  if(!oauthKeyEquals(expect,sig))return oauthErr('OAuth state invalid.',400);
  if(url.searchParams.has('error'))return oauthErr('Googleの同意が完了しませんでした。もう一度開始してください。',400);
  const code=url.searchParams.get('code');if(!code||code.length>4096)return oauthErr('OAuth code missing.',400);
  const verifier=await oauthVerifier(nonceState,env);
  const res=await fetch('https://oauth2.googleapis.com/token',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({code,client_id:env.GOOGLE_CLIENT_ID,client_secret:env.GOOGLE_CLIENT_SECRET,redirect_uri:env.AUTH_REDIRECT_URI,grant_type:'authorization_code',code_verifier:verifier})});
  if(!res.ok)return oauthErr('Googleで認証コードを交換できませんでした（HTTP '+res.status+'）。',502);
  const result=await res.json();
  if(!result.access_token||!result.refresh_token)return oauthErr('Googleの更新トークンを取得できません。再度同意を確認してください。',502);
  const got=new Set(String(result.scope||'').split(/\s+/));
  if(!ADNC_AUTH_SCOPE.split(' ').every(s=>got.has(s)))return oauthErr('必要なYouTube/Drive権限がすべて承認されていません。',403);
  const ch=await fetch('https://www.googleapis.com/youtube/v3/channels?mine=true&part=id,snippet',{headers:{Authorization:'Bearer '+result.access_token}});
  if(!ch.ok)return oauthErr('YouTubeチャンネル取得に失敗しました（HTTP '+ch.status+'）。',502);
  const channel=await ch.json();const actual=channel.items?.[0];
  if(!actual?.id||actual.id!==env.EXPECTED_CHANNEL_ID)return oauthErr('投稿先チャンネルが一致しません。別のチャンネルへの登録を防止しました。',403);
  const tokenJs=JSON.stringify(result.refresh_token).replace(/</g,'\\u003c');
  const channelTitle=oauthHtmlEscape(actual.snippet?.title||'');
  // Token appears only in the owner's browser response, not in URL, logs, KV, chat, or source control.
  return oauthPage(`<h1>Google認証成功</h1><p>確認した投稿先：<strong>${channelTitle}</strong> / <code>${oauthHtmlEscape(actual.id)}</code></p><p><strong>このブラウザのタブを他人と共有しないでください。スクリーンショットをチャットへ送らないでください。</strong></p><p><button id="copyToken">更新トークンをコピー（1回限り）</button></p><p>Cloudflare Worker <code>adnc-youtube-private</code> の Settings → Variables and secrets で、<strong>Secret: GOOGLE_REFRESH_TOKEN</strong> に貼り付けて保存してください。ここに取得したトークンは表示しません。保存後はこのタブを閉じてください。</p><p id="copyState"></p>`,
`history.replaceState(null,'','/auth/callback');let refreshToken=${tokenJs};document.getElementById('copyToken').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(refreshToken);document.getElementById('copyState').textContent='コピーしました。CloudflareのSecret入力欄へ貼ってください。';}catch(e){document.getElementById('copyState').textContent='コピーできません。Chromeのクリップボード権限をご確認ください。';}});`);
}
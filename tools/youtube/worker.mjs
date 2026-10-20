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
async function listVideos(args,env){const tok=await token(env);const ch=await google(`${BASE}/youtube/v3/channels?mine=true&part=snippet,contentDetails`,tok);const item=ch.items?.[0];
 if(!item?.id)throw Error('YouTube channel not found');const pl=item.contentDetails?.relatedPlaylists?.uploads;if(!pl)throw Error('uploads playlist not found');
 const limit=Math.min(50,Math.max(1,Number(args?.limit||20)));const response=await google(`${BASE}/youtube/v3/playlistItems?part=contentDetails&maxResults=${limit}&playlistId=${esc(pl)}`,tok);
 const ids=(response.items||[]).map(x=>x.contentDetails?.videoId).filter(Boolean);if(!ids.length)return {channel:item.snippet?.title||'',channel_id:item.id,videos:[]};
 const videos=await google(`${BASE}/youtube/v3/videos?part=snippet,status&id=${esc(ids.join(','))}`,tok);
 return {channel:item.snippet?.title||'',channel_id:item.id,manage_url:env.MANAGEMENT_URL?.startsWith('https://')?env.MANAGEMENT_URL:null,videos:(videos.items||[]).map(x=>({id:x.id,title:x.snippet?.title,privacy_status:x.status?.privacyStatus,upload_status:x.status?.uploadStatus,url:`https://www.youtube.com/watch?v=${x.id}`})),has_more:Boolean(response.nextPageToken)};
}
const defs=[{name:'upload_private_from_drive',title:'Drive動画をYouTubeへ非公開登録',description:'Upload an existing Google Drive video to the authorized YouTube channel. ALWAYS private; never unlisted/public. Requires explicit user instruction. request_key is stable across retried chat tool calls.',inputSchema:{type:'object',additionalProperties:false,required:['drive_file_id','title','made_for_kids','request_key'],properties:{drive_file_id:{type:'string',description:'Owned Google Drive video file ID (not an arbitrary URL)'},title:{type:'string',maxLength:100},description:{type:'string',maxLength:5000},made_for_kids:{type:'boolean',description:'True only when user says the video is made for kids'},request_key:{type:'string',pattern:'^[a-zA-Z0-9_-]{8,100}$',description:'User-task unique stable idempotency key'}}}},
{name:'list_uploaded_videos',title:'YouTube登録済み動画一覧',description:'List owned channel recent videos, visibility, URL. No visibility changes.',inputSchema:{type:'object',properties:{limit:{type:'integer',minimum:1,maximum:50}},additionalProperties:false}}];
export default {async fetch(req,env){const u=new URL(req.url);
 if(u.pathname==='/health'&&req.method==='GET')return json({name:'ADNC YouTube MCP',version:'0.1.0',status:'unconfigured_or_configured_not_disclosed'});
 if(u.pathname!=='/mcp')return json({error:'not_found'},404);
 if(!checkAuth(req,env))return json({error:'unauthorized'},401,{'WWW-Authenticate':'Bearer'});
 if(req.method!=='POST')return json({error:'method_not_allowed'},405,{'Allow':'POST'});
 if(Number(req.headers.get('Content-Length')||0)>65536)return json({error:'request_too_large'},413);
 let data;try{data=await req.json()}catch{return rpcError(null,-32700,'Invalid JSON')};
 const {id,method,params}=data||{};
 if(method==='notifications/initialized')return new Response(null,{status:202});
 if(method==='initialize')return rpc(id,{protocolVersion:PROTOCOL,capabilities:{tools:{}},serverInfo:{name:'adnc-youtube',version:'0.1.0'}});
 if(method==='ping')return rpc(id,{});
 if(method==='tools/list')return rpc(id,{tools:defs});
 if(method==='tools/call'){
  try{const args=params?.arguments||{};let v;if(params?.name==='upload_private_from_drive')v=await uploadPrivate(args,env);else if(params?.name==='list_uploaded_videos')v=await listVideos(args,env);else return rpc(id,bad('Unknown tool'));
   return rpc(id,ok(v));}catch(e){return rpc(id,bad(e.message))}
 }
 return rpcError(id??null,-32601,'Method not found');
 }};

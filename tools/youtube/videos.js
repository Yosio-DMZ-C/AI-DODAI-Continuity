(()=>{'use strict';
const $=id=>document.getElementById(id);
const OAUTH_SCOPE='https://www.googleapis.com/auth/youtube.force-ssl';
const API='https://www.googleapis.com/youtube/v3';
const STORAGE='adnc-youtube-web-client-id-v02';
let token='',tokenClient=null,channel=null,uploadsPlaylist='',nextPage='',listed=[],busy=false,authExpiry=0;
function status(message,error=false){$('authState').textContent=message;$('authState').className='token-state '+(error?'error':'');}
function result(message,error=false){$('uploadState').textContent=message;$('uploadState').className='small '+(error?'error':'');}
function escapeHTML(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function showToast(s){const e=$('toast');e.textContent=s;e.className='hint';setTimeout(()=>e.className='sr',2200);}
function checkedAuth(){if(!token||!channel||Date.now()>=authExpiry){if(token&&Date.now()>=authExpiry)status('認証の有効期限が切れました。再認証してください。',true);throw Error('Googleへの認証またはチャンネル確認が必要です。');}}
function setButtons(){const ok=!!token&&!!channel&&Date.now()<authExpiry;$('upload').disabled=busy||!ok;$('reload').disabled=busy||!ok;$('exportLog').disabled=listed.length===0;$('connect').disabled=busy;$('disconnect').disabled=!token||busy;$('more').disabled=busy;}
async function api(path,opts={}){checkedAuth();const url=path.startsWith('https://')?path:API+path;
 const resp=await fetch(url,{...opts,headers:{Authorization:'Bearer '+token,...(opts.headers||{})}});
 let obj;try{obj=await resp.json()}catch{obj={}};
 if(!resp.ok){let msg=obj?.error?.message||resp.statusText||'APIエラー';if(resp.status===401){token='';channel=null;setButtons();status('認証期限切れ。再認証してください。',true)}throw Error('HTTP '+resp.status+': '+msg)}return obj;}
async function loadChannel(){if(!token)throw Error('未認証');channel={}; // provisional; required for checkedAuth
 const data=await api('/channels?part=snippet,contentDetails&mine=true');const item=data.items?.[0];
 if(!item?.id||!item?.contentDetails?.relatedPlaylists?.uploads){channel=null;throw Error('認証されたYouTubeチャンネルが見つかりません。YouTube側でチャンネルを選んで再認証してください。')}
 channel={id:item.id,title:item.snippet?.title||'(名称不明)'};uploadsPlaylist=item.contentDetails.relatedPlaylists.uploads;
 $('channelName').textContent=channel.title;$('channelId').textContent=channel.id;$('channelBox').classList.remove('hidden');
 status('接続済み：'+channel.title+'（IDを確認してください）');setButtons();await loadVideos(false);
}
function connect(){const clientId=$('clientId').value.trim();if(!/^\d+-[\w-]+\.apps\.googleusercontent\.com$/.test(clientId)){status('Google OAuth WebクライアントIDの形式を確認してください。',true);return;}
 if(!window.google?.accounts?.oauth2){status('Google Identity Servicesを読み込めません。HTTPSとネット接続を確認してください。',true);return;}
 tokenClient=google.accounts.oauth2.initTokenClient({client_id:clientId,scope:OAUTH_SCOPE,callback:async response=>{
 if(!response?.access_token){status('認証できませんでした：'+(response?.error||'不明'),true);return;}
 token=response.access_token;authExpiry=Date.now()+(Math.max(60,Number(response.expires_in||3600))-45)*1000;
 status('チャンネルを確認しています…');try{await loadChannel()}catch(e){channel=null;status(e.message,true);setButtons();}
 },error_callback:e=>status('認証画面の表示に失敗しました：'+(e.type||'error'),true)});
 status('Googleで認証してください…');tokenClient.requestAccessToken({prompt:'consent'});
}
function disconnect(){if(token&&window.google?.accounts?.oauth2)google.accounts.oauth2.revoke(token,()=>{});token='';channel=null;uploadsPlaylist='';nextPage='';listed=[];$('channelBox').classList.add('hidden');$('videoList').innerHTML='<p class="small">未接続</p>';$('more').classList.add('hidden');status('接続解除しました');setButtons();}
async function loadVideos(append){checkedAuth();const params=new URLSearchParams({part:'contentDetails',playlistId:uploadsPlaylist,maxResults:'50'});if(append&&nextPage)params.set('pageToken',nextPage);
 if(!append){listed=[];nextPage='';$('videoList').innerHTML='<p class="small">YouTubeから取得しています…</p>'}
 const pl=await api('/playlistItems?'+params);nextPage=pl.nextPageToken||'';const ids=(pl.items||[]).map(x=>x.contentDetails?.videoId).filter(Boolean);
 if(ids.length){const vr=await api('/videos?'+new URLSearchParams({part:'snippet,status',id:ids.join(',')}));const m=new Map((vr.items||[]).map(x=>[x.id,x]));for(const id of ids){const item=m.get(id);if(item&&!listed.some(y=>y.id===id))listed.push(item)}}
 renderVideos();$('more').classList.toggle('hidden',!nextPage);setButtons();}
function privacyLabel(v){return ({private:'非公開',unlisted:'限定公開',public:'公開'})[v]||'不明';}
function renderVideos(){const el=$('videoList');el.replaceChildren();if(!listed.length){el.innerHTML='<p class="small">表示可能な動画がありません。</p>';return}
 for(const video of listed){const row=document.createElement('div');row.className='rowtable';
 const lhs=document.createElement('div');lhs.style.flex='1 1 240px';
 const title=document.createElement('div');title.className='name';title.textContent=video.snippet?.title||'(名称不明)';lhs.appendChild(title);
 const date=document.createElement('p');date.className='small compact';date.textContent=(video.snippet?.publishedAt||'').slice(0,10)+' / '+(video.status?.uploadStatus||'処理状況不明');lhs.appendChild(date);
 const link=document.createElement('a');link.className='url';link.target='_blank';link.rel='noopener';link.href='https://www.youtube.com/watch?v='+encodeURIComponent(video.id);link.textContent=link.href;lhs.appendChild(link);row.appendChild(lhs);
 const actions=document.createElement('div');actions.className='videoactions';
 const badge=document.createElement('span');badge.className='tag';badge.textContent=privacyLabel(video.status?.privacyStatus);actions.appendChild(badge);
 const copy=document.createElement('button');copy.className='smallbtn';copy.textContent='URLコピー';copy.addEventListener('click',()=>copyText(link.href));actions.appendChild(copy);
 const picker=document.createElement('select');picker.setAttribute('aria-label','公開範囲 '+(video.snippet?.title||''));
 [['private','非公開'],['unlisted','限定公開'],['public','公開']].forEach(([v,label])=>{const o=document.createElement('option');o.value=v;o.textContent=label;picker.appendChild(o)});picker.value=video.status?.privacyStatus||'private';actions.appendChild(picker);
 const update=document.createElement('button');update.className='primary smallbtn';update.textContent='変更を保存';update.disabled=true;
 picker.addEventListener('change',()=>{update.disabled=picker.value===video.status?.privacyStatus||busy});
 update.addEventListener('click',async()=>{try{await updatePrivacy(video,picker.value);picker.value=video.status?.privacyStatus||'private';update.disabled=true}catch(e){alert('更新に失敗しました：'+e.message);picker.value=video.status?.privacyStatus||'private';update.disabled=true}});
 actions.appendChild(update);row.appendChild(actions);el.appendChild(row);
 }
}
async function updatePrivacy(video,to){checkedAuth();const current=video.status?.privacyStatus;if(!['private','unlisted','public'].includes(to))throw Error('公開範囲が不正です。');if(current===to)return;
 if(video.status?.publishAt)throw Error('公開予約が設定されています。YouTube Studioで変更してください。');
 const msg=privacyLabel(current)+' → '+privacyLabel(to)+' に変更します。'+(to!=='private'?'\nURLを知る第三者または一般視聴者が再生できる状態になります。':'')+'\n続行しますか？';
 if(!confirm(msg))return;
 // videos.update(part=status) may reset omitted writable properties: preserve every writable status field.
 const s=video.status||{};const next={privacyStatus:to};
 for(const k of ['embeddable','license','publicStatsViewable','selfDeclaredMadeForKids','containsSyntheticMedia'])if(s[k]!==undefined&&s[k]!==null)next[k]=s[k];
 busy=true;setButtons();try{const ret=await api('/videos?part=status',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:video.id,status:next})});
 if(ret?.status?.privacyStatus!==to)throw Error('更新応答が要求値と一致しません。');
 const verify=await api('/videos?'+new URLSearchParams({part:'snippet,status',id:video.id}));const got=verify.items?.[0];
 if(got?.status?.privacyStatus!==to)throw Error('再取得しても公開範囲が一致しません。YouTube Studioで確認してください。');
 Object.assign(video,got);showToast('公開範囲を更新しました');renderVideos();
 }finally{busy=false;setButtons();}
}
function copyText(s){if(navigator.clipboard&&window.isSecureContext)navigator.clipboard.writeText(s).then(()=>showToast('コピーしました')).catch(()=>prompt('コピーしてください',s));else prompt('コピーしてください',s);}
function xhrUpload(url,file){return new Promise((resolve,reject)=>{const xhr=new XMLHttpRequest();xhr.open('PUT',url,true);xhr.setRequestHeader('Authorization','Bearer '+token);xhr.setRequestHeader('Content-Type',file.type||'application/octet-stream');
 xhr.upload.onprogress=e=>{if(e.lengthComputable){const p=Math.floor((e.loaded/e.total)*100);$('uploadProgress').value=p;result('アップロード中：'+p+'%')}};
 xhr.onload=()=>{let obj;try{obj=JSON.parse(xhr.responseText||'{}')}catch{obj={}};if(xhr.status>=200&&xhr.status<300)resolve(obj);else reject(Error('アップロードHTTP '+xhr.status+': '+(obj?.error?.message||xhr.responseText.slice(0,200))))};xhr.onerror=()=>reject(Error('通信エラー。処理中だった可能性があるため一覧を確認してから再試行してください。'));xhr.onabort=()=>reject(Error('アップロードが中断されました。'));xhr.send(file)})}
async function upload(){try{checkedAuth();if(busy)return;const file=$('file').files?.[0];const title=$('title').value.trim();const description=$('description').value;const audience=$('audience').value;
 if(!file||!file.size)throw Error('動画ファイルを選択してください。');if(!title||title.length>100)throw Error('タイトルを1〜100文字で入力してください。');if(description.length>5000)throw Error('概要欄が長すぎます。');if(!['true','false'].includes(audience))throw Error('子ども向けかどうかを選択してください。');
 if(!confirm('接続先：'+channel.title+'\nファイル：'+file.name+'\n非公開でアップロードします。よろしいですか？'))return;
 busy=true;setButtons();$('uploadProgress').value=0;result('非公開のアップロードセッションを作成中…');
 const url='https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status';
 const meta={snippet:{title,description,categoryId:'28'},status:{privacyStatus:'private',selfDeclaredMadeForKids:audience==='true'}};
 const init=await fetch(url,{method:'POST',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json; charset=UTF-8','X-Upload-Content-Length':String(file.size),'X-Upload-Content-Type':file.type||'video/mp4'},body:JSON.stringify(meta)});
 if(!init.ok){let e={};try{e=await init.json()}catch{}throw Error('アップロード開始に失敗：HTTP '+init.status+' '+(e?.error?.message||''))}
 const location=init.headers.get('Location');if(!location)throw Error('Googleがアップロード先(Locationヘッダ)をブラウザに公開しませんでした。YouTube Studioでアップロードしてください。');
 const lu=new URL(location);if(lu.protocol!=='https:'||!['www.googleapis.com','youtube.googleapis.com'].includes(lu.hostname)||!lu.pathname.startsWith('/upload/youtube/'))throw Error('Googleのアップロード先URLが想定外のため中止しました。');
 const uploaded=await xhrUpload(location,file);if(!uploaded.id)throw Error('動画IDが返りませんでした。一覧で重複登録されていないか確認してください。');
 const check=await api('/videos?'+new URLSearchParams({part:'status',id:uploaded.id}));
 if(check.items?.[0]?.status?.privacyStatus!=='private')throw Error('アップロード応答後の公開範囲を非公開と確認できません。Studioで確認してください。');
 const link='https://www.youtube.com/watch?v='+encodeURIComponent(uploaded.id);$('uploadLink').classList.remove('hidden');$('uploadLink').replaceChildren();const a=document.createElement('a');a.href=link;a.target='_blank';a.rel='noopener';a.textContent=link;$('uploadLink').append('非公開動画：',a);
 result('アップロード成功：非公開を再取得して確認しました。この画面から更新してください（下の動画一覧）。');await loadVideos(false);
 }catch(e){result(e.message,true)}finally{busy=false;setButtons()}}
function exportCsv(){const lines=[['id','title','privacy','youtube_url','upload_status'],...listed.map(v=>[v.id,v.snippet?.title||'',v.status?.privacyStatus||'', 'https://www.youtube.com/watch?v='+v.id,v.status?.uploadStatus||''])];
 const csv='\ufeff'+lines.map(l=>l.map(x=>'"'+String(x).replace(/"/g,'""')+'"').join(',')).join('\r\n');
 const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='ADNC_YouTube_Videos_'+new Date().toISOString().slice(0,10)+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function handoff(){const lines=['AD&C YouTube動画管理の結果','チャンネル: '+(channel?.title||'未確認'),'チャンネルID: '+(channel?.id||'未確認'),'一覧取得: '+listed.length+'件','動画（最初の50件まで）:'];listed.forEach(v=>lines.push('- '+(v.snippet?.title||'')+' | '+(v.status?.privacyStatus||'unknown')+' | https://www.youtube.com/watch?v='+v.id));lines.push('※動画のアップロード成功はYouTube APIの非公開再取得結果で判断する。');copyText(lines.join('\n'))}
try{$('clientId').value=localStorage.getItem(STORAGE)||''}catch{}
$('saveClient').addEventListener('click',()=>{try{localStorage.setItem(STORAGE,$('clientId').value.trim());showToast('OAuthクライアントIDを保存しました')}catch{status('保存できませんでした。',true)}});
$('connect').addEventListener('click',connect);$('disconnect').addEventListener('click',disconnect);$('upload').addEventListener('click',upload);$('reload').addEventListener('click',async()=>{try{await loadVideos(false)}catch(e){status(e.message,true)}});$('more').addEventListener('click',async()=>{if(nextPage)try{await loadVideos(true)}catch(e){status(e.message,true)}});
$('exportLog').addEventListener('click',exportCsv);$('copyHandoff').addEventListener('click',handoff);
$('resetForm').addEventListener('click',()=>{if(!confirm('ファイル・タイトル・説明文・子ども向け設定を消しますか？'))return;for(const id of ['file','title','description','audience'])$(id).value='';$('uploadLink').classList.add('hidden');$('uploadProgress').value=0;result('未実行')});setButtons();
})();

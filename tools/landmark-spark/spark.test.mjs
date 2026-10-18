import test from 'node:test';
import assert from 'node:assert/strict';
import { createState, recordUserTurn, reviewProbe, setEnabled, parseDraftMarkdown } from './spark.mjs';

const deck = Array.from({ length: 8 }, (_, i) => ({
  id: `KG-0${1 + Math.floor(i / 2)}-0${1 + i % 2}`, domain: `0${1 + Math.floor(i / 2)}`,
  aphorism: `発想例${i+1}`, primary_title: `研究${i+1}`, caution: '適用条件を確認',
  rationale: `研究との接続候補${i+1}`, review_status: 'draft'
}));
const evt = (i, conversation_id='c1', overrides={}) => ({
  message_id: `msg-${i}`, conversation_id, context:{ mode:'deep', risk:'low', ...overrides }
});
function run(n=20, overrides={}, initial=null) {
  let state = initial || createState('c1'); let out;
  for (let i=1;i<=n;i++) {out=recordUserTurn(state,evt(i,'c1',overrides),deck);state=out.state;}
  return out;
}

test('1-19 silent, 20th offers 3 diverse internal candidates', () => {
  let state=createState('c1');
  for(let i=1;i<20;i++){let r=recordUserTurn(state,evt(i),deck);assert.equal(r.status,'NOT_DUE');assert.equal(r.probe,null);state=r.state;}
  const r=recordUserTurn(state,evt(20),deck);
  assert.equal(r.status,'PROBE_INTERNAL');assert.equal(r.probe.cards.length,3);
  assert.equal(new Set(r.probe.cards.map(x=>x.id)).size,3);
  assert.equal(new Set(r.probe.cards.map(x=>x.domain)).size,3);
});
test('20th duplicate message does not count or redraw', () => {
  const r=run(); const d=recordUserTurn(r.state,evt(20),deck);
  assert.equal(d.status,'DUPLICATE');assert.equal(d.state.human_turn_count,20);
  assert.deepEqual(d.probe,null);assert.deepEqual(d.state.pending,r.state.pending);
});
test('20th simple question skipped; 40th available once', () => {
  let state=createState('c1');for(let i=1;i<=40;i++){
    const mode=i===20?'simple':'deep';const r=recordUserTurn(state,evt(i,'c1',{mode}),deck);
    if(i===20) assert.equal(r.status,'SKIP_CONTEXT');
    if(i===40)assert.equal(r.status,'PROBE_INTERNAL');
    if(i%20!==0)assert.equal(r.status,'NOT_DUE');
    state=r.state;
  }assert.equal(state.human_turn_count,40);
});
test('sensitive context cannot select card', () => {
  const r=run(20,{risk:'high'});assert.equal(r.status,'SKIP_CONTEXT');
});
test('deck with <3 items is silent',()=>{
  let s=createState('c1');for(let i=1;i<=20;i++){
    const r=recordUserTurn(s,evt(i),deck.slice(0,2));s=r.state;
    if(i===20)assert.equal(r.status,'SKIP_DECK');
  }
});
test('review fails closed and consumes probe',()=>{
  const r=run();const p=r.probe;
  const fail=reviewProbe(r.state,{probe_id:p.probe_id,selected_id:p.cards[0].id,
    original_task_completed:true,relevant:true,novel:false,supported_as_analogy:true,safe:true,non_intrusive:true});
  assert.equal(fail.status,'SILENT');assert.equal(fail.user_text,null);
  assert.equal(reviewProbe(fail.state,{}).status,'NO_PENDING');
});
test('only a chosen eligible card is shown; never quotes a famous person',()=>{
  const r=run();const p=r.probe;
  const yes=reviewProbe(r.state,{probe_id:p.probe_id,selected_id:p.cards[1].id,
    original_task_completed:true,relevant:true,novel:true,supported_as_analogy:true,safe:true,non_intrusive:true});
  assert.equal(yes.status,'OPTIONAL_INSPIRATION');
  assert.match(yes.user_text,/別の見方として/);
  assert.match(yes.user_text,/ただし/);
  assert.equal(yes.user_text.includes(p.cards[1].aphorism),true);
  assert.equal(reviewProbe(yes.state,{probe_id:p.probe_id}).status,'NO_PENDING');
});
test('stale probe cannot leak after next human message',()=>{
  let r=run(); r=recordUserTurn(r.state,evt(21),deck);
  assert.equal(r.state.pending,null);
  assert.equal(reviewProbe(r.state,{probe_id:'x'}).status,'NO_PENDING');
});
test('opt-out cannot produce a probe and opt-in is reversible',()=>{
  let s=setEnabled(createState('c1'),false);
  for(let i=1;i<=40;i++){let r=recordUserTurn(s,evt(i),deck);assert.equal(r.status,'DISABLED');s=r.state;}
  assert.equal(s.human_turn_count,0);
  s=setEnabled(s,true);
  assert.equal(recordUserTurn(s,evt(41),deck).status,'NOT_DUE');
});
test('conversation ID separation fail closed',()=>{
  assert.throws(()=>recordUserTurn(createState('other'),evt(1),deck),/wrong conversation/);
});
test('Markdown 220-input adapter validates primary and secondary references',()=>{
  const research='| LM-01-01 | 自然選択 | あらゆるもの |\n| LM-02-01 | 学び | 条件 |\n| LM-03-01 | 制御 | 条件 |\n';
  const sayings='|KG-01-01|考え方A|LM-01-01 自然選択|LM-02-01 学び|理由A|注意A|\n'
    +'|KG-02-01|考え方B|LM-02-01 学び|LM-03-01 制御|理由B|注意B|\n'
    +'|KG-03-01|考え方C|LM-03-01 制御|LM-01-01 自然選択|理由C|注意C|\n';
  const arr=parseDraftMarkdown(research,sayings);assert.equal(arr.length,3);
  assert.equal(arr[0].review_status,'draft');
  assert.throws(()=>parseDraftMarkdown(research,sayings.replace('LM-01-01 自然選択','LM-01-01 誤表記')),/research title mismatch/);
});
test('deterministic draw for same turn and deck, after independent reset',()=>{
  const a=run(), b=run();assert.deepEqual(a.probe,b.probe);
});
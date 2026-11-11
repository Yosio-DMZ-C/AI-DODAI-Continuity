/**
 * AD&C landmark spark - opt-in, low-frequency experiment (Node.js 18+).
 * Pure decisions first, opt-in CLI below. No API calls, no timers, no chat hooks.
 * Candidate content remains untrusted Draft material until an independent review.
 */
import { createHash } from 'node:crypto';
import { readFile, writeFile, rename, mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export const DEFAULT_INTERVAL = 20;
const MODES = new Set(['deep', 'stuck', 'iterative']);
const MAX_IDS = 500;
const STATE_VERSION = 1;

function hashInt(s) {
  return Number.parseInt(createHash('sha256').update(s).digest('hex').slice(0, 12), 16);
}
function requireText(s, name) {
  if (typeof s !== 'string' || !s.trim()) throw new Error(name + ' must be nonempty text');
  return s.trim();
}
export function createState(conversationId, { interval = DEFAULT_INTERVAL } = {}) {
  requireText(conversationId, 'conversation_id');
  if (!Number.isSafeInteger(interval) || interval < 1) throw new Error('invalid interval');
  return { version: STATE_VERSION, conversation_id: conversationId, interval,
    enabled: true, human_turn_count: 0, seen_message_ids: [], pending: null };
}
function validateState(state, conversationId) {
  if (!state || state.version !== STATE_VERSION || state.conversation_id !== conversationId ||
      !Number.isSafeInteger(state.human_turn_count) || state.human_turn_count < 0 ||
      !Number.isSafeInteger(state.interval) || state.interval < 1 ||
      !Array.isArray(state.seen_message_ids)) throw new Error('state invalid or wrong conversation');
}

/** Strictly parse research & aphorism tables, with content treated as DATA. */
export function parseDraftMarkdown(researchMarkdown, aphorismMarkdown) {
  const research = new Map();
  for (const line of researchMarkdown.split(/\r?\n/)) {
    const m = line.match(/^\|\s*(LM-\d\d-\d\d)\s*\|\s*([^|]+?)\s*\|/);
    if (!m) continue;
    if (research.has(m[1])) throw new Error('duplicate research ID: ' + m[1]);
    research.set(m[1], m[2].trim().replace(/^★\s*/, ''));
  }
  const deck = [], seen = new Set();
  for (const line of aphorismMarkdown.split(/\r?\n/)) {
    const c = line.split('|').map(s => s.trim());
    if (c.length < 8 || !/^KG-\d\d-\d\d$/.test(c[1] || '')) continue;
    const [ , id, aphorism, primary, secondary, rationale, caution ] = c;
    if (seen.has(id)) throw new Error('duplicate aphorism ID: ' + id);
    seen.add(id);
    const p = primary.match(/^(LM-\d\d-\d\d)\s+(.+)$/);
    const s = secondary.match(/^(LM-\d\d-\d\d)\s+(.+)$/);
    if (!p || !s || !research.has(p[1]) || !research.has(s[1]))
      throw new Error('unknown research link in ' + id);
    if (research.get(p[1]) !== p[2].trim() || research.get(s[1]) !== s[2].trim())
      throw new Error('research title mismatch in ' + id);
    if (id.slice(3, 5) !== p[1].slice(3, 5)) throw new Error('primary domain mismatch in ' + id);
    deck.push({ id, domain: id.slice(3, 5), aphorism: requireText(aphorism, 'aphorism'),
      primary_id: p[1], primary_title: p[2].trim(), secondary_id: s[1],
      rationale: requireText(rationale, 'rationale'), caution: requireText(caution, 'caution'),
      review_status: 'draft' });
  }
  if (deck.length < 3) throw new Error('at least 3 valid aphorisms required');
  return deck;
}

function validCards(deck) {
  if (!Array.isArray(deck)) throw new Error('deck must be an array');
  const seen = new Set();
  return deck.filter(c => {
    if (!c || typeof c.id !== 'string' || seen.has(c.id)) return false;
    if (typeof c.aphorism !== 'string' || !c.aphorism.trim() || c.aphorism.length > 200) return false;
    if (typeof c.primary_title !== 'string' || !c.primary_title.trim()) return false;
    if (typeof c.caution !== 'string' || !c.caution.trim()) return false;
    seen.add(c.id); return true;
  });
}

function threeChoices(deck, seed) {
  const ranked = deck.map(card => ({ card, order: hashInt(seed + '\0' + card.id) }))
    .sort((a,b) => a.order - b.order || a.card.id.localeCompare(b.card.id));
  // Diversity without additional model calls: prefer distinct domains among three.
  const out = [], domains = new Set();
  for (const x of ranked) { if (!domains.has(x.card.domain) && out.length < 3) { out.push(x.card); domains.add(x.card.domain); } }
  for (const x of ranked) { if (out.length === 3) break; if (!out.some(c => c.id === x.card.id)) out.push(x.card); }
  return out;
}

/** One invocation = ONE human message received in this conversation; cannot count other chats. */
export function recordUserTurn(originalState, event, deck) {
  const conversationId = requireText(event?.conversation_id, 'conversation_id');
  const id = requireText(event?.message_id, 'message_id');
  const state = originalState ? structuredClone(originalState) : createState(conversationId);
  validateState(state, conversationId);
  if (state.seen_message_ids.includes(id)) return { state, status: 'DUPLICATE', probe: null };
  state.seen_message_ids.push(id);
  state.seen_message_ids = state.seen_message_ids.slice(-MAX_IDS);
  state.pending = null; // Never reveal stale inspiration after the next human turn.
  if (!state.enabled) return { state, status: 'DISABLED', probe: null };
  state.human_turn_count++;
  if (state.human_turn_count % state.interval !== 0)
    return { state, status: 'NOT_DUE', probe: null };
  const ctx = event.context || {};
  // Count trigger is cheap and mechanical. Expensive lookup only after 20 turns.
  if (!MODES.has(ctx.mode) || ctx.risk !== 'low')
    return { state, status: 'SKIP_CONTEXT', probe: null };
  const cards = validCards(deck);
  if (cards.length < 3) return { state, status: 'SKIP_DECK', probe: null };
  const picked = threeChoices(cards, conversationId + '\0' + id + '\0' + state.human_turn_count);
  const probe_id = createHash('sha256').update(conversationId + '\0' + id).digest('hex').slice(0, 20);
  const probe = { probe_id, human_turn_count: state.human_turn_count,
    cards: picked.map(c => ({ id: c.id, domain: c.domain, aphorism: c.aphorism,
      primary_id: c.primary_id, primary_title: c.primary_title,
      rationale: c.rationale, caution: c.caution,
      review_status: c.review_status || 'draft' })) };
  state.pending = probe;
  return { state, status: 'PROBE_INTERNAL', probe };
}

/** AI/human reviewer decides if a card is useful. Every pass flag must be explicit. */
export function reviewProbe(originalState, choice) {
  if (!originalState) throw new Error('state missing');
  const state = structuredClone(originalState);
  const probe = state.pending;
  if (!probe || choice?.probe_id !== probe.probe_id) return { state, status: 'NO_PENDING', user_text: null };
  state.pending = null;
  const card = probe.cards.find(c => c.id === choice.selected_id);
  const checks = ['original_task_completed', 'relevant', 'novel', 'supported_as_analogy', 'safe', 'non_intrusive'];
  if (!card || checks.some(k => choice[k] !== true))
    return { state, status: 'SILENT', user_text: null };
  // Draft aphorisms are shown only as a tentative way to think, never as facts or quotes.
  return { state, status: 'OPTIONAL_INSPIRATION', user_text:
    `別の見方として、「${card.aphorism}」という着想もあります。${card.rationale}。ただし、${card.caution}。` };
}
export function setEnabled(originalState, enabled) {
  if (typeof enabled !== 'boolean') throw new Error('enabled must be boolean');
  const state = structuredClone(originalState);
  validateState(state, state.conversation_id);
  state.enabled = enabled; state.pending = null;
  return state;
}

// Minimal CLI. The host must supply one unique message ID per user turn and persist state.
async function cli() {
  const [, , command, ...arglist] = process.argv;
  const args = {};
  for (let i = 0; i < arglist.length; i += 2) {
    if (!arglist[i]?.startsWith('--') || arglist[i + 1] === undefined) throw new Error('invalid CLI arguments');
    args[arglist[i].slice(2)] = arglist[i + 1];
  }
  const statePath = resolve(requireText(args.state, '--state'));
  let state = null;
  try { state = JSON.parse(await readFile(statePath, 'utf8')); }
  catch (e) { if (e.code !== 'ENOENT') throw e; }
  let result;
  if (command === 'tick') {
    const event = JSON.parse(await readFile(requireText(args.event, '--event'), 'utf8'));
    let deck;
    if (args.research && args.aphorisms) {
      deck = parseDraftMarkdown(await readFile(args.research, 'utf8'), await readFile(args.aphorisms, 'utf8'));
    } else deck = JSON.parse(await readFile(requireText(args.deck, '--deck'), 'utf8'));
    result = recordUserTurn(state, event, deck);
  } else if (command === 'review') {
    const decision = JSON.parse(await readFile(requireText(args.decision, '--decision'), 'utf8'));
    result = reviewProbe(state, decision);
  } else if (command === 'off' || command === 'on') {
    if (!state) throw new Error('first run tick to create conversation state');
    result = { state: setEnabled(state, command === 'on'), status: command.toUpperCase(), user_text: null };
  } else throw new Error('Usage: node spark.mjs tick --state FILE --event FILE --deck FILE | --research FILE --aphorisms FILE; review --state FILE --decision FILE; on/off --state FILE');
  await mkdir(dirname(statePath), { recursive: true });
  const tmp = statePath + '.' + process.pid + '.tmp';
  await writeFile(tmp, JSON.stringify(result.state, null, 2) + '\n', { flag: 'wx', mode: 0o600 });
  await rename(tmp, statePath); // Atomic replacement; caller must serialize concurrent runs.
  const { state: _internalState, ...publicResult } = result;
  process.stdout.write(JSON.stringify(publicResult, null, 2) + '\n');
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href)
  cli().catch(e => { process.stderr.write('ERROR: ' + e.message + '\n'); process.exitCode = 1; });
'use strict';

// Node.js Philosophical Data Combiner Orchestrator
// - Fetches datasets from FastAPI
// - Joins by author (and school_id for schools)
// - Stores master datasets in Redis under specific keys
// - Optional JSON output for debugging

const { createClient } = require('redis');
const fs = require('fs/promises');

// Environment
const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL || 'http://backend:8000';
const FASTAPI_API_KEY = process.env.FASTAPI_API_KEY || '';
const REDIS_URL = process.env.REDIS_URL || 'redis://:ch@ng3m300@redis:6379';
const MASTER_TTL_SECONDS = parseInt(process.env.MASTER_ORCHESTRATOR_TTL || '0', 10) || 0; // 0 = no TTL

// Redis Keys
const REDIS_KEY_ALL = 'master_orchestrator';
const REDIS_KEY_ACTIVE = 'master_orchestrator_active';

// Concurrency
const MAX_CONCURRENCY = parseInt(process.env.ORCHESTRATOR_CONCURRENCY || '6', 10);

const HEADERS = {
  'Content-Type': 'application/json',
  ...(FASTAPI_API_KEY ? { Authorization: `Bearer ${FASTAPI_API_KEY}` } : {}),
};

function buildUrl(path, params = {}) {
  const url = new URL(path, FASTAPI_BASE_URL);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, String(v));
  });
  return url.toString();
}

async function callAPI(path, { method = 'GET', body = undefined, params = undefined } = {}) {
  const url = params ? buildUrl(path, params) : new URL(path, FASTAPI_BASE_URL).toString();
  const opts = { method, headers: HEADERS };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`FastAPI ${method} ${url} -> ${res.status} ${res.statusText} ${text}`);
  }
  return res.json();
}

// Text and hook matching helpers
function escapeRegExp(s) {
  if (typeof s !== 'string') return '';
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function includesWord(val, term) {
  if (!val || !term || typeof val !== 'string') return false;
  const re = new RegExp(`\\b${escapeRegExp(term)}\\b`, 'i');
  return re.test(val);
}

function hookMatchesTerms(hook, terms) {
  if (!hook || !Array.isArray(terms) || terms.length === 0) return false;
  const fields = [hook.topic, hook.content];
  if (Array.isArray(hook.themes)) fields.push(...hook.themes);
  else if (hook.themes) fields.push(hook.themes);
  if (hook.author) fields.push(hook.author);
  if (hook.philosopher) fields.push(hook.philosopher);
  return terms.some((t) => fields.some((f) => {
    const s = String(f || '');
    // Prefer word-boundary, but accept substring to capture variants like 'Kantian', 'Platonic'
    return includesWord(s, t) || s.toLowerCase().includes(String(t).toLowerCase());
  }));
}

function dedupeHooks(hooks) {
  const seen = new Set();
  const out = [];
  for (const h of hooks || []) {
    const key = h?._id || h?.id || `${h?.topic || ''}|${(h?.content || '').slice(0,64)}`;
    if (!seen.has(key)) {
      seen.add(key);
      out.push(h);
    }
  }
  return out;
}

// Flatten possible author-level documents that contain a nested 'discussion_hooks' structure into hook items
function flattenDiscussionHookDocs(input) {
  if (!input) return [];
  // If this is already an array of hook items (with topic/content), return as-is
  if (Array.isArray(input)) {
    if (
      input.length > 0 &&
      input.every((d) => !(d && (Array.isArray(d.discussion_hooks) || (typeof d?.discussion_hooks === 'object' && d.discussion_hooks !== null))))
    ) {
      return input;
    }
    const out = [];
    for (const d of input) {
      const dh = d?.discussion_hooks;
      if (Array.isArray(dh)) out.push(...dh);
      else if (dh && typeof dh === 'object') out.push(...Object.values(dh));
    }
    return out;
  }
  if (typeof input === 'object') {
    const dh = input.discussion_hooks;
    if (Array.isArray(dh)) return dh;
    if (dh && typeof dh === 'object') return Object.values(dh);
  }
  return [];
}

async function fetchPhilosophers(isActiveChat = null) {
  const params = { limit: 1000 };
  if (isActiveChat === 0 || isActiveChat === 1) params.is_active_chat = isActiveChat;
  const resp = await callAPI('/api/v1/philosophers', { params });
  return Array.isArray(resp?.data) ? resp.data : [];
}

async function fetchSchools() {
  const resp = await callAPI('/api/v1/philosophy-schools', { params: { limit: 1000 } });
  const items = Array.isArray(resp?.data) ? resp.data : [];
  const map = new Map();
  for (const s of items) {
    if (s && (s.id !== undefined || s.school_id !== undefined)) {
      const key = s.school_id ?? s.id; // support either field name
      map.set(String(key), s);
    }
  }
  return map;
}

async function fetchBlueprints(author) {
  const params = {};
  if (author) params.author = author;
  const resp = await callAPI('/api/v1/chat/blueprints', { params });
  return Array.isArray(resp?.data) ? resp.data : [];
}

async function fetchConversationLogic(author) {
  const params = {};
  if (author) params.author = author;
  const resp = await callAPI('/api/v1/chat/conversation-logic', { params });
  return Array.isArray(resp?.data) ? resp.data : [];
}

// Additional collections not included in the unified by-author endpoint
async function fetchBibliography(author) {
  if (!author) return [];
  const safe = encodeURIComponent(author);
  const resp = await callAPI(`/api/v1/books/bibliography/by-author/${safe}`);
  // This endpoint returns a single object in data; normalize to array
  const d = resp?.data;
  if (!d) return [];
  return Array.isArray(d) ? d : [d];
}

async function fetchDiscussionHooks(author) {
  // Retrieve hooks relevant to this author using multiple queries (full name + last name),
  // then dedupe and filter by word-boundary matches against relevant fields.
  if (!author) return [];
  const full = String(author).trim();
  const parts = full.split(/\s+/).filter(Boolean);
  const last = parts.length > 1 ? parts[parts.length - 1] : full;
  const terms = Array.from(new Set([full, last]));

  const queries = Array.from(new Set([full, last]));
  const results = [];
  for (const q of queries) {
    try {
      const resp = await callAPI('/api/v1/summaries/discussion-hooks', { params: { topic: q, limit: 1000 } });
      if (Array.isArray(resp?.data)) results.push(...resp.data);
    } catch (_) {
      // ignore and continue
    }
  }
  // Prefer author field match at the document level, if present
  const authorEq = (a, b) => String(a || '').toLowerCase() === String(b || '').toLowerCase();
  let docsByAuthor = results.filter((d) => authorEq(d?.author, full));
  let flattened = flattenDiscussionHookDocs(docsByAuthor);
  let deduped = dedupeHooks(flattened);
  let filtered = deduped;
  if (filtered.length === 0) {
    // Fallback to global fetch (no topic) but still strictly filter by author terms
    try {
      const respAll = await callAPI('/api/v1/summaries/discussion-hooks', { params: { limit: 1000 } });
      const all = Array.isArray(respAll?.data) ? respAll.data : [];
      docsByAuthor = all.filter((d) => authorEq(d?.author, full));
      flattened = flattenDiscussionHookDocs(docsByAuthor);
      deduped = dedupeHooks(flattened);
      // As a last resort, if still empty, attempt content-based matching on all flattened docs
      if (deduped.length === 0) {
        const anyFlat = flattenDiscussionHookDocs(all);
        filtered = dedupeHooks(anyFlat).filter((h) => hookMatchesTerms(h, terms));
      } else {
        filtered = deduped;
      }
    } catch (_) {
      // keep empty
    }
  }
  return filtered;
}

async function fetchPersonaCores(author) {
  const params = { philosopher: author || undefined, limit: 1000 };
  const resp = await callAPI('/api/v1/chat/persona-cores', { params });
  return Array.isArray(resp?.data) ? resp.data : [];
}

async function fetchModernAdaptations(author) {
  const params = { philosopher: author || undefined, limit: 1000 };
  const resp = await callAPI('/api/v1/chat/modern-adaptations', { params });
  return Array.isArray(resp?.data) ? resp.data : [];
}

async function fetchByAuthor(author) {
  const safe = encodeURIComponent(author);
  const resp = await callAPI(`/api/v1/philosophers/by-author/${safe}`);
  // resp: { success, message, data, total_items }
  return resp?.data || {};
}

function normalizeByAuthorData(data) {
  if (!data || typeof data !== 'object') return {};
  const out = { ...data };
  // normalize top ideas field name to top_10_ideas
  if (!out.top_10_ideas && Array.isArray(out.top_ten_ideas)) {
    out.top_10_ideas = out.top_ten_ideas;
  }
  // ensure arrays exist
  const listFields = [
    'philosophers',
    'aphorisms',
    'book_summary',
    'bibliography',
    'discussion_hook',
    'persona_core',
    'modern_adaptation',
    'top_10_ideas',
    'idea_summary',
    'philosophy_themes',
    'philosopher_summary',
  ];
  // if backend returned a single object (e.g., bibliography), wrap into an array
  for (const f of listFields) {
    if (out[f] && !Array.isArray(out[f])) {
      out[f] = [out[f]];
    }
  }
  for (const f of listFields) {
    if (!Array.isArray(out[f])) out[f] = [];
  }
  return out;
}

function combineOne({ philosopher, byAuthor, school, blueprints, logic, bibliography, discussionHooks, personaCores, modernAdaptations }) {
  const author = philosopher?.author || byAuthor?.author || null;
  const pickHooks = () => {
    const choose = (Array.isArray(byAuthor.discussion_hook) && byAuthor.discussion_hook.length ? byAuthor.discussion_hook : (discussionHooks || []));
    const flat = flattenDiscussionHookDocs(choose);
    return Array.isArray(flat) && flat.length ? flat : (Array.isArray(choose) ? choose : []);
  };
  const combined = {
    author,
    philosopher: philosopher || null,
    school: school || null,
    // collections joined by author
    aphorisms: byAuthor.aphorisms || [],
    book_summary: byAuthor.book_summary || [],
    bibliography: (Array.isArray(byAuthor.bibliography) && byAuthor.bibliography.length ? byAuthor.bibliography : (bibliography || [])),
    discussion_hook: pickHooks(),
    persona_core: (Array.isArray(byAuthor.persona_core) && byAuthor.persona_core.length ? byAuthor.persona_core : (personaCores || [])),
    modern_adaptation: (Array.isArray(byAuthor.modern_adaptation) && byAuthor.modern_adaptation.length ? byAuthor.modern_adaptation : (modernAdaptations || [])),
    top_10_ideas: byAuthor.top_10_ideas || [],
    idea_summary: byAuthor.idea_summary || [],
    philosophy_themes: byAuthor.philosophy_themes || [],
    philosopher_summary: byAuthor.philosopher_summary || [],
    // chat datasets
    chat_blueprints: blueprints || [],
    conversation_logic: logic || [],
    // metadata
    counts: {},
  };
  combined.counts = {
    aphorisms: combined.aphorisms.length,
    book_summary: combined.book_summary.length,
    bibliography: combined.bibliography.length,
    discussion_hook: combined.discussion_hook.length,
    persona_core: combined.persona_core.length,
    modern_adaptation: combined.modern_adaptation.length,
    top_10_ideas: combined.top_10_ideas.length,
    idea_summary: combined.idea_summary.length,
    philosophy_themes: combined.philosophy_themes.length,
    philosopher_summary: combined.philosopher_summary.length,
    chat_blueprints: combined.chat_blueprints.length,
    conversation_logic: combined.conversation_logic.length,
  };
  return combined;
}

async function processWithConcurrency(items, worker, max = MAX_CONCURRENCY) {
  const results = new Array(items.length);
  let index = 0;
  async function runNext() {
    const i = index++;
    if (i >= items.length) return;
    try {
      results[i] = await worker(items[i], i);
    } catch (e) {
      results[i] = { error: String(e?.message || e) };
    }
    return runNext();
  }
  const runners = Array.from({ length: Math.min(max, items.length) }, runNext);
  await Promise.all(runners);
  return results;
}

async function buildDataset(isActiveChatFilter = null) {
  // Fetch base datasets
  const [philosophers, schoolsMap, globalBlueprints] = await Promise.all([
    fetchPhilosophers(isActiveChatFilter),
    fetchSchools(),
    // chat_blueprint is a global dataset (not keyed) applied to each philosopher
    fetchBlueprints(null).catch(() => []),
  ]);

  // Per-author aggregation
  const combined = await processWithConcurrency(
    philosophers,
    async (p) => {
      const author = p?.author;
      if (!author) {
        return combineOne({ philosopher: p, byAuthor: normalizeByAuthorData({}), school: null, blueprints: [], logic: [], bibliography: [], discussionHooks: [], personaCores: [], modernAdaptations: [] });
      }
      const [byAuthorRaw, logic, bibliography, discussionHooks, personaCores, modernAdaptations] = await Promise.all([
        fetchByAuthor(author).catch(() => ({})),
        fetchConversationLogic(author).catch(() => []),
        fetchBibliography(author).catch(() => []),
        fetchDiscussionHooks(author).catch(() => []),
        fetchPersonaCores(author).catch(() => []),
        fetchModernAdaptations(author).catch(() => []),
      ]);
      const byAuthor = normalizeByAuthorData(byAuthorRaw);
      const schoolKey = (p.school_id !== undefined && p.school_id !== null) ? String(p.school_id) : null;
      const school = schoolKey ? (schoolsMap.get(schoolKey) || null) : null;
      return combineOne({ philosopher: p, byAuthor, school, blueprints: globalBlueprints, logic, bibliography, discussionHooks, personaCores, modernAdaptations });
    },
    MAX_CONCURRENCY
  );

  // Filter out nulls if any
  return combined.filter(Boolean);
}

async function writeToRedis(client, key, value) {
  const payload = JSON.stringify(value);
  if (MASTER_TTL_SECONDS > 0) {
    await client.set(key, payload, { EX: MASTER_TTL_SECONDS });
  } else {
    await client.set(key, payload);
  }
}

async function maybeWriteJson(filename, data, enabled) {
  if (!enabled) return;
  try {
    await fs.writeFile(filename, JSON.stringify(data, null, 2), 'utf-8');
  } catch (e) {
    console.error(`Failed to write JSON ${filename}:`, e.message || e);
  }
}

async function main() {
  const args = new Set(process.argv.slice(2));
  const writeJson = args.has('--write-json') || process.env.WRITE_DEBUG_JSON === 'true';

  console.time('orchestrator_total');
  const redis = createClient({ url: REDIS_URL });
  redis.on('error', (err) => console.error('Redis Client Error', err));
  await redis.connect();

  try {
    console.log(`[Orchestrator] FASTAPI_BASE_URL=${FASTAPI_BASE_URL} | Redis=${REDIS_URL}`);

    const [allCombined, activeCombined] = await Promise.all([
      buildDataset(null),    // all
      buildDataset(1),       // only active chat
    ]);

    console.log(`[Orchestrator] Combined counts: all=${allCombined.length} active=${activeCombined.length}`);

    await writeToRedis(redis, REDIS_KEY_ALL, allCombined);
    await writeToRedis(redis, REDIS_KEY_ACTIVE, activeCombined);

    await maybeWriteJson('/app/master_orchestrator.json', allCombined, writeJson);
    await maybeWriteJson('/app/master_orchestrator_active.json', activeCombined, writeJson);

    console.log(`[Orchestrator] Stored in Redis keys: ${REDIS_KEY_ALL}, ${REDIS_KEY_ACTIVE}`);
    if (MASTER_TTL_SECONDS > 0) console.log(`[Orchestrator] TTL set to ${MASTER_TTL_SECONDS}s`);
  } catch (e) {
    console.error('[Orchestrator] Failed:', e?.message || e);
    process.exitCode = 1;
  } finally {
    await redis.disconnect().catch(() => {});
    console.timeEnd('orchestrator_total');
  }
}

if (require.main === module) {
  // Node 18+ has global fetch
  if (typeof fetch !== 'function') {
    console.error('Global fetch is not available. Use Node 18+ runtime.');
    process.exit(1);
  }
  main();
}

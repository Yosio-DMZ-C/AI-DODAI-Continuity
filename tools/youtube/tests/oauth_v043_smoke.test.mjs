import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../worker.oauth.v0.4.3.mjs';

const root = 'https://adnc-youtube-private.yosio-hasenaka.workers.dev';
const env = {
  GOOGLE_CLIENT_ID: 'example-client-id.apps.googleusercontent.com',
  GOOGLE_CLIENT_SECRET: 'example-only-not-a-secret',
  AUTH_SETUP_KEY: 'A'.repeat(48),
  EXPECTED_CHANNEL_ID: 'UC_EXAMPLE_ONLY',
  AUTH_REDIRECT_URI: root + '/auth/callback',
  MCP_API_KEY: 'M'.repeat(48),
};

test('OAuth UI permits same-origin fetch while prohibiting outside connections', async () => {
  const resp = await worker.fetch(new Request(root + '/auth/start'), env);
  assert.equal(resp.status, 200);
  const csp = resp.headers.get('Content-Security-Policy');
  assert.match(csp, /default-src 'none'/);
  assert.match(csp, /connect-src 'self'/);
  assert.doesNotMatch(csp, /connect-src \\*/);
  assert.match(csp, /script-src 'nonce-/);
  assert.equal(resp.headers.get('Cache-Control'), 'no-store, max-age=0');
});
test('Unauthenticated OAuth POST fails', async () => {
  const resp = await worker.fetch(new Request(root + '/auth/start', { method: 'POST' }), env);
  assert.equal(resp.status, 401);
});
test('Existing health check and unauthorized MCP rejection remain intact', async () => {
  assert.equal((await worker.fetch(new Request(root + '/health'), env)).status, 200);
  const resp = await worker.fetch(new Request(root + '/mcp', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'ping' })
  }), env);
  assert.equal(resp.status, 401);
});
test('Signed OAuth request is restricted to expected redirect, uses PKCE S256', async () => {
  const req = new Request(root + '/auth/start', {
    method: 'POST', headers: { Authorization: 'Bearer ' + env.AUTH_SETUP_KEY }
  });
  const resp = await worker.fetch(req, env);
  assert.equal(resp.status, 200);
  const { authorization_url } = await resp.json();
  const url = new URL(authorization_url);
  assert.equal(url.hostname, 'accounts.google.com');
  assert.equal(url.searchParams.get('redirect_uri'), env.AUTH_REDIRECT_URI);
  assert.equal(url.searchParams.get('code_challenge_method'), 'S256');
  assert.match(url.searchParams.get('code_challenge'), /^[a-zA-Z0-9_-]{43}$/);
  assert.match(resp.headers.get('Set-Cookie'), /HttpOnly; Secure; SameSite=Lax/);
});

# AD&C YouTube Worker v0.4.3 — Codex引継ぎ・本番導入チェックリスト

- 対象: Cloudflare Worker `adnc-youtube-private` **のみ**
- 状態: **GitHubに候補コード登録済み・本番未デプロイ**
- この手順の根拠: 本人がCodex公式Cloudflare MCPから取得した本番Worker照合結果（2026-10-20）、GitHubブランチ上の候補コード、Cloudflare公式 API ドキュメント
- 既存機能: `/health`、`/mcp`、`UPLOADS_KV`、`EXPECTED_CHANNEL_ID`、既存 Google Client ID / Secret を維持する
- **YouTubeへの投稿、Drive原本削除、公開範囲変更は絶対に実行しない。**

## デプロイ対象（コード正本）

`https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity/blob/feature/adnc-youtube-tools-v0-2-20261020/tools/youtube/worker.oauth.v0.4.3.mjs`

Raw: `https://raw.githubusercontent.com/Yosio-DMZ-C/AI-DODAI-Continuity/feature/adnc-youtube-tools-v0-2-20261020/tools/youtube/worker.oauth.v0.4.3.mjs`

候補SHA-256：`2f0817a3b379cabfa4be77a40130e0ab6c3cf5e7ac04bb458e0ec58d703aa088`。**デプロイ直前にダウンロードしたコードでこの値を検査すること**。GitHubに保存されている別の古い `worker.oauth.v0.4.2.mjs` は**使用禁止（CSPによりブラウザのfetchが遮断されるバグあり）**。

ローカル検証（Node 22）：構文PASS、模擬テスト **18/18 PASS**。GitHubのCIスモークテスト: `tests/oauth_v043_smoke.test.mjs`。実Google認証・実YouTube投稿は未検証。

## 本番変更前の必須ゲート

1. Cloudflare公式MCPの `search` で **Workerスクリプト内容のGET**、**Worker binding/settings GET**、および**コード本文だけのPUT** のAPI仕様を確認。GETはこれまで実機PASS。書込みスコープが現在Read onlyなら、本人に最小限の `Workers Scripts Write` または対象Worker限定Editorのみを要求し、**認証ダイアログの承認を人間に依頼**。Full accessの自動選択は禁止。
2. **本番スクリプトの再GET/ハッシュ検査**：想定 **12,392 bytes, SHA256 `28923a2bc522c7c79acb18f2ebeb8e20f08e7390b6a7a38a6dd82d7f9288560e`**。先頭LF1バイト除去後 **12,391 bytes / SHA256 `d91d362cee4a6387f95c066b031e7caf5de8b04c3b898500567111fb1fa5fa74`**。これ以外なら**変更を停止**し、追加差分を報告。
3. 現在の本番スクリプトの**完全なバイト列**と変数の**名前・型（値は取らない）**、Bindings情報、スクリプト設定を本人PCのローカルな復旧領域にバックアップ。**ChatGPT会話・GitHub・コンソール出力へSecretの値を含めない**。すでに登録済みの `GOOGLE_CLIENT_SECRET`、`AUTH_SETUP_KEY` はSecretのまま。
4. GitHub候補v0.4.3と本番の差分が **`/auth/start`、`/auth/callback` の認証機能の追加と `fetch` の分岐1行のみ**であることを確認。既存のMCP実装・KVキープロトコルは不変であるべき。
5. ここまで全てPASSなら、ユーザーはこの会話で本番変更の進行を許可済み。**本番デプロイ用の実際のMCP実行確認（「一度だけ許可」）は本人に委ねてよい**。許可不能ならここで停止。

## デプロイ方式（最優先）

Cloudflare公式 **「Replace Worker Script Content」** APIのみを使う：

`PUT /accounts/{account_id}/workers/scripts/adnc-youtube-private/content`

これはCloudflareが **“Replace Worker script content without touching config or metadata”** と説明しているAPI。既存のKV Binding・Variables・Secretsを維持するため、**一般の `PUT /workers/scripts/{script_name}` にコードをそのままPOST/PUTしない**。APIメタデータは `main_module: 'worker.js'`、同名でJavaScript ES Moduleパートをmultipartで添付。MCP `execute` からmultipartでこのAPIを実行できるかは**未検証**。API仕様に準拠していなければデプロイを試さず停止。

公式根拠:
- https://developers.cloudflare.com/api/resources/workers/subresources/scripts/subresources/content/methods/update/
- https://developers.cloudflare.com/workers/authorization/

**MCPツールがmultipart PUTを扱えない場合は、APIキーを発行したり、別サービス・GitHub Actions経由で勝手に代行したりせず停止**。既存WorkerのWebエディタを使う人間操作へ切り替える。新規Workerを作らない。

## デプロイ後のゲート（いずれもGET／無認証拒否テスト）

- 本番コードを再取得し、候補v0.4.3への一致確認（正規化前後のHash/差分の扱いを区別）。
- Worker Bindings/Variablesの**名前・型**とKV ID `210bbeeee68442b5a02bff985cf8b04e`を再GET。特に `UPLOADS_KV`、`AUTH_SETUP_KEY` Secret、`GOOGLE_CLIENT_SECRET` Secret が消えていないことを確認。
- `GET /health` → HTTP 200、旧JSON内容を維持。
- `POST /mcp`（認証ヘッダーなし）→ HTTP 401。**認証鍵をチャットへ表示せず、成功した認証POSTはしない**。
- `GET /auth/start` → HTTP 200、`Content-Security-Policy` に `connect-src 'self'`、`Cache-Control: no-store`、`AUTH_SETUP_KEY` 入力フォームを確認。
- `POST /auth/start`（認証ヘッダーなし）→ HTTP 401。
- **Google OAuthへのリダイレクト、本番更新トークン取得、YouTubeアップロードは別工程**。ここで自動実行しない。
- 異常が1件でもあれば **最初に退避したスクリプト本体を同じcontent-only APIで復元**し、`/health` と無認証 `/mcp` を再検査する。認証情報は削除しない。

## 報告書フォーマット（抜粋）

```
DEPLOY: PASS / FAIL / NOT_RUN
MCP search/execute: PASS/FAIL
書込スコープ: 対象Worker限定 / Worker scripts Write / 未取得
本番旧SHA256: ...
GitHub候補SHA256: 2f0817a3b379cabfa4be77a40130e0ab6c3cf5e7ac04bb458e0ec58d703aa088
バックアップ保存先: ローカルパス（Secret値・コード本文は出さない）
使用したAPI: GET /... , PUT /.../content
本番更新後のSHA256: ...
Bindings保持: PASS/FAIL
/health: HTTP ...
/mcp (unauthenticated): HTTP ...
/auth/start GET: HTTP ...
/auth/start POST (unauthenticated): HTTP ...
Rollback: NOT_NEEDED / DONE / FAILED
NEXT_HUMAN_ACTION: ...
```

## Google認証の次工程（本番デプロイPASS後）

1. 本人のChromeで `https://adnc-youtube-private.yosio-hasenaka.workers.dev/auth/start` を開く。
2. 初回認証の `AUTH_SETUP_KEY` を入力（**SecretはCloudflareから読み戻せない**。元の生成値が不明なら、本人が別の長い乱数にローテーションしCloudflare Secretを更新。キーをチャットへ送らない）。
3. GoogleのOAuthに本人がログイン・許可。チャンネルID `UCrLzqKRdeNsCpSrHPQy8Ifg` の一致を確認。ブラウザの更新トークンは第三者に公開しない。
4. 表示されるコピー操作から `GOOGLE_REFRESH_TOKEN` をCloudflareのSecretとして登録。保存後はブラウザを閉じてクリップボードを消去。別の独立した鍵 `MCP_API_KEY` を後日登録し、`check_connection` で実機試験。
5. Google Driveの原本はYouTubeの非公開投稿成功・映像確認後も本人の明示承認までは削除しない。

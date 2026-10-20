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


## 2026-10-21 実機結果：初回デプロイ HTTP 403（変更なし）

**実行証跡**：本人がCodexのデプロイレポートをチャットに転載。GitHub候補v0.4.3と本番コードを比較後、コードのみの更新が **HTTP 403** で拒否された。**DEPLOY: FAIL（権限不足、実変更なし）**。

| チェック | 判定 |
|---|---|
| 本番/候補SHA-256照合 | PASS |
| バックアップ・差分確認 | PASS（Codex報告）。詳細は本人側の `outputs/deploy-result-v0.4.3.md` |
| コード本体のみの更新 | FAIL — HTTP 403 |
| 403後、元コード維持 | PASS |
| 現行 `/health` | PASS — HTTP 200 |
| 無認証 `/mcp` | PASS — HTTP 401 |
| `/auth/start`（更新後） | NOT_RUN |
| ロールバック | NOT_RUN — 本番無変更のため不要 |

**403の要求スコープ**：MCP実応答では **Workers Scripts Write (`workers-scripts.write`)** を要求。これはすでに許可されているRead onlyだけでは不可。Cloudflare公式はOAuth同意画面 `Additional access > Edit Permissions` で任意権限を個別にON/OFFでき、拒否したスコープが必要になれば再認可するよう案内（https://developers.cloudflare.com/changelog/post/2026-08-22-wrangler-mcp-optional-oauth-scopes/ 、https://developers.cloudflare.com/fundamentals/oauth/authorizing-an-application/）。

### 次に人間が行うこと（OAuthだけ）

1. Windows版ChatGPT/Codexの設定 **MCPサーバー > cloudflare-api** を表示し、サーバー行の歯車または再認証操作から、Cloudflare OAuthの再同意フローを起動する。実画面のボタン名が異なる可能性があるので、操作メニューを確認してから進む。
2. Cloudflareの権限同意画面で `Additional access > Edit Permissions`、`Search scopes` にまず **`Workers`** または **`Workers Scripts`** を入力して、UI表示名 **`Workers Scripts Write`** を探す。実機で `workers-scripts.write` は `No scopes match your search` となったため、API内部スコープ名をUI検索に入れる案内はしない。現在のRead only選択のまま、**この1項目の書込だけを追加し、その他のWriteはOFF**。最後に選択された権限を確認して `Authorize`。最初から `Full access` 全体を選んだまま承認しない。
3. OAuth完了後、Codexで先の手順書を再実行。403が再発すれば中断し、勝手にグローバルAPIキーや別の書込スコープを追加しない。
4. 再認証ボタンが現れなければCloudflare公式の **Manage OAuth authorizations** から旧MCP承認のRevokeを行い、Codex側で再認証する予備手順。ただしRevokeは一時的にMCPを切断するため**本人の了承を得てから**実施する。Cloudflareアカウントや他のアプリは誤ってRevokeしない。

**補足**：Cloudflare OAuthの `workers-scripts.write` は必ずしも当該Worker1件だけに限定されない可能性がある。「Worker単位Editor」等の別のCloudflare権限方式と混同しない。書込権限が追加されても対象Worker `adnc-youtube-private` だけを更新、他のWorker・KV・Secrets・動画・Google Driveは変更禁止。

## 2026-10-21 公式MCPの再認証導線・Base scopes実画面

### 再認証の導線（ユーザー実機スクリーンショットで確認）

- Windows版ChatGPTの **左下ユーザーアイコン → 設定** を開いたところ、画面上部に橙色の通知 **「MCP サーバー『cloudflare-api』に再接続」** が表示された。
- 通知の本文は **「認証の有効期限が切れました。この MCP サーバーを引き続き使用するには再接続してください」**。通知右端の黒いボタン名は **「再接続」**。このボタンを押すとChromeでCloudflare OAuthの `Authorize application` に遷移した。
- ユーザーは設定画面の **コーディング → 接続**（PC/SSHの遠隔操作用）を開いていたが、**この画面とMCPの再認証は無関係**。
- 上部の橙色通知は一時的なものであり、**通知が表示されない場合はこの方法では進められない**。「通知が出ないときの別導線（設定 → MCPサーバー → 対象行の歯車など）」はユーザー実機で未検証。**未確認のメニュー名・ボタン位置を断定しない**。通知がなければ現在のMCP管理画面を表示してもらい操作位置を再確認する。

### Google Chrome上で開いたCloudflare公式OAuth画面

- タイトル **`Authorize application`**、サブタイトル `Grant access to Cloudflare API`、接続アプリ `Codex`。Client ID `https://chatgpt.com/oauth/codex/client.json`、Redirect URI `http://127.0.0.1:<可変ポート>/callback`。可変ポートを手順に固定しない。認証URLの `state` / `code_challenge` をチャットへ貼り付けない。
- **Base scopes** に `Minimal` / `Read only` / `Full access` / **`Requested scopes`** の選択肢（2026-10-21実画面）。この再接続では `Requested scopes` が**初期選択**され、下段に `This client asked for:` と多数の `... Read` ラベル、`and 180 more` が表示された。**Requested scopesが現在の権限をすべて維持する／書込みを含まないとは現画面だけでは判断できない**。
- **安全な今回の操作（実機結果により訂正）**：Read onlyで一旦認証を完了し、Codexからの書込APIでStep-up認可が起動するか検証する。Write項目はこのRead onlyの同意画面では見つかっていない。Full accessは選択しない。
- 書込みスコープはCloudflare公式MCPに **403 `insufficient_scope` で要求された実名**。Full access一括選択はしない。Read onlyがアカウント横断の広範な読取りを許す点も、別途最小化を検討。
- 参照: [Cloudflare 2026-08-22 OAuth権限の任意選択](https://developers.cloudflare.com/changelog/post/2026-08-22-wrangler-mcp-optional-oauth-scopes/) / [Cloudflare 2026-10-19 step-up authorization](https://developers.cloudflare.com/changelog/product/agents/)。
- 認証が完了したら、Codexで元のデプロイ用手順書を**差分再検査・バックアップの確認から再開**し、更新後GETによる読戻しと `/health`, `/mcp` 401の回帰検査を行う。

### 実機補足：権限検索にはAPIの内部識別子を使わない

- 2026-10-21本人Cloudflare OAuth `Edit Permissions` のスクリーンショットで検索欄 `workers-scripts.write` は `No scopes match your search` と表示された。
- Cloudflare公式API権限一覧の正式表示名は `Workers Scripts Write`：https://developers.cloudflare.com/fundamentals/api/reference/permissions/ 。**API内部スコープ識別子とUI検索表示名を混同しない**。まず `Workers` などの部分文字列で検索し、該当する権限のみON。
- 同画面には `194 total permissions` と表示されている。他の書込権限が選ばれていないか最終確認し、確認できなければ Authorizeを押さない。

### 2026-10-21 権限画面：Workers検索にRead項目だけ表示、Step-up方式へ移行

- 2026-10-21のCloudflare OAuth `Edit Permissions` 実機SS：`workers` の検索では `Workers R2 Storage Read`、`Workers Routes Read`、`Workers Scripts Read` が表示された。スクロール領域の一部であり **`Workers Scripts Write` が一覧に存在しないと断定できない**。ただし `workers-scripts.write` では `No scopes match your search` を確認。
- Cloudflare公式は2026-10-19に **Cloudflare API MCP Serverのstep-up authorization** を公開。[公式説明](https://developers.cloudflare.com/changelog/post/2026-10-19-cloudflare-mcp-step-up/)では、MCPクライアントが対応していれば、接続時は低権限のまま、実行時の `insufficient_scope` チャレンジで必要な権限だけ追加認証させ、既存スコープを保持する。
- **案内の修正**：Edit Permissionsで `Scripts Write` を検索して見つからない場合、Full accessプリセットで代用しない。既存Read onlyのまま通常再認証を完了し、Codexへ先の単一Workerコードのみ更新を再試行するよう依頼。その際にMCPクライアントの **step-up追加承認ダイアログが出るか**を確認する。**Codexクライアント側でstep-up対応済みとはまだ未検証**。403だけで承認UIが出なければ操作停止、別途安全なデプロイ経路の検討に切り替える。
- 既存のローカルバックアップと元本照合は維持し、他のCloudflareサービスを変更しない。再認証しただけでは本番コード更新PASSにしない。更新実行前に現行SHAを再GETする。
- 参考：[Cloudflare OAuth任意権限](https://developers.cloudflare.com/fundamentals/oauth/authorizing-an-application/) は「表示される**requested optional scopes**から個別選択」であり、対象Clientが要求していない権限をUIから自由追加できるわけではない。

### 2026-10-21 Read only選択時にWriteが見つからない実機結果

- ユーザーが `Read only` プリセットでCloudflare OAuthの `Edit Permissions` を操作したところ、`workers-scripts.write` / `Scripts Write` のどちらも **`No scopes match your search`**。一方、`workers` では `Workers Scripts Read` 等のみが確認できた。
- 結論：**Read only状態でWrite権限を同じ一覧から追加できるとは案内しない。** OAuthの権限編集は「何でも自由に追加」ではなく当該フローで要求されたスコープの選択画面。少なくとも今回の画面ではWriteを選べていない。
- Cloudflare公式2026-10-19の [step-up authorization](https://developers.cloudflare.com/changelog/post/2026-10-19-cloudflare-mcp-step-up/) に沿い、最初はRead onlyで認証を完了し、CodexがWrite APIを呼ぶ際に `insufficient_scope` を受けたら必要な `Workers Scripts Write` の追加認可が起動するか確認する。**Codex側のstep-up対応は未実証**。再403で追加承認画面が表示されなければ書込試行を停止し、別方式を検討。
- **訂正**：『Read onlyを選択→Edit PermissionsでWriteを検索してON』という従来案内は実機と整合せず標準手順から撤回。Full access一括許可で代用しない。

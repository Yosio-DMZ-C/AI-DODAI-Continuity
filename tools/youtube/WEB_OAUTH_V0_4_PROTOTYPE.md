# AD&C YouTube ブラウザ初回OAuth認証 v0.4（実装試作）

- 更新: 2026-10-20
- 状態: **LOCAL_TEST_PASS / GOOGLE_OAUTH_NOT_RUN / WORKER_DEPLOY_NOT_RUN**
- 対象Worker: `adnc-youtube-private` （本番環境へまだ反映しない）
- 目的: WindowsにPython・Node.js・npmを導入せず、ブラウザ操作だけで、既存Drive動画→YouTube非公開投稿のバックエンド初回OAuth認証を完了する。

## 現在の実機PASS

Cloudflare公式MCPをWindows Codexへ直接登録し、OAuth Read onlyでCloudflareのGET APIへ接続成功。Worker `adnc-youtube-private`、KV `adnc-youtube-uploads` / `UPLOADS_KV`、`EXPECTED_CHANNEL_ID = UCrLzqKRdeNsCpSrHPQy8Ifg` は **Codexの報告上GET 200**（2026-10-20）。MCP `search`、`execute` はPASS、Workerへの書込みは未実施。Claude/Gemini等、別AIから使えることまで検証したわけではない。

## v0.4の実装

試作用の依存ゼロJS `oauth_web_module.mjs` を作成済み。ローカルNode.js 22の模擬テスト **6/6 PASS**。主な機能:

- 既存Workerに `/auth/start` (GET: 本人向け画面、POST: `MCP_API_KEY` が必要) と `/auth/callback` (GET: Google OAuthコード交換) を追加する。
- Web application型のGoogle OAuth Clientを使用し、`offline`、`prompt=consent` でRefresh Tokenを受ける。
- `state` にHMAC署名と10分期限を付し、Secure/HttpOnly/SameSite=Lax Cookieで開始ブラウザを確認。
- 認証後のGoogle YouTube API `channels?mine=true` のIDと `EXPECTED_CHANNEL_ID` を照合。違えばトークン提示禁止。
- 必要スコープが欠けていれば停止。旧Driveアップロード検証のため `youtube.force-ssl` と `drive.readonly` を要求。将来Drive非依存で再設計。
- Refresh TokenはOAuth完了ページの**コピー専用ボタン**から**本人がCloudflare WorkerのSecret `GOOGLE_REFRESH_TOKEN` へ貼り付け**。チャット・URL・KVに保存しない。ただし認証完了ページのHTML/JSには一時的に値を含むため、第三者へ画面やHTMLを共有せず、ブラウザ拡張にも注意。
- GoogleクライアントSecret、MCP_API_KEY、Refresh Tokenをリポジトリへ格納しない。OAuth実行前にHTTPS／CSP／認証制御のコードレビューが必要。

**配布形態**：この会話で検証済みの試作ZIPを成果物として提供。正式採用前にGitHubの原本Workerへ組み込み、モック6件の再検査と本番向けセキュリティレビューを行う。ZIPのリンクはGitHubリポジトリ内には記録しない（会話添付参照）。

## 次のユーザー操作：Google Web OAuth Clientの作成

1. [Google Auth Platform > Clients](https://console.cloud.google.com/auth/clients) で対象Google Cloudプロジェクトを選択する。以前使ったデスクトップ用Clientは**そのまま維持**。
2. 新しいOAuth Clientの種類 **Web application / ウェブアプリケーション** を選び、任意名 `AD&C YouTube Web OAuth`。**「Use this client for an AI-powered agent」はON**。このクライアントは将来ChatGPT→Cloudflare Worker→YouTube REST APIの自動投稿（AIによるツール実行）専用に使用する。GoogleはAIエージェントの代理操作に専用OAuthクライアントを使用するよう案内している。
3. **Authorized redirect URI** を次の値で登録（完全一致）：`https://adnc-youtube-private.yosio-hasenaka.workers.dev/auth/callback`
4. 作成完了だけをAIへ報告。Client SecretやJSONは**安全上チャットへ送信・添付禁止**。
5. 次工程でCloudflare WorkerにWeb Client ID、Web Client Secret、`AUTH_REDIRECT_URI`、`MCP_API_KEY` を設定。現在のCloudflare公式MCPはRead onlyで接続済み。書込みが必要なら影響箇所と対象Workerを示し、最小限の権限をユーザーに再承認してもらう。**これらのSecretをCloudflare公式MCPのチャット実行引数に直接貼らせない**。秘密値はCloudflare管理画面へ本人が入力する。

## 前提・残作業

- Cloudflare本番WorkerにはOAuth bootstrapコードがまだない。モジュール試作だけで `/auth/start` が利用可能と案内しない。
- Cloudflare Workerの `/mcp` は別途ユーザー個人向けプラグインへ接続する必要がある。Cloudflare管理用MCP `cloudflare-api` と YouTube投稿用MCPは**別**。
- 初回Web OAuthのユーザー許可／対象YouTubeチャンネル確認／Refresh Token Secret保存はNOT_RUN。
- 既存動画1件の非公開アップロード後に、APIで `privacyStatus=private` およびYouTubeで動画内容を検証する。第三者との共有を目的とする限定公開への変更は**ユーザー本人のみ**。
- Drive原本の削除は**未実装・未承認**。成功確認後に独立の承認を求める。
- CloudflareのWorkerコードをユーザーがWebエディタで管理しているため、過去のMCP認証・Bindings・変数を壊さない**既存コードへの最小差分**を必須とする。
- OAuth Refresh Tokenが失効する要因はGoogle側のポリシー・アプリ公開状態に依存し、再認証手順を用意する。

## 出典

- [Google OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Cloudflare Workers Secrets](https://developers.cloudflare.com/workers/configuration/secrets/)
- [Cloudflare Workers limits](https://developers.cloudflare.com/workers/platform/limits/)
- [YouTube videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert)

## 追補（2026-10-20）：AI-powered agentチェック

- Google公式 [Manage OAuth Clients](https://support.google.com/cloud/answer/15549257) は、AIがユーザーに代わって操作するOAuth ClientをAgenticとして区別し、通常の対話型クライアントとは別IDを維持するよう推奨している。
- 本Web OAuthクライアントは、ブラウザで本人が初回承認するが**継続的な用途はAIから起動するCloudflare WorkerのYouTube/Drive REST API呼び出し**。そのため `Use this client for an AI-powered agent` を**ON**にする。別のブラウザ人手操作用 `videos.html` のOAuth Web Clientは分離する。
- GoogleのWeb OAuthクライアント作成後はこの種別チェックを変更できない旨が公式クイックスタートに明記されている。すでにOFFで作成した場合、基本は**別のWeb Clientを新規作成**してこちらに採用する。
- Agenticタグは自動で追加権限を与えない。公式: https://developers.google.com/people/quickstart/js

## 2026-10-20 実機確認：Web OAuthクライアントの作成とJSON取得

- ユーザー本人がGoogle Cloud `WPGARankking` で `AD&C YouTube Web OAuth` をWeb applicationとして作成。 `Use this client for an AI-powered agent` を **ON** にして作成し、OAuth Client JSONを自身のPCにダウンロード済みと報告。
- 作成画面の実機SSで **Authorized redirect URI** が `https://adnc-youtube-private.yosio-hasenaka.workers.dev/auth/callback`、JavaScript originsは空であることを確認済み。
- JSON／Client Secret自体の取得・閲覧はユーザーのローカルPCのみ。**チャットにJSON/Secretを添付・貼り付けさせない**。まだCloudflare Worker Secretの登録・v0.4 Worker本番展開・Google OAuth本人同意・YouTube投稿は未実施。
- **初回登録の案内文（ユーザー確認による簡略化）**：Cloudflare Worker `adnc-youtube-private` の **Settings → Variables and secrets → ＋ Add variable** を**3回実行し、下表の①〜③を登録してください。** 一度説明した画面遷移は繰り返さない。迷った場合のみ補足する。

  | No. | Key | Value（JSONから引用符を外した値） | Secret |
  |---|---|---|---|
  | ① | `GOOGLE_CLIENT_ID` | `web.client_id` | **OFF** |
  | ② | `GOOGLE_CLIENT_SECRET` | `web.client_secret` | **ON** |
  | ③ | `AUTH_REDIRECT_URI` | `https://adnc-youtube-private.yosio-hasenaka.workers.dev/auth/callback` | **OFF** |

  対象は **Production**。各入力後 `Add variable and deploy` で保存。Secret値の画面共有禁止。旧Desktop Clientの値と混ぜない。
- **実機結果（2026-10-20）**：ユーザーが上記3回の登録を完了。スクリーンショットで `AUTH_REDIRECT_URI` / `GOOGLE_CLIENT_ID` は `Variable`、`GOOGLE_CLIENT_SECRET` は `Secret` かつ `Value encrypted` を確認。既存 `EXPECTED_CHANNEL_ID` も維持。**環境変数登録 PASS**。ただしWorkerのOAuthコード本番デプロイとGoogle本人認証はまだ NOT_RUN。
- 本番WorkerコードへOAuth試作を組み込む作業は上記と別工程。**認証画面 `/auth/start` が既に動くと案内しない**。

## 2026-10-20 v0.4.1 統合済みレビューパッケージ／デプロイ前ゲート

- 前回の `oauth_web_module.mjs` を **既存Worker単一ファイルへ統合**したレビュー用コード `worker.integrated.mjs` を作成。成果物：会話添付 `ADNC_YouTube_OAuth_Integrated_v0.4.1_REVIEW.zip`（ローカルコンテナで生成。GitHubに機密ファイルはコミットしない）。旧 `worker.mjs` を残し、変更差分 `worker_oauth_review.patch` も同梱。
- セキュリティ改善：初回認証用キーを **`AUTH_SETUP_KEY`** としてCloudflare Secretに**新規独立**。Web認証画面へYouTube MCPの高権限Bearer `MCP_API_KEY` を入力させない（失効／漏えい時の影響を分離）。生成・設定は本人のWindows PowerShellとCloudflare管理画面で実施、チャットへ値は送らない。
- 新規追加されるHTTP経路は `GET /auth/start`、`POST /auth/start`、`GET /auth/callback` のみ。`GET /health`、`POST /mcp` の本体は変更しない。
- **検証**：Node.js v22で `node --check` に成功。古いWorkerの非公開アップロード・重複防止・想定チャンネルID・プライバシー判定等の回帰検査とOAuthの署名付きstate・Cookie・権限・別キー拒否・HTTPルーティングの模擬テストを合わせ **16/16 PASS**。外部APIの本番Google OAuth、トークン取得、Workerデプロイは **NOT_RUN**。
- **要注意**：ローカルで統合した元のWorkerは `ADNC_YouTube_Tools_v0.3.1_DASHBOARD.zip` の `worker.mjs`。GitHubブランチの最新 `worker.mjs` とバイト数が異なる（GitHub読出し12,170文字／ローカル旧アーカイブ12,391 bytes）。**現行のデプロイ済みWorkerと差分を突き合わせず、統合ファイルを丸ごと貼り付けて上書きしない**。CodexのCloudflare公式MCP（現在Read only）で本番WorkerのコードをGET読戻しして照合するまではデプロイを止める。
- **次のユーザー作業は1回のみ**：Cloudflare `adnc-youtube-private` → Settings → Variables and secrets → `＋ Add variable` → `Key=AUTH_SETUP_KEY`、`Secret=ON`、`Value=本人がPowerShellで生成した48バイト乱数のBase64`。登録後に存在だけ報告し値は送らない。PowerShell:

  ```powershell
  $b = New-Object byte[] 48
  $r = [Security.Cryptography.RandomNumberGenerator]::Create()
  try { $r.GetBytes($b) } finally { $r.Dispose() }
  [Convert]::ToBase64String($b) | Set-Clipboard
  Write-Host '初回認証キーをクリップボードへコピーしました'
  ```

- 本番デプロイ前に、**現在の実行中Workerのバックアップ→最小差分レビュー→人間承認→デプロイ→/health・/mcp認証拒否を再検証**。Google更新トークンは別工程で本人がCloudflare Secret `GOOGLE_REFRESH_TOKEN` に貼り付ける。
- 今回生成した単体ZIPは本番Workerのソースバックアップではない。ローカルの模擬テストPASSと本番デプロイPASSを混同しない。

## 2026-10-20 実機：AUTH_SETUP_KEY 登録完了

- ユーザー提供Cloudflare Worker設定画面で `AUTH_SETUP_KEY` が **Secret / Value encrypted** として登録済み（Production）。既存 `GOOGLE_CLIENT_SECRET` もSecretのまま、`GOOGLE_CLIENT_ID`、`AUTH_REDIRECT_URI`、`EXPECTED_CHANNEL_ID` を確認。**設定項目の存在とSecret型はPASS**。値の正確さ／機能は未検証。
- レビューパッケージ `ADNC_YouTube_OAuth_Integrated_v0.4.1_REVIEW.zip` を再検査。Node.js v22.16.0で `node --check worker.integrated.mjs` PASS、2つのテストスイート合計 **16/16 PASS**。ローカル模擬試験であり本番実動作の証明ではない。
- **次はCodex Cloudflare公式MCPを使用したGET専用確認**：現在デプロイ済みWorker `adnc-youtube-private` のスクリプト本文を読み取り、GitHubブランチ `feature/adnc-youtube-tools-v0-2-20261020` の `tools/youtube/worker.mjs` と比較。本文全体やSecretらしい値はユーザー宛てに表示しない（ハッシュ、ファイル長、差分概要、ルーティング・Binding確認など安全なメタ情報だけ出す）。ソース内の埋込認証情報に遭遇したら値は出さずに注意を促す。
- 元ファイルが**完全に一致**すれば、同一版を元にしたOAuth統合コードを最小差分で適用する計画へ進める。不一致の場合は差分を慎重にレビューし、既存機能を消す可能性のある丸ごと上書きを行わない。
- 本作業はCloudflare MCP `Read only` 権限のみ。API書き込み・再デプロイ・Secret取得・Drive削除・YouTube投稿は行わない。

### 比較用ソース指紋（2026-10-20）

- レビューZIP内 `worker.mjs`（統合前の元ソース）：**12,391 bytes**、SHA-256 **`d91d362cee4a6387f95c066b031e7caf5de8b04c3b898500567111fb1fa5fa74`**。
- レビューZIP内 `worker.integrated.mjs`（OAuth追加済みの候補、未デプロイ）：**22,190 bytes**、SHA-256 **`1adf526a545793aecca48643e920f60e6141f68481fa7f464af0cb071c126993`**。
- バイト差は意図したレビュー対象であり、ライブWorkerのコードがリリース形式／改行処理により変わる場合はハッシュ一致しない。ハッシュ不一致だけで不具合断定せず、差分のレビューを要する。

## 2026-10-21 本番ソース照合PASS／OAuth v0.4.2レビュー候補

**入力証跡:** ユーザーがCodex Cloudflare公式MCPのRead only結果をこのチャットへ提示（実行レポート）。全対象GETはHTTP 200、デプロイなどの変更なし。

| 項目 | 判定と根拠 |
|---|---|
| 本番Worker GET | PASS: `worker.js` 1ファイル、**12,392 bytes** |
| 本番Worker SHA-256 | `28923a2bc522c7c79acb18f2ebeb8e20f08e7390b6a7a38a6dd82d7f9288560e` |
| 先頭LF除去後の一致 | PASS: **12,391 bytes**、元ファイルSHA `d91d362cee4a6387f95c066b031e7caf5de8b04c3b898500567111fb1fa5fa74` |
| GitHub参考ソースとの内容照合 | PASS（Codex報告）：先頭・末尾のLF各1文字のみ差分 |
| `/health`、`/mcp`、`UPLOADS_KV`、認証・非公開アップロードの静的処理 | PASS（静的読取のみ） |
| `MCP_API_KEY` / `GOOGLE_REFRESH_TOKEN` | 現在のBindings一覧に未登録との報告。Secretの値は取得なし |
| 本番への実デプロイ・Google OAuth・動画アップロード | **NOT_RUN** |

### v0.4.2 レビュー成果物（ローカル作成、未デプロイ）

- v0.4.1統合候補に **PKCE S256** を追加。各リクエストの `code_verifier` を別の秘密 `AUTH_SETUP_KEY` と状態ノンスのHMACから導出、認可URLへ `code_challenge` と `code_challenge_method=S256`、Googleトークン交換時へ `code_verifier` を追加。既存Workerの本体コードは、OAuthへの早期分岐2行を追加する以外不変。
- Node.js 22.16.0で `node --check` PASS。オリジナル/新OAuthモック含む **17/17 PASS**（新PKCEチャレンジとVerifier一致のテスト1件追加）。ライブAPI検証ではない。
- 候補本体 `worker.oauth.v0.4.2.mjs` SHA-256: **`2f6710f915e63e507c4daa828db18d4c05bb52d23cbdb975cb72692d112c153a`**。
- 差分 `worker.oauth.v0.4.2.patch`、元コード `worker.base.mjs`、検査テストと `REVIEW_NOTES.md` をまとめた**レビューZIP**を本チャットで出力。ZIPの名前 `ADNC_YouTube_OAuth_Integrated_v0.4.2_REVIEW.zip`。GitHubにレビューZIP本体は登録していないが、**実装候補ソースを [worker.oauth.v0.4.2.mjs](worker.oauth.v0.4.2.mjs) に新規コミット済み（commit ec840560475c3b5fb77ef9298a6ce426278a0782）**。登録後にローカルの候補ソースとGitHubから読み戻したテキストの完全一致を確認した。**GitHub既存の `worker.mjs` を上書きしていない。本番デプロイも未実施**。
- 本番Workerへのコード変更は**ユーザーの明示承認待ち**。Cloudflare公式MCPはRead onlyなので、書込スコープを必要最小限にして再認可が必要。承認後は本番コードを個別バックアップし、差分をレビューしてからデプロイし、`/health` / 未認証`/mcp` の回帰テストを実施。
- この段階でユーザーに依頼するCloudflare Secretの登録は**なし**。まずデプロイの承認と方法を決める。次段階でGoogle OAuth実認証→ `GOOGLE_REFRESH_TOKEN` Secret設定、その後別々の乱数Secret `MCP_API_KEY` の設定。両者を `AUTH_SETUP_KEY` と混同・再利用しない。
- **要注意**：OAuth完了ページのHTML/JSには一時的に更新トークンが存在する。URLや通常の画面には表示しないが、ページソース・ブラウザ拡張からは見える可能性がある。チャットへのスクリーンショット・HTML・トークンの送付は禁止。Google Driveソースファイルの削除は引き続き禁止。

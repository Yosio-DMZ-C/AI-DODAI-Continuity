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

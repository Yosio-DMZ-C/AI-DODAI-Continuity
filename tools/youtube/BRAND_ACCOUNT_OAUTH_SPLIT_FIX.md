# AD&C YouTube Brand Account OAuth 認証障害 — 修正指示（2026-10-21）

## 現状

- 本番 Worker `adnc-youtube-private` v0.4.3 デプロイ：Codex報告 **PASS**（コード読み戻し／設定・Secret保持／`/health` 200／無認証 `/mcp` 401／`/auth/start` GET 200・POST 401）。
- ユーザーが初回 Google OAuth のアカウント選択で **「AI-DODAI & Continuity」**（対象YouTubeブランドチャンネル）を選択すると、Google画面に **「サービスをご利用いただけません／お使いのアカウントで利用できないサービスにアクセスしようとしました」** と表示された。OAuth同意画面に到達せず、**更新トークンは未取得**。
- 現行v0.4.3の `ADNC_AUTH_SCOPE` は `https://www.googleapis.com/auth/youtube.force-ssl` と `https://www.googleapis.com/auth/drive.readonly` を同一Googleアカウントに要求している。
- **優先原因仮説：YouTubeブランドアカウント（Google Driveを持たない）にDrive権限まで求めた**。Google公式Issue Tracker [538926827](https://issuetracker.google.com/issues/538926827) で同一症状が報告され、**Drive scopeを外すとBrand Accountの認証が成功**。別の公式Issue Tracker [569129170](https://issuetracker.google.com/issues/569129170) でも非YouTubeスコープとの混用が障害要因と記載。
- 今回の認証エラーは **Google OAuth側で発生**。ユーザーに別のチャンネルを選ばせて回避しない。現在の本番コード・Bindings・Secretはそのまま。

## 正式修正方針：YouTubeとDriveの認証を分割

1. **YouTube権限のOAuth**：`youtube.force-ssl` のみを要求し、対象ブランドチャンネル **`UCrLzqKRdeNsCpSrHPQy8Ifg`** を本人が選択。認証後 `channels.list?mine=true` によるチャンネルID一致を必須とし、得られたrefresh tokenは従来名 `GOOGLE_REFRESH_TOKEN` のSecretに保存する。
2. **Drive権限のOAuth**：`drive.readonly` のみを要求し、**個人のGoogleアカウント**を選択。Drive `about.get?fields=user(emailAddress,displayName)` 等を使ってDrive権限を検査し、別の `GOOGLE_DRIVE_REFRESH_TOKEN` Secretに保存する。ユーザーがDriveへアクセスできることの検証は、必要時に対象 `drive_file_id` のメタデータGETで行う。Google Driveへ書込み・削除しない。
3. **アップロードWorker**：YouTube API（チャンネル照合、resumable videos.insert、非公開確認）はYouTube用token、Drive API（files metadata、alt=media Range取得）は**Drive用token**でそれぞれ呼ぶ。認証情報が不足している状態では実アップロードを開始しない。
4. 初回認証ページは `/auth/start` をYouTube用既定、`/auth/start?mode=drive` をDrive用に分けてよい。既存のGoogle OAuthクライアントID／Secretと `/auth/callback` を再利用可能。ただし**認証のmodeをHMAC署名済みOAuth stateに結合**し、PKCE S256・SameSite=Lax HttpOnly Secure Cookie・10分の期限を維持。コールバック時にmodeと要求スコープ・本人IDを検証し、誤ったSecret名で更新トークンを保存しない。
5. 新しい権限は要求しない。YouTube側のDrive scopeを除くことで権限を縮小するだけ。Googleアカウントとブランドアカウントの選択画面を混同させない。
6. 既存の `/health`, `/mcp`, `UPLOADS_KV`, `EXPECTED_CHANNEL_ID`, `AUTH_SETUP_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `AUTH_REDIRECT_URI` は維持。既存のアップロード重複防止・YouTubeプライバシー private 強制・「公開は人間のみ」も維持。**Drive原本を削除しない**。

## テスト／デプロイ品質ゲート

- まずGitHubのv0.4.3から **v0.4.4修正候補を新規ファイルとして作成**。既存のv0.4.3を直接上書きしない。
- ローカルNode等のモックで、①YouTube認可URLはYouTube scopeのみ、②Drive認可URLはDrive scopeのみ、③mode改ざんのstate拒否、④OAuthコールバックのサービスごとの確認と保存名、⑤YouTubeはYouTube token、DriveはDrive token、⑥誤チャンネル拒否、⑦既存/healthと無認証/mcp、⑧private強制と重複防止を回帰検査。認証トークンの内容をログへ出さない。
- 実環境の **GETソースバックアップ→差分検査→設定保持のままcontent-only APIでデプロイ→ソースGET読戻し→ルート・認証拒否・CSP・Bindings確認**。異常なら旧ソースへロールバック。
- **MCP_API_KEY / GOOGLE_REFRESH_TOKEN / GOOGLE_DRIVE_REFRESH_TOKEN はチャット・GitHub・ログへ送信・出力しない**。Google OAuthの本人同意およびSecret値のCloudflare入力は本人だけが行う。
- 修正バージョンの本番導入がPASSするまでは、旧 `/auth/start` を用いたBrand Account OAuthの再試行を案内しない。
- Google OAuth Web Serverの公式資料：https://developers.google.com/identity/protocols/oauth2/web-server
- Google Drive about.get：https://developers.google.com/workspace/drive/api/reference/rest/v3/about/get

## 人間への確認事項

- 初回Google OAuthのサービス拒否画面にはトークンはない。JSON/Secret/認証URLのcode・stateをスクリーンショット／チャットへ送らない。
- v0.4.4をデプロイした後、まずYouTubeブランドアカウント認証→本人がSecret `GOOGLE_REFRESH_TOKEN` 登録。続いて個人GoogleアカウントのDrive認証→本人がSecret `GOOGLE_DRIVE_REFRESH_TOKEN` 登録。その後MCP_API_KEY設定・接続試験へ進む。

## v0.4.4 本番デプロイ実機報告（2026-10-21）

ユーザーがCodex実行結果をチャットに貼付。詳細ログのローカルパスはこのチャットから直接閲覧しておらず、以下はCodex報告に基づく。

| 項目 | Codex報告 |
|---|---|
| YouTube/Driveの認証分離 | PASS |
| モックテスト | PASS 16/16 |
| 本番バックアップ・差分検証 | PASS |
| コードのみの更新と本番GET読戻し一致 | PASS |
| Bindings・Variables・Secrets保持 | PASS |
| 本番回帰検査 | PASS 8/8 |
| ロールバック | NOT_RUN：不要 |
| Google本人認証・秘密値の登録 | NOT_RUN：本人操作待ち |
| 動画の公開・Google Drive原本の削除 | NOT_RUN |

詳しいCodex報告は本人PCの C:/Users/Yosio/Documents/Codex/2026-10-21/v0-4-3/outputs/v0.4.4/deploy-result-v0.4.4.md。

### 人間だけが行うGoogle OAuth認証

1. [YouTube認証](https://adnc-youtube-private.yosio-hasenaka.workers.dev/auth/start) にアクセスし、本人のAUTH_SETUP_KEYで開始。GoogleでAD&Cブランドチャンネル AI-DODAI & Continuity を選択し、YouTubeのみの権限を確認して本人が同意。チャンネルIDの一致を確認した後、表示される更新トークンを Cloudflare Worker Settings → Variables and secrets → ＋ Add variable → GOOGLE_REFRESH_TOKEN（Production、Secret ON）へ直接登録。
2. [個人Drive認証](https://adnc-youtube-private.yosio-hasenaka.workers.dev/auth/start?mode=drive) にアクセスし、同じAUTH_SETUP_KEYで開始。個人Googleアカウントを選択してDrive読み取り権限だけ本人が同意。更新トークンを GOOGLE_DRIVE_REFRESH_TOKEN（Production、Secret ON）へ直接登録。
3. OAuth成功ページには更新トークンが含まれる。スクリーンショット／HTML／トークン／code・state付き認証URLをチャットやGitHubへ共有しない。秘密値はユーザー本人がCloudflareへ転記し、成功後にクリップボードを消去。
4. 両Secret登録後、独立したMCP_API_KEYの設定と、動画アップロードを伴わない接続試験へ進む。

**ソース保管上の注意:** このチャットから同GitHubブランチの tools/youtube/worker.oauth.v0.4.4.mjs を確認したところ404。Codexの修正版が本番に導入されたとの報告はあるが、GitHubレビュー用ソースが同期されている証拠はない。現行本番コードを安全にバックアップ済みであることを確かめ、Secret値や認証情報をGitHubに載せずにレビュー候補を保存する工程が必要。既存v0.4.3ファイルをv0.4.4と誤認しない。

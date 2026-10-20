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


### 2026-10-21 Google Drive refresh token Secret登録実機確認

ユーザー提供のCloudflare Production設定画面で、YouTube側 `GOOGLE_REFRESH_TOKEN` とDrive側 `GOOGLE_DRIVE_REFRESH_TOKEN` がともにType=Secret、Value encryptedとして存在することを確認。Google Driveの権限同意画面では個人GoogleアカウントのDriveファイル表示・ダウンロード権限のみが提示された。Secret値やトークンの有効性は読み取っていない。次の作業は未登録の `MCP_API_KEY` を独立した乱数で生成し、Cloudflare ProductionのSecretとして登録後、投稿を伴わないMCP接続試験を実施すること。動画の投稿・公開とDrive原本削除は依然NOT_RUN。

### 2026-10-21 MCP_API_KEY 追加を画面で確認

ユーザーのCloudflare Production / Runtime variables and secrets の画面に `MCP_API_KEY` がType=`Secret`、Value=`Value encrypted` と表示された。既存の `GOOGLE_REFRESH_TOKEN`、`GOOGLE_DRIVE_REFRESH_TOKEN`、`AUTH_SETUP_KEY`、`GOOGLE_CLIENT_SECRET` もSecretとして残っている。**設定項目の存在のみPASS**。MCP Bearer認証、refresh tokenのGoogle受理、対象YouTubeチャンネルID、Drive API疎通は**NOT_RUN**。
次はMCPの `initialize` と `check_connection` を投稿なしで検証。`MCP_API_KEY` の値はChatGPTチャット、GitHub、ログに出さない。登録直後のクリップボードに鍵が残っている場合は利用者PC内のPowerShellからBearerヘッダーで試験できる。現在チャットからCloudflareのSecretを取得したり、公式Cloudflare MCPで同Workerの認証済みMCPツールを直接実行したりはできない。

### 2026-10-21 実証：MCP initialize / check_connection PASS とキー管理改善

**ユーザー実行のPowerShell応答（キー非表示、動画投稿なし）**：

| 項目 | 確認結果 |
|---|---|
| `POST /mcp` → JSON-RPC `initialize` | `MCP initialize: PASS` |
| `tools/call: check_connection` | `state: ready` |
| 対象チャンネルID | `UCrLzqKRdeNsCpSrHPQy8Ifg` と一致 |
| 投稿モード | `upload_mode: private_only` |
| 公開操作 | `human_publication_required: true` |
| Google Driveの実データ取得 | 未検査（応答にDrive個別の疎通結果なし） |
| YouTube非公開アップロード / 動画公開 / Drive原本の削除 | 未実施 |

ユーザー指摘：**『生成したキーをクリップボードにコピー』→『次のPowerShellコマンドをコピー』の順では秘密値が上書きされる**。これは手順設計上の欠陥。ユーザーがクリップボード履歴で復旧したことを汎用解決策として扱わない（履歴への秘密値残留・クラウド同期に注意）。

**標準の修正案**：

1. 最初に『この作業で使用する鍵』と役割を1行で説明し、利用者がキーやパスワードをチャットへ貼らないことを明記。設定項目名と値（乱数文字列）を混同しない。
2. 既存のキーを試験する場合は、**検査コマンドの実行後に `Read-Host -AsSecureString` で入力させる**。値は表示させない。ただしSecureStringでもプロセス中に必要な平文に変換され得るので万能な秘密保護ではない。
3. キーを新規発行してCloudflareに登録する場合は、**1本のPowerShell手順で生成→クリップボードへ一時コピー→人間がCloudflareのSecretに貼り付け→同じPowerShellプロセスのメモリ上に保持したキーで自動接続検査→クリップボード消去→プロセス終了**まで行う。途中で別のコードコピーを要求しない。この一時鍵はファイルに保存しない。
4. **メモ帳などの平文ファイルへの一時保存は既定にしない**。誤保存・OneDrive同期・バックアップ・クリップボード履歴・画面共有で漏洩する可能性がある。もし手動転記が避けられない場合も一時的な取り扱いとし、秘密はスクリーンショット・ログ・GitHubへ載せない。
5. 試験終了後に削除してよいのは**ユーザー側の一時コピーだけ**。CloudflareのSecret値は運用中必要なため削除しない。**クライアント側にも将来Bearer認証を行うためのキーが必要**：継続接続するならOSの資格情報保管庫・信頼できるパスワードマネージャー・プラグインの秘密入力機構のいずれかに保存し、平文 `.env` や公開ZIPへの直接埋込は避ける。保存せず一度限り使う方針なら再利用できず、失われたキーはCloudflare側でローテーションが必要。
6. できるだけ将来はユーザーがキーを扱わないOAuth接続／安全なシークレット保管方式を検討。**最初から個人用の非公開プラグインやMCPクライアントへBearer値を保存してよいとは限らない**ため仕様・保存先を実機確認してから採用。

**次ゲート**：`list_uploaded_videos` 等の**読み取りのみ**の検査、Drive用トークンを使用するコードと実Drive疎通の検証、ChatGPT/Codexへの専用MCP接続の安全な手順化。ユーザーによる明示指定までは `upload_private_from_drive` を実行しない。

### 2026-10-21 個人用プラグイン AD&C YouTube Ops v0.1.0 作成

- 私有プラグインの作成を完了（利用者個人スコープ、Private）。[AD&C YouTube Ops](https://chatgpt.com/plugins/plugins_6ad7b5f434e08191994c39a1c3e44203)、name=`adnc-youtube-private`、version=`0.1.0`。
- MCP endpoint=`https://adnc-youtube-private.yosio-hasenaka.workers.dev/mcp`、`streamable-http`、クライアント側認証宣言=`api_key` + `headerScheme: bearer`。プラグインZIPはコードと設定だけで、**Bearer Secretの値、Cloudflare Secret、refresh tokenは含めていない**。作成後にAPIキースキームとSkillsの保存内容を読戻して確認した。
- 権限表示はRead, Write。デフォルトプロンプトは`check_connection`専用、Skillsでは非公開投稿はユーザーから明示指示がある場合のみ許可し、公開・削除・Drive整理は禁止。秘密を会話に貼る案内禁止。
- **MCPプラグイン経由の初回接続・APIキー入力・ツール検査はNOT_RUN**。Codex/ChatGPTのAPIキー認証UIが現行環境で機能するかは本人画面を見て確認が必要。OpenAI公式は固定Bearerトークン用の `auth.type=api_key` / `headerScheme=bearer` を文書化するが、投稿ポータルや一部クライアントではセットアップ方法に制約がある：https://developers.openai.com/plugins/build/plugins
- 次ゲート：本人がリンクを開き、接続UIに**秘密値をチャットへ送らず直接入力**できるならプラグインを有効化。接続先MCPの`check_connection`のみを起動してチャンネル一致を検査。安全なUIがない場合はSecretをマニフェストへ埋め込まず、CodexのローカルMCP接続でOSの秘密情報保管を使う方式を検討する。
- **未解決**：Drive API疎通の独立検証、本番v0.4.4ソースのGitHub同期、テスト動画の非公開アップロード。接続確認に成功するまでユーザーの動画は投稿しない。

### 2026-10-21 プラグイン画面からの接続：APIキーUI非対応（方式変更）

- ユーザーのCodexデスクトップ版：インストールした個人用プラグイン `AD&C YouTube Ops` のページにはMCP `Adnc-youtube-private` が表示される。しかし右端の歯車を押すと、**プラグインの認証画面ではなく設定 → MCPサーバー管理一覧**へ遷移する。管理一覧には `cloudflare-api`, `node_repl` の2件のみが表示され、AD&C YouTube MCPは直接設定できない。
- 既存プラグインの `mcp.json` が宣言する `auth.type=api_key`, `headerScheme=bearer` の構文は許容されるが、**OpenAI公式のプラグイン接続ポータルはBearerトークン入力UIを現在サポートしない**。プラグインの作成・インストールPASSはMCPの認証接続PASSではない。
- OpenAI公式：https://developers.openai.com/plugins/deploy/submission （Authentication limitations）、https://developers.openai.com/plugins/build/plugins （Fixed bearer tokens and API keys）。
- **訂正**：「プラグイン右側歯車からAPIキーを入力」は誤案内だった。公開/非公開を問わず、ZIPやmanifestのheadersへ秘密値を埋め込んで代用しない。
- 暫定策は**Codexデスクトップの共通MCP一覧 → ＋ サーバーを追加する → Streamable HTTP**、URL=`https://adnc-youtube-private.yosio-hasenaka.workers.dev/mcp`、Bearer Token Environment Variable=`ADNC_YOUTUBE_MCP_KEY` のようなローカル環境変数を設定する。値を直接UIに貼るのではなく**環境変数名**を指定する。Codex公式 `mcp_servers.<id>.bearer_token_env_var` が対応：https://developers.openai.com/docs/config-file/config-reference 。ただし、値の安全な供給方法（毎回非表示入力してプロセスのみに保持／OSの資格情報保管庫）を整備するまでは接続完了扱いしない。
- 本命はWorker MCPへOAuth 2.1認証を実装し、ChatGPTのプラグイン認証画面で接続できる方式へ更新すること。GoogleのOAuth（YouTube/Drive連携）とは別の**MCPクライアントの認証レイヤー**。現行v0.4.4と既存Secretを変更せず別設計・検証後に切替える。
- 現状：PowerShell経由の`initialize`・`check_connection`はPASS。ChatGPT/Codexプラグインからの実ツールはNOT_RUN。動画投稿もNOT_RUN。

### 2026-10-21 Codex CLI MCP list確認

ユーザー実機でCodex Windowsの `codex.exe mcp list` を実行。`adnc-youtube-private` がURL `https://adnc-youtube-private.yosio-hasenaka.workers.dev/mcp`、Bearer Token Env Var `ADNC_YOUTUBE_MCP_KEY`、Status `enabled`、Auth `Bearer token` と表示された。これは **設定認識PASS** だが、Codex内の実MCP呼出しは未検証。

次工程では `Read-Host -AsSecureString` からキーを受け取り、同じPowerShellプロセスで `ADNC_YOUTUBE_MCP_KEY` を一時設定して Codex CLI の `exec --ephemeral --skip-git-repo-check --sandbox read-only` で `check_connection` のみ呼び出し、`finally` で環境変数を消す。キーをコマンド文字列・永続環境変数・GitHub・チャットに埋め込まない。CLI認証PASSとWindowsアプリ認証PASSは区別する。

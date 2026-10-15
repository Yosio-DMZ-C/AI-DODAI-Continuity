# AD&C APIキー・秘密情報の保管と再利用（運用標準 v0.1）

- 制定：2026-10-15
- 対象：プラグイン、外部API、MCP、PowerShell、バッチ、CLI、定期タスク、CI/CD、Worker、他AI連携
- 適用：**APIキーを使用する設計・スクリプトを作るときは、保存方式と利用・更新手順を必ず説明する。** 秘密値自体はAD&CのKB・Git・チャットに保存しない。
- 状態：**運用方針は採用、各利用環境の実動作検査は別ゲート。** この手順書だけでWindows実機・外部サービスの認証が成功したとは扱わない。

## 1. 結論：毎回の手入力は禁止を既定にする

1. **鍵なし認証を優先**：接続先が対応し、実際に利用可能なら公式OAuth接続、短命トークン、OIDC、マネージドID等を優先。新規APIキーの発行を必須にしない。
2. **APIキーが必要なら安全に永続保管**：初回設定またはローテーション時に登録し、通常実行では保管庫／OS暗号化保存先から自動取得する。各回の標準入力、チャット貼付、スクリプト引数入力を要求しない。
3. **保管場所は実行主体ごとに選定**：個人Windows、無人ジョブ、GitHub Actions、Workers、外部プラグインでは認証主体と保管庫が異なる。「環境変数へ永続化すれば安全」としない。
4. **失敗時は停止**：未登録・アクセス拒否・復号失敗・期限切れ・権限不一致では理由と再登録手順を表示し、キーを表示したり毎回の手入力に黙って戻したりしない。
5. **最小権限・分離・追跡**：サービス／用途／環境ごとに別のキーを優先し、読み取り専用・対象限定・有効期限・失効方法を確認する。共用管理者キーを便利さのために使い回さない。

## 2. 実行環境別の既定保存方式

| 実行場所 | 既定の保存先・方式 | 毎回のキー入力 | 適用上の制約 |
|---|---|---|---|
| Windows 11の対話的なPowerShell／同一ユーザーのタスク | **ユーザー別DPAPI暗号化ファイル**。例：`%LOCALAPPDATA%\ADNC\secrets\SERVICE_X_API_KEY.credential.xml` | 不要 | 通常は同一PC・同一Windowsユーザー／プロファイルで復号。保存ファイル自体はGit外・ACL制限 |
| 組織管理PC／高権限／別アカウントでの無人処理 | **承認済みのOS資格情報保管庫・組織Secrets Manager**。適切なサービスIDで取得 | 不要（認証基盤の仕様に従う） | DPAPIの個人ユーザー保存を別ID／別ホストから強引に共有しない |
| PowerShell SecretManagement＋SecretStoreを使える環境 | `Get-Secret`を利用し、適切に設定した拡張Vaultへ保存 | Vaultのロック状態次第 | SecretStore既定はパスワード要求。`Authentication=None`はOSアクセス制御が主となり、高保護環境の既定にしない |
| GitHub Actions | OIDC＋短命資格情報を優先。不可ならGitHub Actions Secrets | 不要 | Workflow権限は最小限。ログの自動マスクは完全ではない |
| Cloudflare Workers | Workers Secrets（`wrangler secret put`、DashboardのSecret） | 不要 | 通常の`vars`、ソース、Wrangler設定に秘密値を置かない |
| ChatGPT／MCP／その他プラグイン | 提供者の公式OAuth／接続設定／秘密情報保管機能 | 通常利用では不要 | プラグインが鍵の保管に対応しない場合は安全な接続方式を再設計し、チャット本文へAPIキーを要求しない |
| macOS／Linuxローカル | OS Keychain・認証済みSecret Service／組織Vault等 | 不要 | Windowsの`Export-Clixml`方式を安全な代替として移植しない |

**保存しない場所**：プログラム本文、`.ps1`／`.bat`、Git履歴、KB／registry、Issue／PR、プロンプト、スクリーンショット、ログ、引数・コマンド履歴、URLクエリ、平文の永続環境変数。`.gitignore`だけに安全性を依存しない。

`.env`／`.dev.vars` は、提供者が認める隔離されたローカル開発で必要な場合の限定例外（Git追跡・同期・添付・配布から除外し、権限を確認）。一般のWindowsスクリプトの既定にはしない。環境変数は子プロセス・ダンプ・ログ等に漏れ得るため、保管庫の代用にはしない。

## 3. Windows／PowerShell：初回1回で登録し、以後自動読込

**推奨対象**：Windows上で利用者自身の権限で実行するPowerShell 5.1/7系の一般的なローカルツール。新たなPowerShellモジュールを必須にせず、Windows DPAPIを使う。

**保存方式**：`PSCredential`を`Export-Clixml`でファイルに保存。Windowsでは資格情報の機密部分が**そのWindowsアカウントを使うDPAPIで暗号化**される。保存先はGit作業ツリー・OneDrive等の同期対象外にあるユーザープロファイル配下。ファイルへのアクセス権（ACL）も確認する。**管理者／同一利用者のマルウェアからキーを完全隔離できる方式ではない。**

### 3.1 初回登録（または明示的な再登録時のみ）

次のコードの`SERVICE_X_API_KEY`を対象サービス固有の非秘密の識別名に置き換える。**本物のキーは表示されずにプロンプトへ入力**する。ChatGPTに貼らない。

~~~powershell
# Windowsで、実際に利用するユーザーとして1回実行
if ($env:OS -ne 'Windows_NT') { throw 'Windows専用のDPAPI登録例です。' }
$name = 'SERVICE_X_API_KEY'
$dir = Join-Path $env:LOCALAPPDATA 'ADNC\secrets'
$path = Join-Path $dir "$name.credential.xml"

New-Item -ItemType Directory -Path $dir -Force | Out-Null
if (Test-Path -LiteralPath $path) {
    throw "登録済みです。上書き・鍵更新は明示的なローテーション手順で行ってください: $path"
}
$secret = Read-Host -Prompt "$name を初回登録" -AsSecureString
[pscredential]::new('apikey', $secret) | Export-Clixml -LiteralPath $path
Remove-Variable secret -ErrorAction SilentlyContinue
Write-Host "秘密値を表示せず登録しました: $path"
~~~

設定後、`icacls "$env:LOCALAPPDATA\ADNC\secrets"`等でACLを確認し、意図しない一般ユーザー／共有グループに読取権限を与えない。必要な権限調整は組織のセキュリティポリシーに従う。

### 3.2 通常実行（入力を求めず読み込む）

以下は**取得方法の例**。実APIへ送る場合は、対象サービスの認証方式・正式なHTTPSエンドポイント・権限を別途確認する。`Write-Host`でキー値を表示しない。

~~~powershell
if ($env:OS -ne 'Windows_NT') { throw 'Windows専用のDPAPI読込例です。' }
$name = 'SERVICE_X_API_KEY'
$path = Join-Path $env:LOCALAPPDATA "ADNC\secrets\$name.credential.xml"
if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    throw "キーが未登録です。初回登録手順を実行してください: $name"
}

$credential = Import-Clixml -LiteralPath $path
if (-not ($credential -is [pscredential])) { throw '資格情報の形式が不正です。' }
$apiKey = $credential.GetNetworkCredential().Password
try {
    # APIに送るときだけ必要最小限の範囲で利用
    $headers = @{ Authorization = "Bearer $apiKey" }
    # 例: Invoke-RestMethod -Uri 'https://api.example.invalid/v1/status' -Headers $headers -Method Get
    Write-Host '暗号化保存済みキーの読込に成功（認証・API接続の成否は別検査）'
}
finally {
    Remove-Variable headers, apiKey, credential -ErrorAction SilentlyContinue
}
~~~

API呼出しの都合でメモリ上に平文文字列が一時的に生じ得る。**通信はHTTPS／適切なヘッダーを使用し、ログ・トレース・例外・ダンプに値が出ないよう検査する。** メモリからの変数削除だけで平文が即時消去される保証はない。

### 3.3 スケジュール・端末移行・キー更新

- **スケジュール実行**：タスクスケジューラ等が**登録時と同じWindowsユーザー**で実行され、当該ユーザープロファイル／DPAPIを利用できることを実機確認する。「SYSTEM」「別サービスアカウント」ではこの個人保存先を共用しない。ログオン形態・資格情報設定によって復号できない場合は別方式を選ぶ。
- **端末／ユーザー変更**：暗号化ファイルだけをコピーして復号できると期待しない。新環境で正規の保管先へ再登録する。移行用の平文キーをKB・チャット・ZIPに入れない。
- **通常ローテーション**：提供元で新キーを発行→明示的な確認のもと保管先を新キーへ更新→新キーで疎通検査→旧キーを失効。漏えい疑いなら**旧キーの失効を最優先**する。更新中の共存可否は提供元に従う。
- **停止・破損**：値の再表示で調査しない。保管ファイルの存在／ACL／ユーザーID／APIから返るステータスのみ検査。復号不可能なら再登録し、ジョブは中断する。

## 4. ツール・プラグイン納品時の必須説明（短い定型）

**APIキーを使うツールを提供するときは、ユーザーへ次の項目を必ず表示する。** 空欄や「環境変数に設定」の一行だけでは納品しない。

| 項目 | 明示する内容 |
|---|---|
| **認証と保存方式** | OAuth／DPAPI／SecretManagement／GitHub Secrets／Workers Secrets等、選定理由 |
| **保存先と実行主体** | 実際のパスまたは保管庫・キー名（**値は書かない**）、利用するOSユーザー／サービスID |
| **初回登録** | 手順・必要権限・一度だけ入力するタイミング・追加インストール要否 |
| **2回目以降の実行** | 手入力不要の自動読込方式。キー欠落時は止まり、通常実行中に再入力を要求しない |
| **定期・無人実行** | 利用するアカウント、ログオン条件、Vault解錠、失敗時の扱い |
| **キーの更新・失効・端末移行** | 保存先更新方法、旧キーの失効、バックアップ／再登録方針 |
| **制約と検査** | 保存暗号化・ログ非表示・疎通試験のPASS／FAIL／NOT_RUN、残るリスク |

**短い案内の例（ユーザーへ表示）**

> 【APIキーの保存】Windowsでは初回だけキーを入力し、`%LOCALAPPDATA%\ADNC\secrets\（サービス名）.credential.xml`へDPAPI暗号化保存します。以降は同一ユーザーのPowerShellが自動読込し、毎回の入力は不要です。未登録・別ユーザー実行時は停止します。端末交換・キー更新時は再登録が必要です。API通信の実動作は別途検証します。

**禁止例**：毎回`Read-Host`させる、`$apiKey = "実キー"`を埋め込む、`-ApiKey "実キー"`のコマンドライン例を利用者へ強制する、永続的なユーザー／マシン環境変数に実キーを入れる、秘密値を標準出力・GitHub Issue・Drive正本・KB・AIチャットに貼る。

ユーザーが既に安全な保管庫を持つ場合、新たな重複保管庫を作らない。保管庫APIを使えるならそれを再利用する。非対応なら使える方式を説明し、無断で別サービスに鍵を移動しない。

## 5. 実装者用・品質ゲート

- **QG-S01 保存**：秘密値をコード・Git・KB・ログ・配布物・Issue・チャットに含めない。実キーで検査する場合も値を表示・転記しない。
- **QG-S02 初回設定**：初回のみ登録でき、既存保存を無断上書きしない。
- **QG-S03 再実行**：登録済みのダミーキーで2回連続実行し、**入力回数0**を確認。DPAPIなら同一ユーザー・同一PCで復号する。
- **QG-S04 異常・権限**：未登録、別ユーザー、破損、失効時に機密情報を漏らさず停止。
- **QG-S05 無人実行**：本当にスケジュール実行する場合、該当実行主体で自動取得できることを別に確認。
- **QG-S06 失効／復旧**：新キーへの移行・旧キー無効化・端末交換時の手順がある。
- **QG-S07 対外API**：鍵の読込成功と実際のAPI認証成功を別判定。API未実行は`NOT_RUN`。

QG-S01〜S06の設計上の静的確認がPASSでも、Windows端末や実サービスで実行していなければ実動作を`PASS`としない。

## 6. 事故対応

1. 漏えいが疑われたら、提供元側で**失効／ローテーションを優先**。
2. そのキーを利用するジョブを必要に応じ停止し、影響を受ける権限・利用記録を確認。
3. チャット・ログ・Git履歴・CI成果物・同期先への露出を調査。単にファイルを削除しただけで無効化済みと見なさない。
4. 新しいキーを適切な保管先へ登録し、最小権限で再開。原因と再発防止策を**鍵の値なし**で記録。

## 7. 根拠（一次資料）

- OWASP Secrets Management Cheat Sheet： https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- OWASP Cryptographic Storage Cheat Sheet： https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
- Microsoft `Export-Clixml`（Windows DPAPI）： https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/export-clixml
- Microsoft `CryptProtectData`（同一ユーザー／端末の制約）： https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata
- Microsoft PowerShell SecretManagement概説： https://learn.microsoft.com/en-us/powershell/utility-modules/secretmanagement/overview
- Microsoft SecretStoreのセキュリティ： https://learn.microsoft.com/en-us/powershell/utility-modules/secretmanagement/security-concepts
- GitHub Actions Secrets： https://docs.github.com/en/actions/reference/security/secrets
- GitHub Actions OIDC： https://docs.github.com/en/actions/concepts/security/openid-connect
- Cloudflare Workers Secrets： https://developers.cloudflare.com/workers/configuration/secrets/

**調査上の境界**：公式仕様から保存手段の成立を説明できるが、個別ユーザーのWindows ACL、タスクスケジューラ、プラグインの設定画面、実サービス認証は実機確認が必要。
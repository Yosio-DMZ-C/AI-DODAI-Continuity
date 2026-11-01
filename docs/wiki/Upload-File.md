# AIへのファイルの送り方（ダウンロード・アップロード）

## まずはQR画像を写真として送る（第一候補）

[![AD&C共通インストーラーQR](../../assets/adnc-installer-qr.png)](https://raw.githubusercontent.com/Yosio-DMZ-C/AI-DODAI-Continuity/main/docs/AgentOS-C_%E8%A8%AD%E8%A8%88%E3%83%BB%E6%A7%8B%E7%AF%89%E9%81%8B%E7%94%A8%E6%8C%87%E7%A4%BA%E6%9B%B8_%E4%B8%80%E8%88%AC%E9%85%8D%E5%B8%83%E7%89%88.md)

1. [QR画像を開いて写真として保存](../../assets/adnc-installer-qr.png)する。
2. Muse、ChatGPTなど使い慣れたAIの写真・画像添付からQR画像を送る。
3. **「これを実行して」** と伝える。AIがQRを読んだだけでなく、[正式な単一インストーラーMarkdown本文](https://raw.githubusercontent.com/Yosio-DMZ-C/AI-DODAI-Continuity/main/docs/AgentOS-C_%E8%A8%AD%E8%A8%88%E3%83%BB%E6%A7%8B%E7%AF%89%E9%81%8B%E7%94%A8%E6%8C%87%E7%A4%BA%E6%9B%B8_%E4%B8%80%E8%88%AC%E9%85%8D%E5%B8%83%E7%89%88.md)を**全文取得して配布版を確認したか**を確かめる。保存先選択 → 本人承認 → 実保存・読戻しを省略しない。

QRの解読とGitHub本文取得は別の機能です。取得先が404だった場合は正式な[リポジトリREADME](../../README.md)から現行版を一度探し直し、**名前の似た別文書を勝手に実行しない**。本文が取得できなければ以下の方法に切り替えます。2026-11-01のMuse試験でリンク取得トラブルの報告があり、このQR経路の独立再現性は未検証です。

## QRが使えない場合：Markdownファイルを添付する

1. [現行の単一AD&Cインストーラー（Markdown）](../AgentOS-C_設計・構築運用指示書_一般配布版.md)を開きます。**旧「AI無課金ユーザー版」は新規導入に使いません**。
2. GitHubの文書画面で［Download raw file］を選んで `.md` を保存します。**HTMLページではなくMarkdown本文**を保存します。
3. AIのチャットで［＋］または［添付］→［ファイル］からそのMarkdownを送り、`実行` と伝えます。添付できない場合のみ本文全文を貼り付けます。

端末の画面・共有メニュー名はOSやAIによって異なります。以下は**QRが使えないときのファイル添付補助**です。

## iPhone

Safariなどで設計書をダウンロードしたら、通常は**「ファイル」アプリ →「ブラウズ」→「ダウンロード」**から探せます。ChatGPTの入力欄にある **［＋］→［ファイル］** から保存した設計書を選びます。

[![iPhoneでChatGPTにファイルを添付する動画](https://img.youtube.com/vi/9IIcpTu4uvM/hqdefault.jpg)](https://www.youtube.com/watch?v=9IIcpTu4uvM)

[動画を見る：mrhackio／iPhoneアプリでの添付（2024年・英語／旧画面）](https://www.youtube.com/watch?v=9IIcpTu4uvM) · [Apple公式：ダウンロードしたファイルの場所](https://support.apple.com/ja-jp/102440)

## Android

ブラウザで設計書を保存したら、通常は**「Files」アプリ →「ダウンロード」**から探せます。ChatGPTの入力欄の **［＋］→［ファイル］** を選び、ファイル選択画面で「ダウンロード」を開きます。

[![AndroidでChatGPTにファイルを添付する動画](https://img.youtube.com/vi/Z-sZ4vxblZM/hqdefault.jpg)](https://www.youtube.com/watch?v=Z-sZ4vxblZM)

[動画を見る：How To Android／Androidでのファイル添付（2026年・英語）](https://www.youtube.com/watch?v=Z-sZ4vxblZM) · [Google公式：Androidでファイルを探す](https://support.google.com/android/answer/9110661?hl=ja)

## Windows PC

ブラウザで設計書を保存し、通常は**「ダウンロード」フォルダー**を開きます。AIのチャットで **［＋］／［添付］→［ファイル］** を選んで保存した設計書を指定します。対応するWeb画面なら、ファイルをチャットの入力欄へドラッグする方法もあります。

[![WindowsのブラウザでChatGPTにファイルを添付する動画](https://img.youtube.com/vi/BYtSLS181oE/hqdefault.jpg)](https://www.youtube.com/watch?v=BYtSLS181oE)

[動画を見る：インプレス「できるChatGPT 改訂2版」／ファイルのアップロード（2026年・日本語）](https://www.youtube.com/watch?v=BYtSLS181oE) · [動画提供元の説明ページ](https://dekiru.net/article/27621/)

## Mac

ブラウザで設計書をダウンロードし、通常はFinderの**「ダウンロード」**から探せます。ChatGPTのWeb画面で **［＋］／［添付］→［ファイル］** を選びます。Mac用アプリの場合は、アプリ内の追加・添付メニューからファイルを選びます。

[![Macを含むPCのChatGPTファイル添付を説明する動画](https://img.youtube.com/vi/nuKgAWabYzA/hqdefault.jpg)](https://www.youtube.com/watch?v=nuKgAWabYzA)

[動画を見る：How To Fix Guide／Macを含む複数端末向け解説（2026年・英語）](https://www.youtube.com/watch?v=nuKgAWabYzA) · [OpenAI公式：macOSの添付メニュー](https://help.openai.com/ja-jp/articles/9295241-chat-bar-%E3%81%AE%E8%B5%B7%E5%8B%95%E6%96%B9%E6%B3%95)

## うまく送れないとき

- **QR画像なら**：写真・画像の送信から選びます。**Markdownファイルなら**：上の端末別説明で「ダウンロード」を確認し、「ファイル」から選びます。
- **`.md` が添付できない**：AIごとの対応形式を確認してください。設計書はテキストなので、必要なら**全文をチャットに貼り付ける**方法に切り替えます。**HTMLページをそのまま添付しない**でください。
- **［＋］や［添付］がない／エラーが出る**：何度も同じ操作を繰り返さず、AIに「ファイルを添付できません。今の画面から次に押す場所を一つ教えてください」と伝えてください。画面を送れるなら[画面の撮り方（動画あり）](https://github.com/Yosio-DMZ-C/AD-C-Shared-Knowledge/blob/main/docs/USER_TO_AI_FEEDBACK_GUIDE.md)も使えます。
- **送った後**：QR画像の受信、URL解読、正式Markdown全文取得は別の確認です。AIに実際に読めたファイル名と版を尋ねてください。HTMLや類似文書での代用を認めず、取得不能ならNOT_RUNとしてファイル添付へ切り替えます。

**送信前の確認**：自分で付け足したパスワード・認証コード・個人情報・会社の機密などが含まれていないことを確認してください。

参考：[OpenAI公式：ファイルアップロード](https://help.openai.com/ja-jp/articles/8555545-uploading-files-and-audio-to-chatgpt)／[OpenAI Academy：ChatGPTでファイルを使う](https://openai.com/ja-JP/academy/working-with-files/)／[GitHub公式：Rawファイルのダウンロード](https://docs.github.com/en/repositories/working-with-files/using-files/viewing-and-understanding-files)

> **検証範囲**：旧ファイル添付ガイドは2026-10-20時点で公開済みですが、端末別動画の全編再生・最新画面・実添付操作は未検証です。**2026-11-01追加のQR画像導線は新たな提案で、QR画像自体の生成・リンク解読と、他AIが本文を取得して導入を完走することは別判定です。** 画像送信・初回保存・別チャット再開の実機試験はNOT_RUN。画面表示が違う場合は利用者の現在の画面を優先してください。

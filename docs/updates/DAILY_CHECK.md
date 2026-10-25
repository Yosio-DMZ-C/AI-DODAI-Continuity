# AD&C｜秘書日々の確認に付随する版チェック（読取専用）

> **日次品質ゲート**：この日に秘書が**実際に起動した初回**だけ実行する。既存の日付別日記に同日の`ADNC_UPDATE_CHECK status=PASS`があれば、GitHubを再照会しない。秘書の予定確認や日記・質問は省略しない。

## 確認と通知

1. KBの`START_HERE.md`から`ADNC_INSTALLER_VERSION`を実取得（不明ならNOT_RUN）。公開の [LATEST.json](LATEST.json) を取得し、`product=AD&C`、`track=installer`、`latest_version` を解析する。KB schema_versionなど別の版と混同しない。
2. X.Y.Zを3整数として比較。**上流のXまたはYが上昇**したときだけ通知候補。Zのみ変更／同じX.Yの差分は秘書から通知しない。ただし利用者が明示的に「アップデートして」と言った場合は[UPDATE.md](UPDATE.md)へ進む。
3. 直近の過去の日付別日記の`ADNC_UPDATE_CHECK`から、**最後に実際に通知したX.Y** (`notified_minor`) を確認する。新しいX.Yを未通知の場合だけ秘書報告の末尾に「AD&Cに更新があります（現行版→最新版）。内容を確認しますか？」と一文添える。**同じX.Yを翌日も再通知しない**。通知済み値が追跡不能なら重複排除未確認とし、確実と断言しない。
4. 比較できた場合、すでに承認済みの**当日日記**へ短いメタ行`<!-- ADNC_UPDATE_CHECK day=YYYY-MM-DD status=PASS installed=X.Y.Z latest=X.Y.Z notified_minor=X.Y|none -->`を**同日1件だけ**保存・読戻し。実通知がない日は前回`notified_minor`を維持。**保存できない場合は読取PASSと記録保存NOT_RUNを分ける。** 同じチャット内の可視記録だけでは日を跨ぐ厳密な1日1回や重複通知防止を保証しない。
5. 更新のダウンロード、既存KBのアップデート、公開、権限変更、送信、GitHubのIssue/PR/CI巡回は**一切実行しない**。通知のために新たなスケジュールやDBを作らない。

実行不能な場合は取得不能・履歴未取得・保存不能の別を保持し、必要なら一言だけ知らせる。秘書の本来の仕事をこの版チェックで妨げない。

#!/usr/bin/env python3
"""Rebuild Issue #13's current-state block from approved structured issue comments.

No database: the comments are the append-only events; the Issue body is a view.
Does not touch Drive, releases, pull requests, or task decisions.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ISSUE_NO = 13
MARKER = "ADNC-STATE-V1"
BEGIN = "<!-- ADNC-CURRENT-STATE-BEGIN -->"
END = "<!-- ADNC-CURRENT-STATE-END -->"
OPEN_BEGIN = "<!-- ADNC-OPEN-WORK-BEGIN -->"
OPEN_END = "<!-- ADNC-OPEN-WORK-END -->"
TASK_HEADER = "## 今のタスク表"
# DONE requires actual task completion; a PR merge/close or design adoption alone cannot close larger work.
TERMINAL = {"DONE", "DROPPED"}
TASK_ID = re.compile(r"^ADNC-T[0-9]{3,}$")

KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{2,48}$")
STATES = {"PASS", "FAIL", "NOT_RUN", "IN_PROGRESS", "BLOCKED", "DONE"}
BASES = {
    "MUSE_REPORT": "Muse実行報告",
    "USER_REPORT": "利用者報告",
    "LEADER_REVIEW": "リーダー検査報告",
}
NAMES = {
    "MUSE-NEW-INSTALL-1310": "Muse B：v1.3.10新規導入・保存・同一ID更新",
    "MUSE-SINGLECHAT-STRESS-02": "Muse B：単一チャット知識品質試験v0.2",
    "MUSE-EXISTING-KB": "Muse A：既存個人KB利用（別環境）",
    "MUSE-A-LEGACY-ADOPTION": "Muse A：旧KB互換導入（独立読戻し）",
    "MUSE-A-SECRETARY-HOOK": "Muse A：既存秘書への更新確認接続",
    "MUSE-A-DAILY-CHECK": "Muse A：秘書の日次バージョン確認",
    "MUSE-B-152-UPGRADE": "Muse B：共通版への差分更新・読戻し試験",
    "T002-UNIFIED-RELEASE": "T002：現行共通ガイド配布・旧無料版保全",
    "MUSE-CROSS-AI-TRANSFER": "Muse B：別AIへの受渡し",
    "T014-FORMAL-SCHEMA": "T014：正式JSON Schema検査",
    "T014-CONCURRENT-UPDATE": "T014：実同時更新検査",
    "PR31-REAL-AI-RESTORE": "PR #31：実AIによる復元",
    "ARCH-2026-IMPLEMENTATION": "2026暫定設計：採用事項の実装照合",
    "KB-PROBE-BETA-CI": "KB整合検査器：読取専用βと合成CI",
    "WORK-RESUME-BETA-CI": "作業復元プリフライト：βコードと合成CI",
    "INSTALLER-153-RELEASE": "共通インストーラー1.5.3：配布・実ダウンロード",
    "TASK-PERSISTENCE-DISPLAY": "未完了タスク表示：Issue自動同期・読戻し",
    "TASK-HANDOFF-RECEIPT": "中断タスク引継ぎ：秘書・別AIの実受信",
    "RUNBOOK-ASSET-RULE": "Runbook素材・画像・ツールの単一入口（規則保存）",
    "RUNBOOK-ASSET-COLDSTART": "Runbook素材の独立Q2/Q3実検査",
}


def parse_comment(comment):
    """Accept only owner's short JSON event, never arbitrary prose or instructions."""
    body = comment.get("body") or ""
    if comment.get("user", {}).get("login") != OWNER or len(body) > 4000:
        return []
    lines = body.strip().splitlines()
    if not lines or lines[0] != MARKER:
        return []
    try:
        event = json.loads("\n".join(lines[1:]))
        updates = event["updates"]
        if not isinstance(updates, list) or not 1 <= len(updates) <= 12:
            return []
        result = []
        for item in updates:
            if not isinstance(item, dict) or set(item) != {"key", "state", "basis"}:
                return []
            key, state, basis = item["key"], item["state"], item["basis"]
            if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key):
                return []
            if state not in STATES or basis not in BASES:
                return []
            result.append((key, state, basis))
        return result
    except (ValueError, TypeError, KeyError):
        return []


def latest_states(comments):
    latest = {}
    for comment in sorted(comments, key=lambda c: (c.get("created_at", ""), c.get("id", 0))):
        for key, state, basis in parse_comment(comment):
            latest[key] = {
                "state": state,
                "basis": basis,
                "url": comment["html_url"],
                "created_at": comment["created_at"],
            }
    return latest


def render_block(states):
    out = [
        BEGIN,
        "## 最新状態（Issueコメントから自動同期）",
        "",
        "> ここが該当試験の現行判定です。以下の古い本文・コメント中のNOT_RUNは履歴として残ります。",
        "> PASSは根拠欄の報告主体による判定であり、独立検証済みと自動的にはみなしません。",
        "> 異なるMuse環境・別AI試験・Foundation全体の完了は混同しません。",
        "",
        "| 対象 | 現行判定 | 判定根拠 | 報告日時（JST）・記録 |",
        "|---|---|---|---|",
    ]
    for key, row in sorted(states.items()):
        instant = dt.datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        when = instant.astimezone(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")
        name = NAMES.get(key, key)
        # All variable fields above are enum values or trusted GitHub API metadata.
        out.append(
            f"| {name} | **{row['state']}** | {BASES[row['basis']]} | "
            f"[{when}]({row['url']}) |"
        )
    out.extend(["", "更新方法：Issue #13に先頭行 ADNC-STATE-V1 と公開可能なJSONをコメント投稿。"
                "この表だけを更新し、履歴・作業正本・PR・Driveには触れません。",
                END])
    return "\n".join(out)


def replace_block(body, states):
    new = render_block(states)
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
    if pattern.search(body):
        return pattern.sub(lambda _: new, body, count=1)
    first_line, sep, rest = body.partition("\n")
    return first_line + "\n\n" + new + "\n" + (rest if sep else "")


def pending_tasks(body):
    """Derive open items from the existing Issue #13 task table; never infer new tasks."""
    section = body.find(TASK_HEADER)
    if section < 0:
        raise RuntimeError("Issue task list missing; refuse to publish empty open queue")
    rows = []
    began = False
    ids = set()
    for line in body[section:].splitlines()[1:]:
        if line.startswith("## "):
            break
        if not line.startswith("|"):
            if began and rows:
                break
            continue
        fields = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(fields) != 6:
            continue
        if fields[0] == "ID" or fields[0].startswith("---"):
            began = True
            continue
        if not TASK_ID.fullmatch(fields[0]):
            continue
        began = True
        if fields[0] in ids:
            raise RuntimeError("Duplicate task ID in Issue; refusing an ambiguous current state")
        ids.add(fields[0])
        status = re.match(r"([A-Z_]+)", fields[4])
        state = status.group(1) if status else "UNKNOWN"
        if state not in TERMINAL:
            rows.append((fields[0], fields[1], fields[2], fields[3], state))
    if not began or not ids:
        raise RuntimeError("No parseable task entries; refusing empty success")
    return rows


def render_pending_block(body):
    pending = pending_tasks(body)
    out = [OPEN_BEGIN, "## 未完了・要追跡（自動抽出）", "",
           "> **DONEまたは理由付きDROPPEDになるまで追跡フラグが残ります。**",
           "> BLOCKED・REVIEW_PENDING・WAITING・PROPOSEDも隠しません。",
           "> これは既存タスク表の表示用派生物。根拠・担当・完了判定は下の各タスク行が正本。",
           "> PRのClosed/Mergedや部分PASSをタスク全体のDONEに自動変換しません。",
           "",
           f"**未完了：{len(pending)} 件**", "",
           "| ID | 優先 | 現在状態 | 担当 | 続ける仕事（タスク表参照） |",
           "|---|---|---|---|---|"]
    for ident, priority, next_work, assignee, status in pending:
        brief = re.sub(r"\s+", " ", next_work).replace("|", "／")
        # Task text comes from the existing public issue; truncate, don't duplicate private metadata.
        if len(brief) > 85:
            brief = brief[:82] + "…"
        brief_owner = re.sub(r"\s+", " ", assignee).replace("|", "／")
        if len(brief_owner) > 48:
            brief_owner = brief_owner[:45] + "…"
        out.append(f"| {ident} | {priority} | **{status}** | {brief_owner} | {brief} |")
    out.extend(["",
                "**再開の入口**：下のタスク表の対象ID→既存PR/Issue/BUILD_PLANの現行状態→最終実取得→次の1工程。",
                "資料・接続が欠ける場合はNOT_RUNのまま保全。作業が途中終了したら担当・失敗箇所・次の一手を対象行へ書き戻す。",
                OPEN_END])
    return "\n".join(out)


def replace_pending_block(body):
    new = render_pending_block(body)
    pattern = re.compile(re.escape(OPEN_BEGIN) + r".*?" + re.escape(OPEN_END), re.S)
    if pattern.search(body):
        return pattern.sub(lambda _: new, body, count=1)
    first_line, sep, rest = body.partition("\n")
    return first_line + "\n\n" + new + "\n\n" + (rest if sep else "")


def request(path, method="GET", data=None):
    base = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    url = base + path
    headers = {
        "Authorization": "Bearer " + os.environ["GH_TOKEN"],
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "adnc-issue13-state-sync",
    }
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
    if payload is not None:
        headers["Content-Type"] = "application/json"
    with urllib.request.urlopen(
        urllib.request.Request(url, data=payload, headers=headers, method=method), timeout=25
    ) as resp:
        return json.loads(resp.read().decode("utf-8")), resp.headers


def fetch_comments(repo):
    # Fetch every page, not only the newest 100: no stale/partial reconstructions.
    comments = []
    for page in range(1, 21):
        path = f"/repos/{repo}/issues/{ISSUE_NO}/comments?per_page=100&page={page}"
        batch, _ = request(path)
        comments.extend(batch)
        if len(batch) < 100:
            return comments
    raise RuntimeError("Comment pagination exceeded 2000; refusing incomplete update")


def self_test():
    global OWNER
    OWNER = "Yosio-DMZ-C"
    c = lambda ident, updates: {
        "id": ident, "created_at": "2026-10-25T00:00:00Z",
        "user": {"login": OWNER}, "html_url": f"https://github.com/example/issues/13#issuecomment-{ident}",
        "body": MARKER + "\n" + json.dumps({"updates": updates}),
    }
    events = [
        c(1, [{"key": "MUSE-NEW-INSTALL-1310", "state": "NOT_RUN", "basis": "USER_REPORT"}]),
        c(2, [{"key": "MUSE-NEW-INSTALL-1310", "state": "PASS", "basis": "MUSE_REPORT"}]),
        c(3, [{"key": "T014-FORMAL-SCHEMA", "state": "NOT_RUN", "basis": "LEADER_REVIEW"}]),
    ]
    state = latest_states(events)
    assert state["MUSE-NEW-INSTALL-1310"]["state"] == "PASS"
    assert state["T014-FORMAL-SCHEMA"]["state"] == "NOT_RUN"
    text = "# Issue\n\nExisting content\n"
    updated = replace_block(text, state)
    assert "Existing content" in updated and updated.count(BEGIN) == 1
    assert replace_block(updated, state) == updated
    invalid = c(4, [{"key": "INVALID|TABLE", "state": "PASS", "basis": "USER_REPORT"}])
    assert not parse_comment(invalid)
    impostor = c(5, [{"key": "MUSE-NEW-INSTALL-1310", "state": "FAIL", "basis": "MUSE_REPORT"}])
    impostor["user"]["login"] = "other"
    assert not parse_comment(impostor)
    synthetic = ("# Test\n\n## 今のタスク表\n\n"
                 "| ID | 優先 | 次にすること | 担当チャット | 状態 | 依存・根拠 |\n"
                 "|---|---|---|---|---|---|\n"
                 "| ADNC-T001 | P0 | 仕様案の実装 | AI | DONE（実体確認済） | evidence |\n"
                 "| ADNC-T002 | P0 | PR失敗後の復旧 | AI | BLOCKED（CI異常） | PR |\n"
                 "| ADNC-T003 | P1 | レビュー待ち | AI | REVIEW_PENDING | source |\n"
                 "| ADNC-T004 | P2 | 却下済み | AI | DROPPED（承認済） | source |\n")
    pending = pending_tasks(synthetic)
    assert [x[0] for x in pending] == ["ADNC-T002", "ADNC-T003"]
    highlighted = replace_pending_block(synthetic)
    assert "未完了：2 件" in highlighted
    assert replace_pending_block(highlighted) == highlighted
    assert "ADNC-T001 |" not in highlighted.split(OPEN_END)[0]
    try:
        pending_tasks("# No task list")
        raise AssertionError("Missing task list must not be silently successful")
    except RuntimeError:
        pass
    print("SELF_TEST_PASS: latest-wins, idempotent, authenticated events, pending-work flags, refusal on missing list")


def main():
    global OWNER
    if "--self-test" in sys.argv:
        self_test()
        return
    repo = os.environ["GITHUB_REPOSITORY"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise RuntimeError("Invalid repository")
    OWNER = repo.partition("/")[0]
    comments = fetch_comments(repo)
    state = latest_states(comments)
    if not state:
        print("No approved status events; nothing to change")
        return
    issue, _ = request(f"/repos/{repo}/issues/{ISSUE_NO}")
    before = issue["body"] or ""
    after = replace_pending_block(replace_block(before, state))
    if after == before:
        print(f"NO_CHANGE: {len(state)} current states")
        return
    # Narrow the stale-read window: an Issue edit may add a task while
    # a previous sync is running. Never patch the original stale body.
    # GitHub Issues REST PATCH is not an atomic compare-and-swap; races
    # after this final read still require post-write monitoring.
    latest_issue, _ = request(f"/repos/{repo}/issues/{ISSUE_NO}")
    if latest_issue.get("body", "") != before:
        before = latest_issue.get("body") or ""
        after = replace_pending_block(replace_block(before, state))
        print("REFRESHED: issue body changed during synchronization")
    if after == before:
        print(f"NO_CHANGE: {len(state)} current states after refresh")
        return
    request(f"/repos/{repo}/issues/{ISSUE_NO}", method="PATCH", data={"body": after})
    readback, _ = request(f"/repos/{repo}/issues/{ISSUE_NO}")
    if readback.get("body") != after:
        raise RuntimeError("Issue readback mismatch")
    print(f"UPDATED_PASS: {len(state)} current states; issue readback matched")


if __name__ == "__main__":
    main()

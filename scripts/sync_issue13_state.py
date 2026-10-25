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
    print("SELF_TEST_PASS: latest-wins, distinct scopes, unchanged body, idempotent, reject invalid")


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
    after = replace_block(before, state)
    if after == before:
        print(f"NO_CHANGE: {len(state)} current states")
        return
    request(f"/repos/{repo}/issues/{ISSUE_NO}", method="PATCH", data={"body": after})
    readback, _ = request(f"/repos/{repo}/issues/{ISSUE_NO}")
    if readback.get("body") != after:
        raise RuntimeError("Issue readback mismatch")
    print(f"UPDATED_PASS: {len(state)} current states; issue readback matched")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""CI 门禁退出码三分（W2b）。

退出码：
  0 = 扫描完整，且无漏洞达到 --fail-on-severity
  1 = 扫描完整，但存在达到阈值的漏洞
  2 = 扫描不完整（核心能力降级/失败）或读取/用法错误

"不完整"的核心集（2026-10-21 拍板）：hunt / validate / reduce。
另外把 budget=degraded/failed 视为完整性信号（预算超限 = 部分成果保留）。
plan 与 optional/aux 能力不参与退出码，只作为报告/SARIF 属性。

用法：
  cd backend && python scripts/sec_gate.py --result data/audit_history/<task>.json
  cd backend && python scripts/sec_gate.py --result <task_id> --fail-on-severity high
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from agentic.layerb.priority import normalize_severity  # noqa: E402

CORE_CAPABILITIES = ("hunt", "validate", "reduce")
COMPLETENESS_CAPABILITIES = ("budget",)
_SEV_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
_BAD = frozenset({"degraded", "failed"})
_SEV_CHOICES = ("critical", "high", "medium", "low", "info")
# 显式关闭/无候选的 skipped 是配置选择，不是结果不完整（L0 纯静态基线实测 47 场）
_INTENTIONAL_SKIP_TOKENS = ("未启用", "无候选", "disabled", "mode=off",
                            "hunt_enabled=0", "no candidates")


def _cap(caps: dict, name: str) -> dict | None:
    rec = caps.get(name)
    return rec if isinstance(rec, dict) else None


def _intentional_skip(rec: dict) -> bool:
    err = str(rec.get("error") or "").strip().lower()
    return any(token in err for token in _INTENTIONAL_SKIP_TOKENS)


def _incomplete(caps: dict) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    warnings: list[str] = []
    if not caps:
        return ["capabilities=missing"], warnings
    for name in CORE_CAPABILITIES:
        rec = _cap(caps, name)
        if rec is None:
            # 历史场次可能没有该键；只提示，不回溯判不完整
            warnings.append(f"{name}=missing")
            continue
        status = str(rec.get("status") or "").lower()
        if status in _BAD:
            reasons.append(f"{name}={status}")
        elif status == "skipped":
            if _intentional_skip(rec):
                continue
            if rec.get("enabled", True) and not rec.get("executed", False):
                reasons.append(f"{name}=skipped(enabled)")
    for name in COMPLETENESS_CAPABILITIES:
        rec = _cap(caps, name)
        if rec is not None and str(rec.get("status") or "").lower() in _BAD:
            reasons.append(f"{name}={rec.get('status')}")
    return reasons, warnings


def _findings(result: dict) -> list[dict]:
    src = result.get("findings")
    if not isinstance(src, list):
        sd = result.get("scan_details") or {}
        src = sd.get("reduced") or sd.get("findings")
    return [f for f in (src or []) if isinstance(f, dict)]


def _over_threshold(findings: list[dict], threshold: str) -> int:
    rank = _SEV_RANK.get(normalize_severity(threshold), 1)
    hits = 0
    for f in findings:
        sev = normalize_severity(f.get("severity"))
        if sev and _SEV_RANK.get(sev, 99) <= rank:
            hits += 1
    return hits


def evaluate(result: dict, *, fail_on_severity: str = "high",
             max_cost: float | None = None) -> dict:
    """返回退出码与判据明细；不写文件、不改 result。"""
    caps = (result or {}).get("capabilities") or {}
    reasons, warnings = _incomplete(caps)
    hits = _over_threshold(_findings(result or {}), fail_on_severity)
    code = 2 if reasons else (1 if hits else 0)
    return {
        "exit_code": code,
        "incomplete": reasons,
        "warnings": warnings,
        "findings_over_threshold": hits,
        "fail_on_severity": fail_on_severity,
        "max_cost_ignored": max_cost is not None,
    }


def decide_exit_code(result: dict, *, fail_on_severity: str = "high",
                     max_cost: float | None = None) -> int:
    return evaluate(result, fail_on_severity=fail_on_severity,
                    max_cost=max_cost)["exit_code"]


def _load(path_or_id: str) -> dict:
    if os.path.isfile(path_or_id):
        with open(path_or_id, encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        from agentic.audit_history import get_audit_record  # 仅 task_id 档需要
        record = get_audit_record(path_or_id)
        if not record:
            raise FileNotFoundError(f"未找到结果文件或历史记录: {path_or_id}")
        data = record
    if isinstance(data, dict) and isinstance(data.get("result"), dict):
        return data["result"]
    return data


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--result", required=True,
                        help="结果 JSON 路径，或历史 task_id")
    parser.add_argument("--fail-on-severity", default="high",
                        choices=_SEV_CHOICES,
                        help="命中该档及以上的漏洞返回 1（默认 high）")
    parser.add_argument("--max-cost", type=float, default=None,
                        help="本期未实现：传入会警告并忽略")
    args = parser.parse_args(argv)

    if args.max_cost is not None:
        print("--max-cost 本期未实现，已忽略", file=sys.stderr)
    try:
        result = _load(args.result)
    except Exception as e:
        print(f"读取结果失败: {e}", file=sys.stderr)
        return 2

    details = evaluate(result, fail_on_severity=args.fail_on_severity,
                       max_cost=args.max_cost)
    for warning in details["warnings"]:
        print(f"warning: {warning}", file=sys.stderr)
    print(json.dumps(details, ensure_ascii=False))
    return details["exit_code"]


if __name__ == "__main__":
    sys.exit(main())

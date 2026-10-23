"""层 B 前提 · 优先级门禁（P1 定义契约）

**问题**：层 B 触发条件要求「P1 高危」，但 finding 的 `severity` 存在**两套词汇**：
LLM prompt / 静态规则产出小写 `high/medium/low`（见 prompts/defaults.py、static_rules.py），
报告侧阶梯却是大写 `CRITICAL>HIGH>MEDIUM>LOW`（见 report.py `_SEV_ORDER`）。不归一，
"P1"判据必然失真。仓库中既无独立 P0/P1 词汇（`priority` 皆指预算/分片策略），
亦无 attack_chains 专属优先级——故 P1 须在此**显式定契约**。

**契约（2026-10-06 定）**：
  · 归一：去空白 + 转大写，并把常见别名折入四档（见 `_ALIASES`）；
  · **P1 := 归一后 ∈ {CRITICAL, HIGH}**（实测多数命中 `high`）；
  · 缺 severity / 无法识别 → 归空 → **不算 P1**（保守：无据不入选，绝不误当高危）。
  · 本模块**只管 severity**；与 status（CONFIRMED/PENDING）的组合由层 B 闸门自行叠加。
"""
from __future__ import annotations

from typing import Any, Mapping

# P1 = 高危两档（与 report.py _SEV_ORDER 前两档一致）
P1_LEVELS = frozenset({"CRITICAL", "HIGH"})

# 归一后的合法档位
_LEVELS = frozenset({"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"})

# 常见别名 → 四档（兼容 LLM/静态规则/外部引擎的不同措辞）
_ALIASES = {
    "CRIT": "CRITICAL", "SEVERE": "CRITICAL", "BLOCKER": "CRITICAL",
    "MODERATE": "MEDIUM", "WARNING": "MEDIUM", "WARN": "MEDIUM", "MED": "MEDIUM",
    "MINOR": "LOW",
    "INFORMATIONAL": "INFO", "NOTE": "INFO", "NONE": "INFO",
}


def normalize_severity(value: Any) -> str:
    """severity 归一为大写档位；缺失/无法识别返回空串（不猜）。"""
    s = str(value or "").strip().upper()
    if not s:
        return ""
    s = _ALIASES.get(s, s)
    return s if s in _LEVELS else ""


def severity_of(item: Any) -> str:
    """从 finding/候选 dict 取 severity 并归一；非 dict 时按原值归一。"""
    if isinstance(item, Mapping):
        return normalize_severity(item.get("severity"))
    return normalize_severity(item)


def is_p1(item: Any) -> bool:
    """是否 P1 高危（severity 归一后 ∈ {CRITICAL, HIGH}）。

    入参可为候选 dict（读 `severity`）或裸 severity 值。缺据一律 False。
    """
    return severity_of(item) in P1_LEVELS
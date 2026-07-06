"""统一错误输出 schema,给 /lychee-workflow 组合链路用。"""

from typing import Any, Dict, Optional


def format_error(
    exc: BaseException,
    *,
    step: Optional[str] = None,
    hint: Optional[str] = None,
) -> Dict[str, Any]:
    """把异常转成统一的失败响应 dict。

    Args:
        exc: 异常对象
        step: 当前步骤名,如 "submit" / "poll" / "download",给 /lychee-workflow 用
        hint: 给用户的恢复建议,如 "检查 LYCHEE_API_KEY 是否设置"
    """
    payload: Dict[str, Any] = {"success": False, "error": str(exc)}
    if step is not None:
        payload["step"] = step
    if hint is not None:
        payload["hint"] = hint
    return payload

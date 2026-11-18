from datetime import date, timedelta


def initial_anchor(cycle: str, start: date, renewal: date | None, anchor: int | None = None) -> int | None:
    if cycle not in ("month", "year"):
        return None
    if anchor is not None and (not isinstance(anchor, int) or isinstance(anchor, bool) or not 1 <= anchor <= 31):
        raise ValueError("锚定日必须为 1–31")
    return anchor if anchor is not None else (renewal or start).day


def add_cycle(d: date, cycle: str, count: int, anchor_day: int | None = None) -> date:
    """在日期 d 上加 count 个 cycle 周期。"""
    count = max(1, count)
    if cycle == "day":
        return d + timedelta(days=count)
    if cycle == "week":
        return d + timedelta(weeks=count)
    if cycle == "month":
        return _add_months(d, count, anchor_day)
    if cycle == "year":
        return _add_months(d, count * 12, anchor_day)
    return _add_months(d, count, anchor_day)  # 默认按月


def _add_months(d: date, months: int, anchor_day: int | None = None) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    # 处理月末（如 1/31 + 1 月 -> 2/28）
    day = min(anchor_day or d.day, _days_in_month(year, month))
    return date(year, month, day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        nxt = date(year + 1, 1, 1)
    else:
        nxt = date(year, month + 1, 1)
    return (nxt - date(year, month, 1)).days


def compute_next_renewal(start: date, cycle: str, count: int, today: date | None = None, anchor_day: int | None = None) -> date:
    """从 start 起按周期推进，返回今天之后（含今天）的下一个续费日。"""
    today = today or date.today()
    nxt = start
    guard = 0
    while nxt < today and guard < 1000:
        nxt = add_cycle(nxt, cycle, count, anchor_day)
        guard += 1
    return nxt

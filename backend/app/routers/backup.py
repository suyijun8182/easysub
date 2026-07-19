"""数据备份与恢复：导出/导入数据。

应对场景：重新部署后数据丢失。用户可随时把自己的订阅及自定义分类/付款方式/
捆绑包/货币导出为一个 JSON 文件离线保存，重装后再导入恢复。
普通用户只能导出/导入自己的数据；管理员还可整站备份/恢复全部成员的数据。
"""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import activity
from app.billing import compute_next_renewal
from app.database import get_db
from app.deps import get_admin_user, get_current_user
from app.models import Bundle, Category, Currency, PaymentMethod, Subscription, User
from app.security import hash_password
from app.services import notify

router = APIRouter(prefix="/api/backup", tags=["backup"])

EXPORT_VERSION = 1


def _sub_dict(s: Subscription) -> dict:
    return {
        "name": s.name,
        "plan": s.plan,
        "icon": s.icon,
        "url": s.url,
        "notes": s.notes,
        "remark": s.remark,
        "ipv4": s.ipv4,
        "ipv6": s.ipv6,
        "category_id": s.category_id,
        "payment_method_id": s.payment_method_id,
        "bundle_id": s.bundle_id,
        "amount": s.amount,
        "currency": s.currency,
        "billing_type": s.billing_type,
        "cycle": s.cycle,
        "cycle_count": s.cycle_count,
        "start_date": s.start_date.isoformat() if s.start_date else None,
        "next_renewal_date": s.next_renewal_date.isoformat() if s.next_renewal_date else None,
        "end_date": s.end_date.isoformat() if s.end_date else None,
        "last_renewed_at": s.last_renewed_at.isoformat() if s.last_renewed_at else None,
        "is_active": s.is_active,
        "auto_renew": s.auto_renew,
        "show_in_calendar": s.show_in_calendar,
        "sort": s.sort,
        "family_members": s.family_members,
        "remind_days_before": s.remind_days_before,
    }


def _collect_entities(db: Session, user: User) -> dict:
    """汇总某用户的订阅及其依赖实体（分类/付款方式/捆绑包/自定义货币）。

    关键修复：订阅可能挂在「系统预置分类」（is_system=True, user_id=None）下，
    旧逻辑只导出 user_id == 当前用户 的分类，导致这些订阅在恢复时分类丢失。
    这里额外把订阅实际引用到的分类/付款方式（含系统预置的）一并导出，
    恢复端按名称匹配即可正确还原到重新种子化后的系统分类上。
    """
    subs = db.scalars(select(Subscription).where(Subscription.user_id == user.id)).all()
    used_cat_ids = {s.category_id for s in subs if s.category_id}
    used_pm_ids = {s.payment_method_id for s in subs if s.payment_method_id}

    cats = db.scalars(
        select(Category).where(
            or_(Category.user_id == user.id, Category.id.in_(used_cat_ids))
        )
    ).all()
    pms = db.scalars(
        select(PaymentMethod).where(
            or_(PaymentMethod.user_id == user.id, PaymentMethod.id.in_(used_pm_ids))
        )
    ).all()
    bundles = db.scalars(select(Bundle).where(Bundle.user_id == user.id)).all()
    currencies = db.scalars(
        select(Currency).where(Currency.is_custom.is_(True), Currency.user_id == user.id)
    ).all()

    return {
        "categories": [
            {
                "id": c.id, "name": c.name, "icon": c.icon, "color": c.color,
                "sort": c.sort, "is_system": c.is_system,
            }
            for c in cats
        ],
        "payment_methods": [
            {"id": p.id, "name": p.name, "icon": p.icon, "is_system": p.is_system}
            for p in pms
        ],
        "bundles": [{"id": b.id, "name": b.name, "note": b.note} for b in bundles],
        "currencies": [
            {"code": c.code, "name": c.name, "symbol": c.symbol} for c in currencies
        ],
        "subscriptions": [_sub_dict(s) for s in subs],
    }


def _parse_date(v):
    try:
        return date.fromisoformat(v) if v else None
    except (TypeError, ValueError):
        return None


def _restore_entities(db: Session, user: User, data: dict, replace: bool) -> int:
    """把一份导出数据恢复到指定用户名下，返回导入的订阅数（不提交事务）。

    自定义分类/付款方式/捆绑包按名称匹配现有实体（含系统预置），缺失才新建。
    """
    subs_in = data.get("subscriptions") or []

    if replace:
        for s in db.scalars(
            select(Subscription).where(Subscription.user_id == user.id)
        ).all():
            db.delete(s)
        db.flush()

    # 现有可用实体（当前用户的 + 系统预置的），按名称去重，避免重复创建
    existing_cats = {
        c.name: c
        for c in db.scalars(
            select(Category).where(
                or_(Category.user_id == user.id, Category.is_system.is_(True))
            )
        ).all()
    }
    existing_pms = {
        p.name: p
        for p in db.scalars(
            select(PaymentMethod).where(
                or_(PaymentMethod.user_id == user.id, PaymentMethod.is_system.is_(True))
            )
        ).all()
    }
    existing_bundles = {
        b.name: b
        for b in db.scalars(select(Bundle).where(Bundle.user_id == user.id)).all()
    }

    cat_map: dict[int, int] = {}
    pm_map: dict[int, int] = {}
    bundle_map: dict[int, int] = {}

    for c in data.get("categories", []) or []:
        name = c.get("name")
        if not name:
            continue
        target = existing_cats.get(name)
        if not target:
            target = Category(
                name=name, icon=c.get("icon"), color=c.get("color"),
                sort=c.get("sort", 0), user_id=user.id, is_system=False,
            )
            db.add(target)
            db.flush()
            existing_cats[name] = target
        if c.get("id") is not None:
            cat_map[c["id"]] = target.id

    for p in data.get("payment_methods", []) or []:
        name = p.get("name")
        if not name:
            continue
        target = existing_pms.get(name)
        if not target:
            target = PaymentMethod(name=name, icon=p.get("icon"), user_id=user.id, is_system=False)
            db.add(target)
            db.flush()
            existing_pms[name] = target
        if p.get("id") is not None:
            pm_map[p["id"]] = target.id

    for b in data.get("bundles", []) or []:
        name = b.get("name")
        if not name:
            continue
        target = existing_bundles.get(name)
        if not target:
            target = Bundle(name=name, note=b.get("note"), user_id=user.id)
            db.add(target)
            db.flush()
            existing_bundles[name] = target
        if b.get("id") is not None:
            bundle_map[b["id"]] = target.id

    for cu in data.get("currencies", []) or []:
        code = (cu.get("code") or "").upper()
        if code and not db.get(Currency, code):
            db.add(
                Currency(
                    code=code, name=cu.get("name", code), symbol=cu.get("symbol", ""),
                    is_custom=True, user_id=user.id,
                )
            )
    db.flush()

    count = 0
    for s in subs_in:
        start = _parse_date(s.get("start_date")) or date.today()
        billing_type = s.get("billing_type", "recurring")
        sub = Subscription(
            user_id=user.id,
            name=s.get("name") or "导入订阅",
            plan=s.get("plan"),
            icon=s.get("icon"),
            url=s.get("url"),
            notes=s.get("notes"),
            remark=s.get("remark"),
            ipv4=s.get("ipv4"),
            ipv6=s.get("ipv6"),
            category_id=cat_map.get(s.get("category_id")),
            payment_method_id=pm_map.get(s.get("payment_method_id")),
            bundle_id=bundle_map.get(s.get("bundle_id")),
            amount=s.get("amount", 0.0) or 0.0,
            currency=s.get("currency") or user.base_currency,
            billing_type=billing_type,
            cycle=s.get("cycle", "month"),
            cycle_count=s.get("cycle_count", 1) or 1,
            start_date=start,
            next_renewal_date=_parse_date(s.get("next_renewal_date")),
            end_date=_parse_date(s.get("end_date")),
            last_renewed_at=_parse_date(s.get("last_renewed_at")),
            is_active=s.get("is_active", True),
            auto_renew=s.get("auto_renew", True),
            show_in_calendar=s.get("show_in_calendar", True),
            sort=s.get("sort", 0) or 0,
            family_members=s.get("family_members"),
            remind_days_before=s.get("remind_days_before", "7,6,5,4,3,2,1") or "7,6,5,4,3,2,1",
        )
        if billing_type == "recurring" and not sub.next_renewal_date:
            sub.next_renewal_date = compute_next_renewal(start, sub.cycle, sub.cycle_count)
        if billing_type == "one_time":
            sub.next_renewal_date = None
        db.add(sub)
        count += 1

    return count


# --------------------------------------------------------------------------- #
# 单用户：导出 / 导入自己的数据
# --------------------------------------------------------------------------- #
@router.get("/export")
def export_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """导出当前用户的全部数据为 JSON。"""
    return {
        "export_version": EXPORT_VERSION,
        "app": "EasySub",
        "exported_at": datetime.utcnow().isoformat(timespec="seconds"),
        "user": {
            "username": user.username,
            "base_currency": user.base_currency,
            "locale": user.locale,
            "theme": user.theme,
            "notify_config": notify.load_config(user),
        },
        **_collect_entities(db, user),
    }


class ImportIn(BaseModel):
    data: dict
    replace: bool = False  # True：导入前先清空当前用户的全部订阅


@router.post("/import")
def import_data(
    payload: ImportIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """从导出的 JSON 恢复数据。自定义分类/付款方式/捆绑包按名称匹配，缺失则新建。"""
    data = payload.data or {}
    if not isinstance(data.get("subscriptions"), list):
        raise HTTPException(400, "备份文件格式不正确：缺少 subscriptions")

    count = _restore_entities(db, user, data, payload.replace)
    # 恢复通知渠道配置（旧备份无此字段则跳过，保证向后兼容）
    udata = data.get("user") or {}
    if isinstance(udata.get("notify_config"), dict):
        notify.apply_config(user, udata["notify_config"])
    db.commit()
    activity.log("backup.import", f"导入恢复了 {count} 个订阅", user=user)
    return {"ok": True, "imported": count}


# --------------------------------------------------------------------------- #
# 管理员：整站备份 / 恢复全部成员的数据
# --------------------------------------------------------------------------- #
def _user_meta(u: User) -> dict:
    """整站备份才导出账户信息（含密码哈希，便于完整还原账号）。仅管理员可访问。"""
    return {
        "username": u.username,
        "email": u.email,
        "password_hash": u.password_hash,
        "is_admin": u.is_admin,
        "is_active": u.is_active,
        "is_approved": u.is_approved,
        "email_verified": u.email_verified,
        "locale": u.locale,
        "theme": u.theme,
        "base_currency": u.base_currency,
        "category_order": u.category_order,
        "notify_config": notify.load_config(u),
    }


def build_full_backup(db: Session) -> dict:
    """构建整站备份数据（全部成员账户与数据）。供导出接口与定时自动备份共用。"""
    users = db.scalars(select(User).order_by(User.id)).all()
    payload_users = []
    for u in users:
        block = _collect_entities(db, u)
        block["user"] = _user_meta(u)
        payload_users.append(block)
    return {
        "export_version": EXPORT_VERSION,
        "app": "EasySub",
        "scope": "all",
        "exported_at": datetime.utcnow().isoformat(timespec="seconds"),
        "users": payload_users,
    }


@router.get("/export-all")
def export_all(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """管理员：导出全部成员的账户与数据（整站备份）。"""
    payload = build_full_backup(db)
    activity.log(
        "backup.export_all", f"管理员导出整站备份（{len(payload['users'])} 个用户）", user=admin
    )
    return payload


@router.get("/auto")
def list_auto_backups(admin: User = Depends(get_admin_user)):
    """管理员：查看服务器本地的每日自动备份文件列表。"""
    from app.services import autobackup  # 延迟导入避免循环
    return {"dir": autobackup.BACKUP_DIR, "keep": autobackup.KEEP, "files": autobackup.list_backups()}


@router.post("/auto/run")
def run_auto_backup_now(admin: User = Depends(get_admin_user)):
    """管理员：立即执行一次本地自动备份。"""
    from app.services import autobackup
    result = autobackup.run_auto_backup()
    activity.log("backup.auto_run", f"手动触发本地自动备份：{result}", user=admin)
    return result


class ImportAllIn(BaseModel):
    data: dict
    replace: bool = False  # True：每个用户导入前先清空其现有订阅


@router.post("/import-all")
def import_all(
    payload: ImportAllIn,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """管理员：从整站备份恢复全部成员数据。

    按用户名匹配现有账户；账户不存在则用备份中的账户信息（含密码哈希）新建。
    """
    data = payload.data or {}
    users_in = data.get("users")
    if not isinstance(users_in, list):
        raise HTTPException(400, "备份文件格式不正确：缺少 users（请使用整站备份文件）")

    existing_users = {u.username: u for u in db.scalars(select(User)).all()}
    created_users = 0
    total_subs = 0

    for ub in users_in:
        meta = ub.get("user") or {}
        username = meta.get("username")
        if not username:
            continue

        target = existing_users.get(username)
        if not target:
            # 新建账户：优先沿用备份的密码哈希，缺失则给一个需重置的占位密码
            pwd_hash = meta.get("password_hash") or hash_password(username + "@reset")
            target = User(
                username=username,
                email=meta.get("email") or f"{username}@example.com",
                password_hash=pwd_hash,
                is_admin=bool(meta.get("is_admin", False)),
                is_active=bool(meta.get("is_active", True)),
                is_approved=bool(meta.get("is_approved", True)),
                email_verified=bool(meta.get("email_verified", True)),
                locale=meta.get("locale", "zh"),
                theme=meta.get("theme", "light"),
                base_currency=meta.get("base_currency", "CNY"),
                category_order=meta.get("category_order"),
            )
            db.add(target)
            db.flush()
            existing_users[username] = target
            created_users += 1

        # 恢复该用户的通知渠道配置（旧备份无此字段则跳过）
        if isinstance(meta.get("notify_config"), dict):
            notify.apply_config(target, meta["notify_config"])

        total_subs += _restore_entities(db, target, ub, payload.replace)

    db.commit()
    activity.log(
        "backup.import_all",
        f"管理员恢复整站备份：新建 {created_users} 个用户，共导入 {total_subs} 个订阅",
        user=admin,
        level="warn",
    )
    return {"ok": True, "users": len(users_in), "created_users": created_users, "imported": total_subs}

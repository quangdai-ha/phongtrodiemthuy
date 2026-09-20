"""API quản lý khách trọ, điện nước và hợp đồng thuê phòng."""
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import get_current_admin, require_admin_role
from ..database import get_db
from ..models import (
    TENANT_STATUS_CHOICES,
    Contract,
    Room,
    SiteSettings,
    Tenant,
    UtilityBill,
)
from ..schemas import (
    ContractCreate,
    ContractOut,
    ContractUpdate,
    TenantCreate,
    TenantOut,
    TenantUpdate,
    UtilityBillCreate,
    UtilityBillOut,
    UtilityBillUpdate,
)

router = APIRouter(prefix="/api/tenants", tags=["tenants"])

_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def _tenant_out(t: Tenant) -> TenantOut:
    return TenantOut(
        id=t.id,
        full_name=t.full_name,
        phone=t.phone or "",
        id_card=t.id_card or "",
        permanent_address=t.permanent_address or "",
        note=t.note or "",
        room_id=t.room_id,
        room_name=t.room.name if t.room else None,
        check_in=t.check_in,
        check_out=t.check_out,
        status=t.status,
        created_at=t.created_at,
    )


def _bill_out(b: UtilityBill) -> UtilityBillOut:
    return UtilityBillOut(
        id=b.id,
        tenant_id=b.tenant_id,
        tenant_name=b.tenant.full_name if b.tenant else None,
        room_name=b.tenant.room.name if b.tenant and b.tenant.room else None,
        month=b.month,
        elec_old=b.elec_old or 0,
        elec_new=b.elec_new or 0,
        water_old=b.water_old or 0,
        water_new=b.water_new or 0,
        elec_amount=b.elec_amount or 0,
        water_amount=b.water_amount or 0,
        other_fee=b.other_fee or 0,
        total=b.total or 0,
        paid=bool(b.paid),
        note=b.note or "",
        created_at=b.created_at,
    )


def _contract_out(c: Contract) -> ContractOut:
    return ContractOut(
        id=c.id,
        tenant_id=c.tenant_id,
        tenant_name=c.tenant.full_name if c.tenant else None,
        room_name=c.tenant.room.name if c.tenant and c.tenant.room else None,
        start_date=c.start_date,
        end_date=c.end_date,
        deposit=c.deposit or 0,
        monthly_rent=c.monthly_rent or 0,
        note=c.note or "",
        created_at=c.created_at,
    )


def _get_unit_prices(db: Session) -> tuple[float, float]:
    settings = db.query(SiteSettings).order_by(SiteSettings.id).first()
    if settings is not None:
        return (
            settings.electricity_price if settings.electricity_price is not None else 3500,
            settings.water_price if settings.water_price is not None else 20000,
        )
    return 3500, 20000


def _get_tenant_or_404(db: Session, tenant_id: int) -> Tenant:
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if t is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách trọ.")
    return t
# ---------------------------------------------------------------------------
# Khách trọ
# ---------------------------------------------------------------------------

@router.get("", response_model=list[TenantOut])
def list_tenants(
    db: Session = Depends(get_db),
    q: str = Query("", description="Tìm theo tên / SĐT"),
    status: str = Query("", description="Lọc theo trạng thái"),
    admin=Depends(get_current_admin),
):
    """Danh sách khách trọ (admin)."""
    query = db.query(Tenant)
    if q and q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(
            Tenant.full_name.ilike(like) | Tenant.phone.ilike(like)
        )
    if status and status in TENANT_STATUS_CHOICES:
        query = query.filter(Tenant.status == status)
    rows = query.order_by(Tenant.id.desc()).all()
    return [_tenant_out(t) for t in rows]


@router.post("", response_model=TenantOut, status_code=201)
def create_tenant(
    body: TenantCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Thêm khách trọ mới."""
    full_name = (body.full_name or "").strip()
    if not full_name:
        raise HTTPException(status_code=400, detail="Vui lòng nhập họ tên khách trọ.")
    if body.status not in TENANT_STATUS_CHOICES:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ.")
    if body.room_id is not None and db.query(Room).filter(Room.id == body.room_id).first() is None:
        raise HTTPException(status_code=400, detail="Phòng không tồn tại.")

    t = Tenant(
        full_name=full_name,
        phone=(body.phone or "").strip(),
        id_card=(body.id_card or "").strip(),
        permanent_address=(body.permanent_address or "").strip(),
        note=body.note or "",
        room_id=body.room_id,
        check_in=body.check_in,
        check_out=body.check_out,
        status=body.status,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _tenant_out(t)
@router.put("/{tenant_id}", response_model=TenantOut)
def update_tenant(
    tenant_id: int,
    body: TenantUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Cập nhật thông tin khách trọ."""
    t = _get_tenant_or_404(db, tenant_id)
    updates = body.model_dump(exclude_unset=True)

    if "full_name" in updates:
        name = (updates["full_name"] or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Họ tên không được để trống.")
        updates["full_name"] = name
    if "status" in updates and updates["status"] not in TENANT_STATUS_CHOICES:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ.")
    if updates.get("room_id") is not None and db.query(Room).filter(Room.id == updates["room_id"]).first() is None:
        raise HTTPException(status_code=400, detail="Phòng không tồn tại.")

    for field, value in updates.items():
        setattr(t, field, value)
    db.commit()
    db.refresh(t)
    return _tenant_out(t)


@router.delete("/{tenant_id}", status_code=204)
def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin_role),
):
    """Xóa khách trọ (chỉ role admin); xóa luôn hóa đơn & hợp đồng liên quan."""
    t = _get_tenant_or_404(db, tenant_id)
    db.query(UtilityBill).filter(UtilityBill.tenant_id == t.id).delete()
    db.query(Contract).filter(Contract.tenant_id == t.id).delete()
    db.delete(t)
    db.commit()
# ---------------------------------------------------------------------------
# Điện nước
# ---------------------------------------------------------------------------

def _compute_bill(db: Session, body, elec_price, water_price) -> dict:
    """Tính thành tiền điện/nước/tổng từ số liệu đầu vào."""
    if not _MONTH_RE.match(body.month):
        raise HTTPException(status_code=400, detail="Tháng phải có dạng YYYY-MM (VD: 2026-09).")
    if body.elec_new < body.elec_old or body.water_new < body.water_old:
        raise HTTPException(status_code=400, detail="Chỉ số mới phải lớn hơn hoặc bằng chỉ số cũ.")
    if body.other_fee < 0:
        raise HTTPException(status_code=400, detail="Phụ phí không được âm.")

    elec_amount = (body.elec_new - body.elec_old) * elec_price
    water_amount = (body.water_new - body.water_old) * water_price
    total = round(elec_amount + water_amount + body.other_fee, 0)
    return {
        "elec_amount": round(elec_amount, 0),
        "water_amount": round(water_amount, 0),
        "total": total,
    }


@router.get("/bills", response_model=list[UtilityBillOut])
def list_bills(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
    month: str = Query("", description="Lọc theo tháng YYYY-MM"),
    tenant_id: int = Query(None, description="Lọc theo khách trọ"),
):
    """Danh sách hóa đơn điện nước."""
    query = db.query(UtilityBill)
    if month:
        query = query.filter(UtilityBill.month == month)
    if tenant_id:
        query = query.filter(UtilityBill.tenant_id == tenant_id)
    rows = query.order_by(UtilityBill.month.desc(), UtilityBill.id.desc()).all()
    return [_bill_out(b) for b in rows]


@router.get("/bills/months", include_in_schema=False)
def bill_months(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Danh sách tháng đã có hóa đơn (để làm danh sách lọc)."""
    rows = db.query(UtilityBill.month).distinct().order_by(UtilityBill.month.desc()).all()
    return {"months": [r[0] for r in rows]}


@router.post("/bills", response_model=UtilityBillOut, status_code=201)
def create_bill(
    body: UtilityBillCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Thêm hóa đơn điện nước cho khách trọ."""
    _get_tenant_or_404(db, body.tenant_id)
    elec_price, water_price = _get_unit_prices(db)
    amounts = _compute_bill(db, body, elec_price, water_price)
    b = UtilityBill(
        tenant_id=body.tenant_id,
        month=body.month,
        elec_old=body.elec_old,
        elec_new=body.elec_new,
        water_old=body.water_old,
        water_new=body.water_new,
        other_fee=body.other_fee,
        note=(body.note or "").strip(),
        **amounts,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return _bill_out(b)


@router.put("/bills/{bill_id}", response_model=UtilityBillOut)
def update_bill(
    bill_id: int,
    body: UtilityBillUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Sửa số liệu hóa đơn; tự tính lại thành tiền theo đơn giá đang lưu."""
    b = db.query(UtilityBill).filter(UtilityBill.id == bill_id).first()
    if b is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn.")
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(b, field, value)
    elec_price, water_price = _get_unit_prices(db)
    proxy = UtilityBillCreate(
        tenant_id=b.tenant_id,
        month=b.month,
        elec_old=b.elec_old or 0,
        elec_new=b.elec_new or 0,
        water_old=b.water_old or 0,
        water_new=b.water_new or 0,
        other_fee=b.other_fee or 0,
        note=b.note or "",
    )
    amounts = _compute_bill(db, proxy, elec_price, water_price)
    for field, value in amounts.items():
        setattr(b, field, value)
    db.commit()
    db.refresh(b)
    return _bill_out(b)


@router.put("/bills/{bill_id}/paid", response_model=UtilityBillOut)
def set_bill_paid(
    bill_id: int,
    body: dict,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Đánh dấu đã thu tiền / chưa thu."""
    b = db.query(UtilityBill).filter(UtilityBill.id == bill_id).first()
    if b is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn.")
    b.paid = bool(body.get("paid", False))
    db.commit()
    db.refresh(b)
    return _bill_out(b)


@router.delete("/bills/{bill_id}", status_code=204)
def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin_role),
):
    """Xóa hóa đơn (chỉ role admin)."""
    b = db.query(UtilityBill).filter(UtilityBill.id == bill_id).first()
    if b is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn.")
    db.delete(b)
    db.commit()
# ---------------------------------------------------------------------------
# Hợp đồng thuê
# ---------------------------------------------------------------------------

@router.get("/contracts", response_model=list[ContractOut])
def list_contracts(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
    tenant_id: int = Query(None, description="Lọc theo khách trọ"),
):
    """Danh sách hợp đồng."""
    query = db.query(Contract)
    if tenant_id:
        query = query.filter(Contract.tenant_id == tenant_id)
    rows = query.order_by(Contract.id.desc()).all()
    return [_contract_out(c) for c in rows]


@router.post("/contracts", response_model=ContractOut, status_code=201)
def create_contract(
    body: ContractCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Thêm hợp đồng thuê mới."""
    _get_tenant_or_404(db, body.tenant_id)
    if body.start_date and body.end_date and body.end_date < body.start_date:
        raise HTTPException(status_code=400, detail="Ngày kết thúc phải sau ngày bắt đầu.")
    c = Contract(
        tenant_id=body.tenant_id,
        start_date=body.start_date,
        end_date=body.end_date,
        deposit=body.deposit or 0,
        monthly_rent=body.monthly_rent or 0,
        note=body.note or "",
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _contract_out(c)


@router.put("/contracts/{contract_id}", response_model=ContractOut)
def update_contract(
    contract_id: int,
    body: ContractUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Sửa hợp đồng."""
    c = db.query(Contract).filter(Contract.id == contract_id).first()
    if c is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hợp đồng.")
    updates = body.model_dump(exclude_unset=True)
    start = updates.get("start_date", c.start_date)
    end = updates.get("end_date", c.end_date)
    if start and end and end < start:
        raise HTTPException(status_code=400, detail="Ngày kết thúc phải sau ngày bắt đầu.")
    for field, value in updates.items():
        setattr(c, field, value)
    db.commit()
    db.refresh(c)
    return _contract_out(c)


@router.delete("/contracts/{contract_id}", status_code=204)
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin_role),
):
    """Xóa hợp đồng (chỉ role admin)."""
    c = db.query(Contract).filter(Contract.id == contract_id).first()
    if c is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hợp đồng.")
    db.delete(c)
    db.commit()
# (Định nghĩa sau cùng để không nuốt các đường dẫn /bills, /contracts)
@router.get("/{tenant_id}", response_model=TenantOut)
def tenant_detail(
    tenant_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Chi tiết khách trọ."""
    return _tenant_out(_get_tenant_or_404(db, tenant_id))
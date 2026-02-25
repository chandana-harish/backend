from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.schemas import InvoiceResponse
from app.services.invoice_service import (
    create_invoice,
    get_invoice,
    list_invoices,
    cancel_invoice,
)

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
)

@router.post(
    "/orders/{order_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invoice_for_order(
    order_id: int,
    discount_type: str | None = None,
    discount_value: Decimal = Decimal("0.00"),
    db: Session = Depends(get_db),
):
    try:
        return create_invoice(
            db=db,
            order_id=order_id,
            discount_type=discount_type,
            discount_value=discount_value,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
)
def get_invoice_by_id(
    invoice_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_invoice(db, invoice_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

@router.get(
    "",
    response_model=list[InvoiceResponse],
)
def list_all_invoices(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    order_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    return list_invoices(
        db=db,
        status=status,
        customer_id=customer_id,
        order_id=order_id,
        from_date=from_date,
        to_date=to_date,
    )
@router.post(
    "/{invoice_id}/cancel",
    response_model=InvoiceResponse,
)
def cancel_invoice_api(
    invoice_id: int,
    db: Session = Depends(get_db),
):
    try:
        return cancel_invoice(db, invoice_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

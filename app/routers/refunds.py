from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.schemas import InvoiceResponse
from app.services.refund_service import refund_payment

router = APIRouter(
    prefix="/refunds",
    tags=["Refunds"],
)
@router.post(
    "/invoice/{invoice_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def refund_invoice_api(
    invoice_id: int,
    reason: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        return refund_payment(
            db=db,
            invoice_id=invoice_id,
            reason=reason,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

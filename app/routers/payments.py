from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.schemas import PaymentResponse, PaymentCreate
from app.services.payment_service import (
    create_payment,
    get_payments_for_invoice,
)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


# -----------------------------
# CREATE PAYMENT
# -----------------------------
@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_api(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
):
    try:
        payment = create_payment(
            db=db,
            invoice_id=payload.invoice_id,
            amount=payload.amount,
            payment_method=payload.payment_method,
        )
        return payment

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

# -----------------------------
# GET PAYMENTS FOR AN INVOICE
# -----------------------------
@router.get(
    "/invoice/{invoice_id}",
    response_model=list[PaymentResponse],
)
def get_payments_for_invoice_api(
    invoice_id: int,
    db: Session = Depends(get_db),
):
    """
    Fetch all payments for a given invoice.
    """
    try:
        return get_payments_for_invoice(db, invoice_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

from pydantic import BaseModel

class PurchaseVerifySchema(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str
    plan_name: str
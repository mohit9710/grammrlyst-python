from fastapi import APIRouter, HTTPException
import os, uuid, requests, json
from dotenv import load_dotenv
from app.core.paytm_checksum import generate_checksum

load_dotenv()

router = APIRouter(prefix="/paytm", tags=["Paytm"])

PAYTM_MID = os.getenv("PAYTM_MID")
PAYTM_KEY = os.getenv("PAYTM_MERCHANT_KEY")
CALLBACK_URL = os.getenv("PAYTM_CALLBACK_URL")

PAYTM_INITIATE_URL = "https://securestage.paytmpayments.com/theia/api/v1/initiateTransaction"

@router.post("/create-payment")
def create_payment(amount: float):
    order_id = str(uuid.uuid4())

    body = {
        "requestType": "Payment",
        "mid": PAYTM_MID,
        "websiteName": "WEBSTAGING",
        "orderId": order_id,
        "callbackUrl": CALLBACK_URL,
        "txnAmount": {
            "value": f"{amount:.2f}",
            "currency": "INR"
        },
        "userInfo": {
            "custId": "CUST_001"
        }
    }

    body_str = json.dumps(body, separators=(",", ":"))
    signature = generate_checksum(body_str, PAYTM_KEY)

    payload = {
        "body": body,
        "head": {
            "signature": signature
        }
    }

    url = f"{PAYTM_INITIATE_URL}?mid={PAYTM_MID}&orderId={order_id}"

    res = requests.post(url, json=payload, timeout=10)
    response = res.json()

    print("PAYTM INIT RESPONSE:", response)

    if response["body"]["resultInfo"]["resultStatus"] != "S":
        raise HTTPException(status_code=400, detail=response)

    return {
        "orderId": order_id,
        "txnToken": response["body"]["txnToken"],
        "amount": amount,
        "mid": PAYTM_MID
    }

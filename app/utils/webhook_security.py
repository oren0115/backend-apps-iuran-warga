import hmac
import hashlib
import base64
from fastapi import HTTPException, status
import os
import logging

logger = logging.getLogger(__name__)

def verify_midtrans_signature(request_body: str, signature: str, secret_key: str) -> bool:
    """
    Verify Midtrans webhook signature
    """
    try:
        # Create expected signature
        expected_signature = base64.b64encode(
            hmac.new(
                secret_key.encode('utf-8'),
                request_body.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        # Compare signatures using constant time comparison
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False

def verify_webhook_signature(request_body: str, signature: str) -> bool:
    """
    Verify webhook signature using environment variable
    """
    webhook_secret = os.getenv("WEBHOOK_SECRET")
    return verify_midtrans_signature(request_body, signature, webhook_secret)

def validate_webhook_request(request_body: str, signature: str) -> None:
    """
    Validate webhook request and raise exception if invalid
    """
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing signature header"
        )
    
    if not verify_webhook_signature(request_body, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )

"""BRI BaaS API Client Service."""

import hashlib
import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from decimal import Decimal

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BRIAPIError(Exception):
    """Base exception for BRI API errors."""
    pass


class BRIAuthenticationError(BRIAPIError):
    """Authentication related errors."""
    pass


class BRIInsufficientBalanceError(BRIAPIError):
    """Insufficient balance error."""
    pass


class BRITransferError(BRIAPIError):
    """Transfer related errors."""
    pass


# ============================================================================
# Response Models
# ============================================================================

class BRIVAResponse(BaseModel):
    """BRIVA creation response."""
    institution_code: str
    briva_no: str
    cust_code: str
    virtual_account: str
    amount: str
    status: str
    expired_date: str


class BalanceResponse(BaseModel):
    """Account balance response."""
    account_number: str
    balance: Decimal
    currency: str = "IDR"


class TransferResponse(BaseModel):
    """Transfer response."""
    response_code: str
    response_message: str
    reference_number: str
    transaction_id: Optional[str] = None


# ============================================================================
# BRI API Client
# ============================================================================

class BRIAPIClient:
    """BRI BaaS API Client with authentication and core banking operations."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        api_key: str,
        base_url: str = "https://sandbox.partner.api.bri.co.id",
        merchant_account: str = "201101000546304"  # Sensasiwangi marketplace account
    ):
        """Initialize BRI API client.
        
        Args:
            client_id: BRI OAuth client ID
            client_secret: BRI OAuth client secret  
            api_key: BRI API key
            base_url: BRI API base URL (sandbox or production)
            merchant_account: Marketplace BRI account number
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_key = api_key
        self.base_url = base_url
        self.merchant_account = merchant_account
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    # ========================================================================
    # Authentication
    # ========================================================================
    
    def _generate_signature(self, method: str, endpoint: str, timestamp: str, body: str = "") -> str:
        """Generate HMAC-SHA512 signature for request authentication.
        
        Args:
            method: HTTP method (GET, POST, etc)
            endpoint: API endpoint path
            timestamp: ISO 8601 timestamp
            body: Request body JSON string
            
        Returns:
            Base64 encoded signature
        """
        # String to sign: HTTP-Method + ":" + RelativeUrl + ":" + Digest(Request Body) + ":" + Timestamp
        if body:
            body_hash = hashlib.sha256(body.encode()).hexdigest().lower()
        else:
            body_hash = hashlib.sha256(b"").hexdigest().lower()
        
        string_to_sign = f"{method}:{endpoint}:{body_hash}:{timestamp}"
        
        signature = hmac.new(
            self.client_secret.encode(),
            string_to_sign.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return signature
    
    async def _get_access_token(self) -> str:
        """Get or refresh OAuth access token.
        
        Returns:
            Valid access token
            
        Raises:
            BRIAuthenticationError: If authentication fails
        """
        # Check if we have a valid token
        if self._access_token and self._token_expires_at:
            if datetime.now(timezone.utc) < self._token_expires_at:
                return self._access_token
        
        # Get new token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/client_credential/accesstoken",
                data={
                    "grant_type": "client_credentials"
                },
                auth=(self.client_id, self.client_secret),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"BRI authentication failed: {response.text}")
                raise BRIAuthenticationError(f"Failed to get access token: {response.text}")
            
            data = response.json()
            self._access_token = data["access_token"]
            
            # Token typically expires in 3600 seconds (1 hour)
            expires_in = data.get("expires_in", 3600)
            self._token_expires_at = datetime.now(timezone.utc).replace(
                second=0, microsecond=0
            ) + timedelta(seconds=expires_in - 60)  # Refresh 1 min before expiry
            
            logger.info("BRI access token obtained successfully")
            return self._access_token
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to BRI API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data as dict
            
        Raises:
            BRIAPIError: If request fails
        """
        token = await self._get_access_token()
        timestamp = datetime.now(timezone.utc).isoformat()
        
        body_str = ""
        if data:
            import json
            body_str = json.dumps(data)
        
        signature = self._generate_signature(method, endpoint, timestamp, body_str)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "BRI-Timestamp": timestamp,
            "BRI-Signature": signature,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    params=params
                )
            elif method == "POST":
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    json=data
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code not in [200, 201]:
                logger.error(f"BRI API request failed: {response.text}")
                raise BRIAPIError(f"API request failed: {response.text}")
            
            return response.json()
    
    # ========================================================================
    # BRIVA (Virtual Account)
    # ========================================================================
    
    async def create_briva(
        self,
        amount: Decimal,
        customer_name: str,
        customer_code: str,
        description: str = "",
        expired_date: Optional[datetime] = None
    ) -> BRIVAResponse:
        """Create BRIVA (BRI Virtual Account) for payment collection.
        
        Args:
            amount: Payment amount
            customer_name: Customer name
            customer_code: Unique customer/order code
            description: Payment description
            expired_date: VA expiration date (default: 48 hours)
            
        Returns:
            BRIVA response with virtual account number
        """
        if not expired_date:
            from datetime import timedelta
            expired_date = datetime.now(timezone.utc) + timedelta(hours=48)
        
        data = {
            "institutionCode": "J104408",  # BRI institution code
            "brivaNo": "77777",  # Fixed prefix for marketplace
            "custCode": customer_code[-10:],  # Last 10 chars of customer code
            "nama": customer_name[:50],  # Max 50 chars
            "amount": str(int(amount)),
            "keterangan": description[:50] if description else "",
            "expiredDate": expired_date.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        response = await self._make_request("POST", "/v1/briva", data=data)
        
        # Parse response
        briva_data = response.get("data", {})
        
        return BRIVAResponse(
            institution_code=briva_data["institutionCode"],
            briva_no=briva_data["brivaNo"],
            cust_code=briva_data["custCode"],
            virtual_account=f"{briva_data['brivaNo']}{briva_data['custCode']}",
            amount=briva_data["amount"],
            status=briva_data.get("status", "active"),
            expired_date=briva_data["expiredDate"]
        )
    
    async def check_briva_status(self, briva_no: str, cust_code: str) -> Dict[str, Any]:
        """Check BRIVA payment status.
        
        Args:
            briva_no: BRIVA number
            cust_code: Customer code
            
        Returns:
            Payment status data
        """
        endpoint = f"/v1/briva/J104408/{briva_no}/{cust_code}"
        response = await self._make_request("GET", endpoint)
        return response.get("data", {})
    
    # ========================================================================
    # Account Operations
    # ========================================================================
    
    async def get_account_balance(self, account_number: str) -> BalanceResponse:
        """Get account balance.
        
        Args:
            account_number: BRI account number
            
        Returns:
            Account balance information
        """
        endpoint = "/v1.0/openingAccount/accountBalance"
        data = {
            "accountNumber": account_number
        }
        
        response = await self._make_request("POST", endpoint, data=data)
        balance_data = response.get("additionalInfo", {})
        
        return BalanceResponse(
            account_number=account_number,
            balance=Decimal(balance_data.get("balance", "0"))
        )
    
    async def get_account_statement(
        self,
        account_number: str,
        start_date: datetime,
        end_date: datetime
    ) -> list[Dict[str, Any]]:
        """Get account statement/transaction history.
        
        Args:
            account_number: BRI account number
            start_date: Statement start date
            end_date: Statement end date
            
        Returns:
            List of transactions
        """
        endpoint = "/v1.0/openingAccount/accountStatement"
        data = {
            "accountNumber": account_number,
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d")
        }
        
        response = await self._make_request("POST", endpoint, data=data)
        return response.get("data", {}).get("transactions", [])
    
    # ========================================================================
    # Fund Transfer
    # ========================================================================
    
    async def transfer_internal(
        self,
        beneficiary_account: str,
        amount: Decimal,
        remark: str = "",
        reference_number: Optional[str] = None
    ) -> TransferResponse:
        """Transfer funds to another BRI account (internal transfer).
        
        Args:
            beneficiary_account: Destination BRI account number
            amount: Transfer amount
            remark: Transfer description
            reference_number: Unique reference number
            
        Returns:
            Transfer response with status
            
        Raises:
            BRIInsufficientBalanceError: If insufficient balance
            BRITransferError: If transfer fails
        """
        if not reference_number:
            import uuid
            reference_number = f"TRF{uuid.uuid4().hex[:12].upper()}"
        
        data = {
            "partnerReferenceNo": reference_number,
            "sourceAccountNo": self.merchant_account,
            "beneficiaryAccountNo": beneficiary_account,
            "amount": {
                "value": str(amount),
                "currency": "IDR"
            },
            "remark": remark[:100] if remark else ""
        }
        
        try:
            response = await self._make_request("POST", "/v3/transfer/internal", data=data)
            
            return TransferResponse(
                response_code=response["responseCode"],
                response_message=response["responseMessage"],
                reference_number=response.get("referenceNo", reference_number),
                transaction_id=response.get("transactionId")
            )
            
        except BRIAPIError as e:
            error_msg = str(e).lower()
            if "insufficient" in error_msg or "balance" in error_msg:
                raise BRIInsufficientBalanceError(f"Insufficient balance for transfer: {amount}")
            raise BRITransferError(f"Transfer failed: {e}")
    
    async def transfer_external(
        self,
        beneficiary_account: str,
        beneficiary_bank_code: str,
        amount: Decimal,
        beneficiary_name: str,
        remark: str = "",
        reference_number: Optional[str] = None
    ) -> TransferResponse:
        """Transfer funds to external bank account (interbank transfer).
        
        Args:
            beneficiary_account: Destination account number
            beneficiary_bank_code: Bank code (e.g., "014" for BCA)
            amount: Transfer amount
            beneficiary_name: Beneficiary name
            remark: Transfer description
            reference_number: Unique reference number
            
        Returns:
            Transfer response with status
        """
        if not reference_number:
            import uuid
            reference_number = f"TRF{uuid.uuid4().hex[:12].upper()}"
        
        # First, inquiry beneficiary account
        inquiry_data = {
            "beneficiaryBankCode": beneficiary_bank_code,
            "beneficiaryAccountNo": beneficiary_account,
            "additionalInfo": {
                "deviceId": "marketplace",
                "channel": "web"
            }
        }
        
        inquiry_response = await self._make_request(
            "POST",
            "/snap-bi/api-account-inquiry-external-interbank-transfer",
            data=inquiry_data
        )
        
        # Then execute transfer
        transfer_data = {
            "partnerReferenceNo": reference_number,
            "sourceAccountNo": self.merchant_account,
            "beneficiaryBankCode": beneficiary_bank_code,
            "beneficiaryAccountNo": beneficiary_account,
            "beneficiaryAccountName": beneficiary_name,
            "amount": {
                "value": str(amount),
                "currency": "IDR"
            },
            "remark": remark[:100] if remark else ""
        }
        
        response = await self._make_request(
            "POST",
            "/snap-bi/api-transfer-interbank",
            data=transfer_data
        )
        
        return TransferResponse(
            response_code=response["responseCode"],
            response_message=response["responseMessage"],
            reference_number=response.get("referenceNo", reference_number),
            transaction_id=response.get("transactionId")
        )


# ============================================================================
# Factory Function
# ============================================================================

def create_bri_client(
    client_id: str,
    client_secret: str,
    api_key: str,
    is_production: bool = False
) -> BRIAPIClient:
    """Create BRI API client instance.
    
    Args:
        client_id: BRI OAuth client ID
        client_secret: BRI OAuth client secret
        api_key: BRI API key
        is_production: Use production URL if True, sandbox if False
        
    Returns:
        Configured BRI API client
    """
    base_url = (
        "https://partner.api.bri.co.id"
        if is_production
        else "https://sandbox.partner.api.bri.co.id"
    )
    
    return BRIAPIClient(
        client_id=client_id,
        client_secret=client_secret,
        api_key=api_key,
        base_url=base_url
    )

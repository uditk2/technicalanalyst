import json
from typing import Dict, Any, Optional, List, Callable
from neo_api_client import NeoAPI, BaseUrl
import logging

from .config import ingestion_config
from app.config import get_default_subscription_instruments, format_for_kotak_api

logger = logging.getLogger(__name__)

class KotakNeoSubscriber:
    def __init__(self):
        self.client: Optional[NeoAPI] = None
        self.is_connected = False
        self.is_authenticated = False
        self.on_message_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
        self.subscribed_instruments = []

    def initialize_client(self):
        """Initialize the Kotak Neo API client"""
        try:
            if not ingestion_config.kotak_ucc:
                raise ValueError("Kotak UCC is required")

            base_url = BaseUrl(ucc=ingestion_config.kotak_ucc).get_base_url()
            if not isinstance(base_url, str) or not base_url.startswith('http'):
                raise RuntimeError(f'Failed to resolve base URL for UCC {ingestion_config.kotak_ucc}: {base_url}')

            self.client = NeoAPI(
                consumer_key=ingestion_config.kotak_consumer_key,
                consumer_secret=ingestion_config.kotak_consumer_secret,
                environment=ingestion_config.kotak_environment,
                access_token=None,
                neo_fin_key=ingestion_config.kotak_neo_fin_key,
                base_url=base_url,
            )

            # Set up callbacks - exactly like in the demo notebook
            self.client.on_message = self._on_message
            self.client.on_error = self._on_error
            self.client.on_open = self._on_open
            self.client.on_close = self._on_close

            logger.info("Kotak Neo API client initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing Kotak Neo client: {e}")
            return False

    def authenticate(self, totp_code: str, mpin: str = None) -> Dict[str, Any]:
        """Authenticate with Kotak Neo using TOTP - based on notebook code"""
        try:
            if not self.client:
                self.initialize_client()

            if not ingestion_config.kotak_mobile_number:
                return {"success": False, "error": "Mobile number is required"}

            # Perform TOTP login - exactly like in the notebook
            login_response = self.client.totp_login(
                mobile_number=ingestion_config.kotak_mobile_number,
                ucc=ingestion_config.kotak_ucc,
                totp=totp_code
            )

            logger.info(f"Login response: {login_response}")

            if login_response.get('data'):
                self.is_authenticated = True

                # If MPIN is provided, perform 2FA
                if mpin:
                    two_fa_response = self.client.totp_validate(mpin=mpin)
                    logger.info(f"2FA response: {two_fa_response}")

                    if not two_fa_response.get('data'):
                        return {
                            "success": False,
                            "error": "2FA validation failed",
                            "details": two_fa_response
                        }

                return {
                    "success": True,
                    "message": "Authentication successful",
                    "data": login_response
                }
            else:
                error_msg = "Authentication failed"
                if login_response.get('error'):
                    errors = login_response['error']
                    if isinstance(errors, list) and errors:
                        error_details = errors[0].get('errors', [])
                        if error_details:
                            error_msg = error_details[0].get('message', error_msg)

                return {
                    "success": False,
                    "error": error_msg,
                    "details": login_response
                }

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {
                "success": False,
                "error": f"Authentication failed: {str(e)}"
            }

    def subscribe_to_instruments(self, instruments: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Subscribe to stock instruments for live data - based on notebook code"""
        try:
            if not self.is_authenticated:
                return {"success": False, "error": "Not authenticated"}

            # Default instruments if none provided - use centralized config
            if not instruments:
                instruments = get_default_subscription_instruments()

            self.subscribed_instruments = instruments

            # Subscribe exactly like in the notebook
            self.client.subscribe(
                instrument_tokens=instruments,
                isIndex=False,
                isDepth=False
            )

            logger.info(f"Subscribed to {len(instruments)} instruments")
            return {
                "success": True,
                "message": f"Subscribed to {len(instruments)} instruments",
                "instruments": instruments
            }

        except Exception as e:
            logger.error(f"Subscription error: {e}")
            return {
                "success": False,
                "error": f"Subscription failed: {str(e)}"
            }

    def unsubscribe_from_instruments(self) -> Dict[str, Any]:
        """Unsubscribe from all instruments - based on notebook code"""
        try:
            if not self.is_authenticated or not self.subscribed_instruments:
                return {"success": False, "error": "Not subscribed to any instruments"}

            # Unsubscribe exactly like in the notebook
            self.client.un_subscribe(
                instrument_tokens=self.subscribed_instruments,
                isIndex=False,
                isDepth=False
            )

            logger.info("Unsubscribed from all instruments")
            self.subscribed_instruments = []
            return {
                "success": True,
                "message": "Unsubscribed from all instruments"
            }

        except Exception as e:
            logger.error(f"Unsubscription error: {e}")
            return {
                "success": False,
                "error": f"Unsubscription failed: {str(e)}"
            }

    def set_message_callback(self, callback: Callable):
        """Set callback for processing incoming messages"""
        self.on_message_callback = callback

    def set_error_callback(self, callback: Callable):
        """Set callback for handling errors"""
        self.on_error_callback = callback

    def _on_message(self, message):
        """Internal message handler - exactly like notebook callback"""
        try:
            print(f"[DEBUG] Raw WebSocket message received: {message}")
            logger.info(f"[Res]: {message}")
            if self.on_message_callback:
                formatted_message = f"[Res]: {json.dumps(message)}"
                print(f"[DEBUG] Calling callback with formatted message: {formatted_message}")
                self.on_message_callback(formatted_message)
            else:
                print("[DEBUG] No message callback set - message will be ignored")
        except Exception as e:
            print(f"[DEBUG] Error processing message: {e}")
            logger.error(f"Error processing message: {e}")

    def _on_error(self, message):
        """Internal error handler"""
        logger.error(f"WebSocket error: {message}")
        if self.on_error_callback:
            self.on_error_callback(message)

    def _on_open(self, message):
        """Internal connection open handler"""
        logger.info(f"WebSocket connection opened: {message}")
        self.is_connected = True

    def _on_close(self, message):
        """Internal connection close handler"""
        logger.info(f"WebSocket connection closed: {message}")
        self.is_connected = False

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the subscriber"""
        return {
            "is_connected": self.is_connected,
            "is_authenticated": self.is_authenticated,
            "subscribed_instruments": len(self.subscribed_instruments),
            "instruments": self.subscribed_instruments
        }

# Global instance
kotak_subscriber = KotakNeoSubscriber()
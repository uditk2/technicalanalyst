from typing import Dict, List, Optional, TypedDict
from enum import Enum
import json
import os

class ExchangeSegment(str, Enum):
    NSE_CM = "nse_cm"
    BSE_CM = "bse_cm"
    NSE_FO = "nse_fo"
    BSE_FO = "bse_fo"
    CDE_FO = "cde_fo"
    MCX_FO = "mcx_fo"

class InstrumentConfig(TypedDict):
    instrument_token: str
    exchange_segment: ExchangeSegment
    symbol: str
    company_name: str
    sector: Optional[str]
    instrument_type: str

class InstrumentRegistry:
    def __init__(self):
        self._instruments: Dict[str, InstrumentConfig] = {}
        self._load_default_instruments()

    def _load_default_instruments(self):
        """Load instruments from JSON file"""
        json_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'instruments.json')

        try:
            with open(json_file_path, 'r') as f:
                instruments_data = json.load(f)

            for instrument in instruments_data:
                key = f"{instrument['symbol']}_{instrument['exchange_segment']}"
                self._instruments[key] = instrument

        except Exception as e:
            print(f"Error loading instruments: {e}")

    def get_all_instruments(self) -> List[InstrumentConfig]:
        """Get all available instruments"""
        return list(self._instruments.values())

    def search_instruments(self, query: str, limit: int = 10) -> List[InstrumentConfig]:
        """Search instruments by symbol or company name"""
        query = query.lower().strip()
        if not query:
            return self.get_all_instruments()[:limit]

        matches = []
        for instrument in self._instruments.values():
            if (query in instrument['symbol'].lower() or
                query in instrument['company_name'].lower() or
                query in instrument.get('sector', '').lower()):
                matches.append(instrument)

        return matches[:limit]

    def get_by_symbol(self, symbol: str, exchange: ExchangeSegment) -> Optional[InstrumentConfig]:
        """Get instrument by symbol and exchange"""
        key = f"{symbol}_{exchange}"
        return self._instruments.get(key)

    def get_by_token(self, token: str) -> List[InstrumentConfig]:
        """Get instruments by token (may have multiple exchanges)"""
        return [inst for inst in self._instruments.values()
                if inst['instrument_token'] == token]

    def get_instruments_by_sector(self, sector: str) -> List[InstrumentConfig]:
        """Get instruments filtered by sector"""
        return [inst for inst in self._instruments.values()
                if inst.get('sector', '').lower() == sector.lower()]

    def get_exchange_segments(self) -> List[str]:
        """Get all available exchange segments"""
        return [e.value for e in ExchangeSegment]

    def get_sectors(self) -> List[str]:
        """Get all available sectors"""
        sectors = set()
        for instrument in self._instruments.values():
            if instrument.get('sector'):
                sectors.add(instrument['sector'])
        return sorted(list(sectors))

instrument_registry = InstrumentRegistry()

def get_default_subscription_instruments() -> List[Dict[str, str]]:
    """Get default instruments for subscription - just Nifty 50"""
    return [{"instrument_token": "Nifty 50", "exchange_segment": "nse_cm"}]

def get_nifty50_subscription() -> List[Dict[str, str]]:
    """Get all Nifty 50 stocks for subscription"""
    nifty50_instruments = []

    # Get all equity instruments (excluding indices)
    for instrument in instrument_registry.get_all_instruments():
        if (instrument['instrument_type'] == 'equity' and
            instrument['exchange_segment'] == 'nse_cm'):
            nifty50_instruments.append({
                "instrument_token": instrument['instrument_token'],
                "exchange_segment": instrument['exchange_segment']
            })

    return nifty50_instruments

def format_for_kotak_api(instruments: List[InstrumentConfig]) -> List[Dict[str, str]]:
    """Format instrument configs for Kotak API subscription"""
    return [
        {
            "instrument_token": inst['instrument_token'],
            "exchange_segment": inst['exchange_segment']
        }
        for inst in instruments
    ]
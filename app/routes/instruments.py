from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.config import instrument_registry, InstrumentConfig, format_for_kotak_api, get_nifty50_subscription

router = APIRouter(prefix="/api/instruments", tags=["instruments"])

class InstrumentSearchResponse(BaseModel):
    instruments: List[InstrumentConfig]
    total: int

class InstrumentAutocompleteItem(BaseModel):
    value: str
    label: str
    token: str
    exchange: str
    sector: Optional[str] = None

@router.get("/search", response_model=InstrumentSearchResponse)
async def search_instruments(
    query: str = Query("", description="Search query for instruments"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """Search instruments by symbol, company name, or sector"""
    try:
        instruments = instrument_registry.search_instruments(query, limit)
        return InstrumentSearchResponse(
            instruments=instruments,
            total=len(instruments)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/autocomplete")
async def autocomplete_instruments(
    query: str = Query("", description="Search query for autocomplete"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of suggestions")
) -> List[InstrumentAutocompleteItem]:
    """Get autocomplete suggestions for instruments"""
    try:
        instruments = instrument_registry.search_instruments(query, limit)
        return [
            InstrumentAutocompleteItem(
                value=f"{inst['symbol']}_{inst['exchange_segment']}",
                label=f"{inst['symbol']} - {inst['company_name']} ({inst['exchange_segment'].upper()})",
                token=inst['instrument_token'],
                exchange=inst['exchange_segment'],
                sector=inst.get('sector')
            )
            for inst in instruments
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autocomplete failed: {str(e)}")

@router.get("/all")
async def get_all_instruments() -> List[InstrumentConfig]:
    """Get all available instruments"""
    try:
        return instrument_registry.get_all_instruments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch instruments: {str(e)}")

@router.get("/sectors")
async def get_sectors():
    """Get all available sectors"""
    try:
        return {"sectors": instrument_registry.get_sectors()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sectors: {str(e)}")

@router.get("/exchanges")
async def get_exchanges():
    """Get all available exchange segments"""
    try:
        return {"exchanges": instrument_registry.get_exchange_segments()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch exchanges: {str(e)}")

@router.get("/sector/{sector}")
async def get_instruments_by_sector(sector: str) -> List[InstrumentConfig]:
    """Get instruments filtered by sector"""
    try:
        instruments = instrument_registry.get_instruments_by_sector(sector)
        return instruments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch instruments for sector: {str(e)}")

@router.get("/token/{token}")
async def get_instruments_by_token(token: str) -> List[InstrumentConfig]:
    """Get instruments by token"""
    try:
        instruments = instrument_registry.get_by_token(token)
        return instruments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch instruments for token: {str(e)}")

@router.post("/validate")
async def validate_instruments(instruments: List[dict]):
    """Validate a list of instruments for Kotak API format"""
    try:
        valid_instruments = []
        invalid_instruments = []

        for inst in instruments:
            token = inst.get('instrument_token')
            exchange = inst.get('exchange_segment')

            if not token or not exchange:
                invalid_instruments.append({
                    "instrument": inst,
                    "error": "Missing instrument_token or exchange_segment"
                })
                continue

            # Check if instrument exists in registry
            found_instruments = instrument_registry.get_by_token(token)
            if found_instruments:
                valid_instruments.append(inst)
            else:
                invalid_instruments.append({
                    "instrument": inst,
                    "error": "Instrument not found in registry"
                })

        return {
            "valid": valid_instruments,
            "invalid": invalid_instruments,
            "valid_count": len(valid_instruments),
            "invalid_count": len(invalid_instruments)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

class InstrumentSubscriptionRequest(BaseModel):
    symbols: List[str]
    exchange_segment: Optional[str] = "nse_cm"

@router.post("/format-for-subscription")
async def format_for_subscription(request: InstrumentSubscriptionRequest):
    """Convert symbol list to Kotak API subscription format"""
    try:
        instruments = []
        for symbol in request.symbols:
            instrument = instrument_registry.get_by_symbol(symbol, request.exchange_segment)
            if instrument:
                instruments.append(instrument)

        if not instruments:
            raise HTTPException(status_code=404, detail="No valid instruments found")

        formatted = format_for_kotak_api(instruments)
        return {
            "instruments": formatted,
            "count": len(formatted),
            "details": instruments
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Formatting failed: {str(e)}")

@router.get("/nifty50-subscription")
async def get_nifty50_subscription_data():
    """Get all Nifty 50 stocks formatted for subscription"""
    try:
        instruments = get_nifty50_subscription()
        return {
            "instruments": instruments,
            "count": len(instruments),
            "type": "nifty50_stocks"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Nifty 50 subscription: {str(e)}")

@router.get("/quick-subscription/{preset}")
async def get_quick_subscription(preset: str):
    """Get predefined subscription sets"""
    try:
        if preset == "nifty50":
            instruments = get_nifty50_subscription()
            return {
                "instruments": instruments,
                "count": len(instruments),
                "preset": "nifty50"
            }
        elif preset == "indices":
            indices = [
                {"instrument_token": "Nifty 50", "exchange_segment": "nse_cm"},
                {"instrument_token": "Bank Nifty", "exchange_segment": "nse_cm"}
            ]
            return {
                "instruments": indices,
                "count": len(indices),
                "preset": "indices"
            }
        elif preset == "top10":
            # Get top 10 instruments by market cap
            all_instruments = instrument_registry.get_all_instruments()
            top10 = [inst for inst in all_instruments if inst['instrument_type'] == 'equity'][:10]
            formatted = format_for_kotak_api(top10)
            return {
                "instruments": formatted,
                "count": len(formatted),
                "preset": "top10"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Preset '{preset}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preset subscription: {str(e)}")
# MCP HTTP adapter router allowing AI agents to call collector tools
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.mcp.tools import (
    mcp_search_diecasts,
    mcp_get_price_guide,
    mcp_verify_seller_trust,
    mcp_create_purchase_intent
)

router = APIRouter()

class McpToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}

@router.post("/tools/call")
async def call_mcp_tool(payload: McpToolCallRequest, db: AsyncSession = Depends(get_db)):
    # Invokes registered MCP tool for AI agents
    name = payload.tool_name
    args = payload.arguments

    if name == "search_diecasts":
        return await mcp_search_diecasts(
            query=args.get("query"),
            series=args.get("series"),
            max_price_inr=args.get("max_price_inr"),
            db=db
        )
    elif name == "get_price_guide":
        return await mcp_get_price_guide(toy_code=args.get("toy_code"), db=db)
    elif name == "verify_seller_trust":
        return await mcp_verify_seller_trust(seller_id=args.get("seller_id"), db=db)
    elif name == "create_purchase_intent":
        return await mcp_create_purchase_intent(
            listing_id=args.get("listing_id"),
            buyer_phone=args.get("buyer_phone"),
            db=db
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown tool '{name}'")

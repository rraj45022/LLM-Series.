from fastapi import FastAPI
from pydantic import BaseModel

from fastmcp import FastMCP  

# Models for inputs/outputs
class SIPInput(BaseModel):
    monthly_sip: float  # Monthly investment
    annual_return_rate: float  # % e.g. 12.0
    years: float

class SIPOutput(BaseModel):
    future_value: float
    total_invested: float
    gains: float

class LoanInput(BaseModel):
    principal: float  # Loan amount
    annual_rate: float  # % e.g. 8.5
    years: float

class LoanOutput(BaseModel):
    monthly_payment: float
    total_amount: float
    total_interest: float

# FastAPI app
app = FastAPI(title="Loan Helper MCP Server", version="1.0")

# SIP Calculator tool
@app.post("/mcp/tools/sip_calculator", response_model=SIPOutput)
async def sip_calculator(input: SIPInput):
    """Calculate SIP future value with compound interest."""
    months = input.years * 12
    monthly_rate = input.annual_return_rate / 12 / 100
    if monthly_rate == 0:
        return SIPOutput(future_value=input.monthly_sip * months, total_invested=input.monthly_sip * months, gains=0)
    future_value = input.monthly_sip * ((1 + monthly_rate)**months - 1) / monthly_rate
    total_invested = input.monthly_sip * months
    return SIPOutput(
        future_value=round(future_value, 2),
        total_invested=round(total_invested, 2),
        gains=round(future_value - total_invested, 2)
    )

# Loan Interest Calculator tool (EMI)
@app.post("/mcp/tools/loan_calculator", response_model=LoanOutput)
async def loan_calculator(input: LoanInput):
    """Calculate loan EMI, total payment, and interest."""
    monthly_rate = input.annual_rate / 12 / 100
    months = input.years * 12
    if monthly_rate == 0:
        monthly_payment = input.principal / months
        return LoanOutput(monthly_payment=round(monthly_payment, 2), total_amount=input.principal, total_interest=0)
    monthly_payment = (input.principal * monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
    total_amount = monthly_payment * months
    total_interest = total_amount - input.principal
    return LoanOutput(
        monthly_payment=round(monthly_payment, 2),
        total_amount=round(total_amount, 2),
        total_interest=round(total_interest, 2)
    )



# MCP integration
mcp = FastMCP.from_fastapi(app=app, name="Loan Helper MCP")

# Add MCP tools endpoint
@app.get("/mcp/tools")
async def get_mcp_tools():
    return [
        {
            "name": "sip_calculator",
            "description": "Calculate SIP future value with compound interest.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "monthly_sip": {"type": "number", "description": "Monthly investment"},
                    "annual_return_rate": {"type": "number", "description": "Annual return rate in %"},
                    "years": {"type": "number", "description": "Number of years"}
                },
                "required": ["monthly_sip", "annual_return_rate", "years"]
            }
        },
        {
            "name": "loan_calculator",
            "description": "Calculate loan EMI, total payment, and interest.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "principal": {"type": "number", "description": "Loan amount"},
                    "annual_rate": {"type": "number", "description": "Annual interest rate in %"},
                    "years": {"type": "number", "description": "Number of years"}
                },
                "required": ["principal", "annual_rate", "years"]
            }
        }
    ]

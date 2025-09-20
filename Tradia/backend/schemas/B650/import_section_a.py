from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date
import json

class B650SectionAHeader(BaseModel):
    import_declaration_type: Optional[str] = Field(None, description="Type of import declaration")
    owner_name: Optional[str] = Field(None, description="Name of the owner")
    owner_id: Optional[str] = Field(None, description="Owner identification number")
    owner_reference: Optional[str] = Field(None, description="Owner reference number")
    aqis_inspection_location: Optional[str] = Field(None, description="AQIS inspection location")
    contact_details: Optional[dict] = Field(None, description="Contact details (email/phone) as JSON object")
    destination_port_code: Optional[str] = Field(None, description="Destination port code")
    invoice_term_type: Optional[str] = Field(None, description="Invoice term type (FOB, CIF, etc.)")
    valuation_date: Optional[date] = Field(None, description="Valuation date in YYYY-MM-DD format")
    header_valuation_advice_number: Optional[str] = Field(None, description="Header valuation advice number")
    valuation_elements: Optional[dict] = Field(None, description="Valuation elements description")
    fob_or_cif: Optional[Literal["FOB", "CIF"]] = Field(None, description="FOB or CIF indicator")
    paid_under_protest: Optional[Literal["Yes", "No"]] = Field(None, description="Paid under protest indicator")
    amber_statement_reason: Optional[str] = Field(None, description="Amber statement reason")
    declaration_signature: Optional[str] = Field(None, description="Declaration signature")


class B650SectionAResponse(BaseModel):
    header: B650SectionAHeader


# Example usage
# example_data = {
#     "header": {
#         "import_declaration_type": "Standard",
#         "owner_name": "John Doe",
#         "owner_id": "123456789",
#         "destination_port_code": "SYD",
#         "invoice_term_type": "FOB",
#         "valuation_date": "2025-09-14",
#         "fob_or_cif": "FOB",
#         "paid_under_protest": "No",
#         "declaration_signature": "John Doe Signature"
#     }
# }

# obj = B650SectionAResponse(**example_data)

# Output JSON with null values for missing fields
# json_str = obj.json(indent=2, exclude_none=False)
# print(json_str)

# # Alternative: using json.dumps
# print(json.dumps(obj.dict(exclude_none=False), indent=2, default=str))

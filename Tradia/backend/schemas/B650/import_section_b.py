from typing import Optional
from pydantic import BaseModel, Field

class SectionB(BaseModel):
    # SEA specific
    vessel_id: Optional[str] = Field(None, description="Vessel identifier")
    cargo_type: Optional[str] = Field(None, description="Type of cargo")
    line_number: Optional[str] = Field(None, description="Line number")
    vessel_name: Optional[str] = Field(None, description="Vessel name")
    gross_weight: Optional[str] = Field(None, description="Gross weight of cargo")
    loading_port: Optional[str] = Field(None, description="Port of loading")
    voyage_number: Optional[str] = Field(None, description="Voyage number")
    discharge_port: Optional[str] = Field(None, description="Port of discharge")
    container_number: Optional[str] = Field(None, description="Container number")
    gross_weight_unit: Optional[str] = Field(None, description="Unit of gross weight (e.g., kg, tons)")
    mode_of_transport: Optional[str] = Field(None, description="Mode of transport (AIR | SEA | POST | OTHER)")
    first_arrival_date: Optional[str] = Field(None, description="Date of first arrival")
    first_arrival_port: Optional[str] = Field(None, description="Port of first arrival")
    number_of_packages: Optional[str] = Field(None, description="Number of packages")
    house_bill_of_lading_no: Optional[str] = Field(None, description="House bill of lading number")
    ocean_bill_of_lading_no: Optional[str] = Field(None, description="Ocean bill of lading number")
    marks_numbers_description: Optional[str] = Field(None, description="Marks and numbers description (address or identifiers)")

    # AIR specific
    airline_code: Optional[str] = Field(None, description="Airline code")
    master_air_waybill: Optional[str] = Field(None, description="Master Air Waybill number")
    house_air_waybill: Optional[str] = Field(None, description="House Air Waybill number")

    # POST specific
    parcel_post_card_numbers: Optional[str] = Field(None, description="Parcel post card numbers")

    # OTHER specific
    department_receipt_for_goods_number: Optional[str] = Field(None, description="Department receipt for goods number")

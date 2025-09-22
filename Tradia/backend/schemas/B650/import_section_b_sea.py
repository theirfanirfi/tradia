from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date


class SeaTransportLine(BaseModel):
    vessel_name: Optional[str] = Field(None, description="Vessel name")
    vessel_id: Optional[str] = Field(None, description="Vessel identification")
    voyage_number: Optional[str] = Field(None, description="Voyage number")
    loading_port: Optional[str] = Field(None, description="Loading port code")
    first_arrival_port: Optional[str] = Field(None, description="First arrival port code")
    discharge_port: Optional[str] = Field(None, description="Discharge port code")
    first_arrival_date: Optional[date] = Field(None, description="First arrival date in YYYY-MM-DD format")
    gross_weight: Optional[str] = Field(None, description="Gross weight as string")
    gross_weight_unit: Optional[str] = Field(None, description="Gross weight unit (kg, lbs, etc.)")
    line_number: Optional[str] = Field(None, description="Line number")
    cargo_type: Optional[str] = Field(None, description="Type of cargo")
    container_number: Optional[str] = Field(None, description="Container number")
    ocean_bill_of_lading_no: Optional[str] = Field(None, description="Ocean bill of lading number")
    house_bill_of_lading_no: Optional[str] = Field(None, description="House bill of lading number")
    number_of_packages: Optional[str] = Field(None, description="Number of packages")
    marks_numbers_description: Optional[str] = Field(None, description="Marks and numbers description")
    mode_of_transport: Optional[str] = Field("SEA", description="Mode of transport")


class B650SectionBSeaResponseFormat(BaseModel):
    sea_transport_lines: List[SeaTransportLine]

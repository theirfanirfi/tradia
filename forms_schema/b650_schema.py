from typing import Optional, List
from pydantic import BaseModel

class HeaderSection(BaseModel):
    import_declaration_type: str
    owner_name: str
    owner_id: str
    owner_reference: Optional[str] = None
    aqis_inspection_location: Optional[str] = None
    contact_details: Optional[str] = None
    destination_port_code: str
    invoice_term_type: str
    valuation_date: str
    header_valuation_advice_number: Optional[str] = None
    valuation_elements: Optional[str] = None
    fob_or_cif: Optional[str] = None
    paid_under_protest: Optional[str] = None
    amber_statement_reason: Optional[str] = None
    declaration_signature: Optional[str] = None

class AirTransportLine(BaseModel):
    airline_code: Optional[str] = None
    loading_port: str
    first_arrival_port: str
    discharge_port: str
    first_arrival_date: Optional[str] = None
    gross_weight: str
    gross_weight_unit: str
    line_number: Optional[str] = None
    master_air_waybill_no: str
    house_air_waybill_no: Optional[str] = None
    number_of_packages: Optional[str] = None
    marks_numbers_description: Optional[str] = None

class SeaTransportLine(BaseModel):
    vessel_name: Optional[str] = None
    vessel_id: Optional[str] = None
    voyage_number: Optional[str] = None
    loading_port: str
    first_arrival_port: str
    discharge_port: str
    first_arrival_date: Optional[str] = None
    gross_weight: str
    gross_weight_unit: str
    line_number: Optional[str] = None
    cargo_type: Optional[str] = None
    container_number: Optional[str] = None
    ocean_bill_of_lading_no: Optional[str] = None
    house_bill_of_lading_no: Optional[str] = None
    number_of_packages: Optional[str] = None
    marks_numbers_description: Optional[str] = None

class TariffLine(BaseModel):
    tariff_classification: Optional[str] = None
    goods_description: str
    quantity: float
    unit_of_measure: str
    country_of_origin: str
    customs_value: Optional[str] = None
    fob_value: Optional[str] = None
    cif_value: Optional[str] = None
    origin_country_code: Optional[str] = None
    preference_rule_type: Optional[str] = None
    preference_scheme_type: Optional[str] = None
    tariff_instrument: Optional[str] = None
    additional_information: Optional[str] = None
    tariff_classification_code: Optional[str] = None

class B650Model(BaseModel):
    header: HeaderSection
    air_transport_lines: Optional[List[AirTransportLine]] = None
    sea_transport_lines: Optional[List[SeaTransportLine]] = None
    tariff_lines: Optional[List[TariffLine]] = None

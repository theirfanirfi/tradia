from typing import Optional, List
from pydantic import BaseModel, Field, constr


class SECTIONC(BaseModel):
    quantity: Optional[str] = Field(None, description="Quantity of goods")
    cif_value: Optional[str] = Field(None, description="CIF value")
    fob_value: Optional[str] = Field(None, description="FOB value")
    customs_value: Optional[str] = Field(None, description="Customs value")
    unit_of_measure: Optional[str] = Field(None, description="Unit of measure (e.g., KGS, LBS)")
    country_of_origin: Optional[str] = Field(None, description="Country of origin")
    goods_description: Optional[str] = Field(None, description="Goods description")
    tariff_instrument: Optional[str] = Field(None, description="Tariff instrument")
    origin_country_code: Optional[str] = Field(None, description="Origin country code")
    preference_rule_type: Optional[str] = Field(None, description="Preference rule type")
    tariff_classification: Optional[str] = Field(None, description="Tariff classification (raw value)")
    additional_information: Optional[str] = Field(None, description="Additional information")
    preference_scheme_type: Optional[str] = Field(None, description="Preference scheme type")
    tariff_classification_code: Optional[str] = Field(None, description="Tariff classification code")

    # passthrough fields
    supplier_id: Optional[str] = Field(None, description="Supplier ID")
    supplier_name: Optional[str] = Field(None, description="Supplier name")
    vendor_id: Optional[str] = Field(None, description="Vendor ID")
    stat_code: Optional[str] = Field(None, description="Statistical code")
    valuation_basis_type: Optional[str] = Field(None, description="Valuation basis type")
    treatment_code: Optional[str] = Field(None, description="Treatment code")
    gst_exemption_code: Optional[str] = Field(None, description="GST exemption code")
    establishment_code: Optional[str] = Field(None, description="Establishment code")
    price_type: Optional[str] = Field(None, description="Price type (CIF, FOB, CUSTOMS)")
    price_amount: Optional[str] = Field(None, description="Price amount")
    price_currency: Optional[str] = Field(None, description="Price currency, e.g. AUD")
    permit_number: Optional[str] = Field(None, description="Permit number")
    preference_origin_country: Optional[str] = Field(None, description="Preference origin country")
    instrument_type1: Optional[str] = Field(None, description="Instrument type 1")
    instrument_number1: Optional[str] = Field(None, description="Instrument number 1")
    instrument_type2: Optional[str] = Field(None, description="Instrument type 2")
    instrument_number2: Optional[str] = Field(None, description="Instrument number 2")
    producer_code: Optional[str] = Field(None, description="Producer code")

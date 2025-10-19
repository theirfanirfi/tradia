import re
import spacy
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

@dataclass
class B650ExtractedData:
    """Structured data matching B650 form fields"""
    
    # Section A - Owner Details
    owner_name: Optional[str] = None
    owner_id: Optional[str] = None  # ABN, ABN/CAC or CCID
    owner_reference: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_fax: Optional[str] = None
    owner_email: Optional[str] = None
    
    # Valuation Information
    valuation_date: Optional[str] = None
    invoice_term_type: Optional[str] = None  # FOB, CIF, etc.
    valuation_elements: Dict[str, Dict[str, Any]] = None
    
    # Section B - Transport Details
    mode_of_transport: Optional[str] = None  # AIR, SEA, POST, OTHER
    
    # Air transport fields
    airline_code: Optional[str] = None
    master_air_waybill: Optional[str] = None
    house_air_waybill: Optional[str] = None
    
    # Sea transport fields
    vessel_name: Optional[str] = None
    vessel_id: Optional[str] = None
    voyage_number: Optional[str] = None
    container_number: Optional[str] = None
    ocean_bill_of_lading: Optional[str] = None
    house_bill_of_lading: Optional[str] = None
    cargo_type: Optional[str] = None
    
    # Post transport fields
    parcel_post_card_numbers: List[str] = None
    
    # Other transport fields
    department_receipt_number: Optional[str] = None
    
    # Common transport fields
    loading_port: Optional[str] = None
    first_arrival_port: Optional[str] = None
    discharge_port: Optional[str] = None
    first_arrival_date: Optional[str] = None
    gross_weight: Optional[str] = None
    gross_weight_unit: Optional[str] = None
    number_of_packages: Optional[str] = None
    marks_and_numbers: Optional[str] = None
    
    # Delivery Address
    delivery_name: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_locality: Optional[str] = None
    delivery_state: Optional[str] = None
    delivery_postcode: Optional[str] = None
    delivery_country: Optional[str] = None
    delivery_phone: Optional[str] = None
    
    # Section C - Goods/Tariff Details
    goods_description: List[str] = None
    supplier_name: Optional[str] = None
    supplier_id: Optional[str] = None  # CCID/ABN
    vendor_id: Optional[str] = None   # ABN/ARN
    tariff_classification: Optional[str] = None
    origin_country: Optional[str] = None
    preference_origin_country: Optional[str] = None
    price_amount: Optional[str] = None
    price_currency: Optional[str] = None
    quantity: Optional[str] = None
    quantity_unit: Optional[str] = None
    permit_numbers: List[str] = None

class B650InvoicePreprocessor:
    def __init__(self):
        # Load spaCy model for NER
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except IOError:
            print("Please install spaCy English model: python -m spacy download en_core_web_sm")
            raise
        
        # Transport mode patterns with B650 specific categories
        self.transport_patterns = {
            'SEA': [
                r'(?i)\b(sea\s*freight|ocean\s*freight|vessel|ship|port\s*of\s*loading|port\s*of\s*discharge|by\s*sea|maritime)\b',
                r'(?i)\b(container|fcl|lcl|bill\s*of\s*lading|bl\s*no|b/l|ocean\s*freight|sea\s*cargo)\b',
                r'(?i)\b(vessel\s*name|voyage|container\s*number)\b'
            ],
            'AIR': [
                r'(?i)\b(air\s*freight|airway\s*bill|awb|by\s*air|airport|flight|cargo\s*plane)\b',
                r'(?i)\b(air\s*transport|aviation|airline|master\s*air\s*waybill|house\s*air\s*waybill)\b'
            ],
            'POST': [
                r'(?i)\b(postal|post\s*office|mail|parcel\s*post|registered\s*mail|parcel\s*card)\b'
            ],
            'OTHER': [
                r'(?i)\b(road\s*transport|truck|rail|train|courier|express|dhl|fedex|ups|land\s*transport)\b'
            ]
        }
        
        # Invoice terms (Incoterms)
        self.incoterms_patterns = [
            r'(?i)\b(FOB|Free\s*on\s*Board)\b',
            r'(?i)\b(CIF|Cost\s*Insurance\s*and\s*Freight)\b',
            r'(?i)\b(CFR|Cost\s*and\s*Freight)\b',
            r'(?i)\b(EXW|Ex\s*Works)\b',
            r'(?i)\b(DDP|Delivered\s*Duty\s*Paid)\b',
            r'(?i)\b(DAP|Delivered\s*at\s*Place)\b',
            r'(?i)\b(FCA|Free\s*Carrier)\b'
        ]
        
        # Australian Business Number (ABN) pattern
        self.abn_pattern = r'\b(?:ABN[:\s]*)?(\d{2}\s*\d{3}\s*\d{3}\s*\d{3})\b'
        
        # Phone number patterns (Australian format)
        self.phone_patterns = [
            r'(?i)(?:phone|ph|tel|mobile|mob)[:\s]*([+]?[\d\s\(\)\-]{10,15})',
            r'(?i)(?:fax)[:\s]*([+]?[\d\s\(\)\-]{10,15})'
        ]
        
        # Email pattern
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Port patterns (enhanced for B650)
        self.port_patterns = {
            'loading': [
                r'(?i)port\s*of\s*loading[:\s]*([^\n\r,;]+)',
                r'(?i)loading\s*port[:\s]*([^\n\r,;]+)',
                r'(?i)origin\s*port[:\s]*([^\n\r,;]+)',
                r'(?i)departure\s*port[:\s]*([^\n\r,;]+)'
            ],
            'discharge': [
                r'(?i)port\s*of\s*discharge[:\s]*([^\n\r,;]+)',
                r'(?i)discharge\s*port[:\s]*([^\n\r,;]+)',
                r'(?i)destination\s*port[:\s]*([^\n\r,;]+)',
                r'(?i)arrival\s*port[:\s]*([^\n\r,;]+)'
            ],
            'first_arrival': [
                r'(?i)first\s*arrival\s*port[:\s]*([^\n\r,;]+)',
                r'(?i)first\s*port\s*of\s*call[:\s]*([^\n\r,;]+)'
            ]
        }
        
        # Transport document patterns
        self.transport_doc_patterns = {
            'bill_of_lading': [
                r'(?i)(?:ocean\s*)?bill\s*of\s*lading\s*(?:no|number)?[:\s#]*([A-Za-z0-9\-\/]+)',
                r'(?i)(?:house\s*)?b/?l\s*(?:no|number)?[:\s#]*([A-Za-z0-9\-\/]+)',
                r'(?i)ocean\s*bl[:\s#]*([A-Za-z0-9\-\/]+)'
            ],
            'air_waybill': [
                r'(?i)(?:master\s*)?air\s*way\s*bill\s*(?:no|number)?[:\s#]*([A-Za-z0-9\-\/]+)',
                r'(?i)(?:house\s*)?awb\s*(?:no|number)?[:\s#]*([A-Za-z0-9\-\/]+)',
                r'(?i)mawb[:\s#]*([A-Za-z0-9\-\/]+)',
                r'(?i)hawb[:\s#]*([A-Za-z0-9\-\/]+)'
            ],
            'container': [
                r'(?i)container\s*(?:no|number)?[:\s#]*([A-Za-z0-9\-\/]+)',
                r'(?i)cntr\s*(?:no|number)?[:\s#]*([A-Za-z0-9\-\/]+)'
            ],
            'vessel': [
                r'(?i)vessel\s*name[:\s]*([^\n\r,;]+)',
                r'(?i)vessel\s*id[:\s]*([A-Za-z0-9\-\/]+)',
                r'(?i)voyage\s*(?:no|number)?[:\s#]*([A-Za-z0-9\-\/]+)'
            ]
        }
        
        # Weight and quantity patterns
        self.weight_patterns = [
            r'(?i)gross\s*weight[:\s]*(\d+(?:\.\d+)?)\s*(kg|kgs|kilogram|pound|lb|ton|tonnes?)',
            r'(?i)weight[:\s]*(\d+(?:\.\d+)?)\s*(kg|kgs|kilogram|pound|lb|ton|tonnes?)',
            r'(?i)(\d+(?:\.\d+)?)\s*(kg|kgs|kilogram|pound|lb|ton|tonnes?)'
        ]
        
        self.quantity_patterns = [
            r'(?i)quantity[:\s]*(\d+(?:\.\d+)?)\s*(pcs?|pieces?|units?|cartons?|boxes?|cases?)',
            r'(?i)qty[:\s]*(\d+(?:\.\d+)?)\s*(pcs?|pieces?|units?|cartons?|boxes?|cases?)',
            r'(?i)(\d+)\s*(?:pcs?|pieces?|units?|cartons?|boxes?|cases?)'
        ]
        
        # Valuation elements patterns (for B650 Section A)
        self.valuation_patterns = {
            'invoice_total': [
                r'(?i)(?:invoice\s*)?total[:\s]*([A-Z]{3})?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'(?i)amount[:\s]*([A-Z]{3})?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
            ],
            'freight': [
                r'(?i)freight[:\s]*([A-Z]{3})?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'(?i)shipping[:\s]*([A-Z]{3})?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
            ],
            'insurance': [
                r'(?i)insurance[:\s]*([A-Z]{3})?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
            ],
            'packing': [
                r'(?i)packing[:\s]*([A-Z]{3})?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
            ]
        }
        
        # Date patterns
        self.date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',  # DD/MM/YYYY
            r'\b(\d{2,4}[/-]\d{1,2}[/-]\d{1,2})\b',  # YYYY/MM/DD
            r'\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})\b',
            r'\b((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})\b'
        ]

    def extract_owner_details(self, text: str) -> Dict[str, str]:
        """Extract owner details for B650 Section A"""
        owner_details = {}
        
        # Extract ABN
        abn_match = re.search(self.abn_pattern, text, re.IGNORECASE)
        if abn_match:
            owner_details['owner_id'] = abn_match.group(1).replace(' ', '')
        
        # Extract phone numbers
        for pattern in self.phone_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                field_type = match.group(0).lower()
                phone_number = match.group(1).strip()
                if 'fax' in field_type:
                    owner_details['owner_fax'] = phone_number
                elif 'mobile' in field_type or 'mob' in field_type:
                    owner_details['owner_phone'] = phone_number
                else:
                    owner_details['owner_phone'] = phone_number
        
        # Extract email
        email_match = re.search(self.email_pattern, text)
        if email_match:
            owner_details['owner_email'] = email_match.group(0)
        
        return owner_details

    def extract_valuation_elements(self, text: str) -> Dict[str, Dict[str, str]]:
        """Extract valuation elements for B650 Section A"""
        valuation_elements = {}
        
        for element_type, patterns in self.valuation_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    currency = match.group(1) if match.group(1) else 'USD'
                    amount = match.group(2).replace(',', '')
                    
                    valuation_elements[element_type] = {
                        'amount': amount,
                        'currency': currency
                    }
                    break  # Take first match for each type
        
        return valuation_elements

    def extract_transport_mode(self, text: str) -> str:
        """Extract mode of transport (SEA, AIR, POST, OTHER)"""
        scores = {}
        for mode, patterns in self.transport_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text)
                score += len(matches)
            scores[mode] = score
        
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return None

    def extract_transport_details(self, text: str, transport_mode: str) -> Dict[str, str]:
        """Extract transport-specific details based on mode"""
        details = {}
        
        # Extract ports
        for port_type, patterns in self.port_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    details[f'{port_type}_port'] = match.group(1).strip()
                    break
        
        # Extract transport documents
        if transport_mode == 'SEA':
            # Bill of lading
            for pattern in self.transport_doc_patterns['bill_of_lading']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if 'house' in match.group(0).lower():
                        details['house_bill_of_lading'] = match.group(1)
                    else:
                        details['ocean_bill_of_lading'] = match.group(1)
            
            # Container and vessel details
            for pattern in self.transport_doc_patterns['container']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    details['container_number'] = match.group(1)
                    break
            
            for pattern in self.transport_doc_patterns['vessel']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if 'name' in match.group(0).lower():
                        details['vessel_name'] = match.group(1).strip()
                    elif 'id' in match.group(0).lower():
                        details['vessel_id'] = match.group(1)
                    elif 'voyage' in match.group(0).lower():
                        details['voyage_number'] = match.group(1)
        
        elif transport_mode == 'AIR':
            # Air waybill
            for pattern in self.transport_doc_patterns['air_waybill']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if 'house' in match.group(0).lower() or 'hawb' in match.group(0).lower():
                        details['house_air_waybill'] = match.group(1)
                    else:
                        details['master_air_waybill'] = match.group(1)
        
        # Extract weight and quantity
        weight_match = re.search(self.weight_patterns[0], text, re.IGNORECASE)
        if weight_match:
            details['gross_weight'] = weight_match.group(1)
            details['gross_weight_unit'] = weight_match.group(2).upper()
        
        quantity_match = re.search(self.quantity_patterns[0], text, re.IGNORECASE)
        if quantity_match:
            details['number_of_packages'] = quantity_match.group(1)
        
        return details

    def extract_delivery_address(self, text: str) -> Dict[str, str]:
        """Extract delivery address details"""
        doc = self.nlp(text)
        address_info = {}
        
        # Look for "delivery", "ship to", "consignee" sections
        delivery_patterns = [
            r'(?i)(?:delivery|ship\s*to|consignee|deliver\s*to)[:\s]*([^\n\r]+?)(?=\n\s*[A-Z]|\n\s*\n|\r|$)',
            r'(?i)address[:\s]*([^\n\r]+?)(?=\n\s*[A-Z]|\n\s*\n|\r|$)'
        ]
        
        for pattern in delivery_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                address_text = match.group(1).strip()
                
                # Extract Australian postcode
                postcode_match = re.search(r'\b(\d{4})\b', address_text)
                if postcode_match:
                    address_info['delivery_postcode'] = postcode_match.group(1)
                
                # Extract state abbreviations
                state_match = re.search(r'\b(NSW|VIC|QLD|WA|SA|TAS|NT|ACT)\b', address_text, re.IGNORECASE)
                if state_match:
                    address_info['delivery_state'] = state_match.group(1).upper()
                
                address_info['delivery_address'] = address_text
                break
        
        return address_info

    def extract_goods_details(self, text: str) -> Dict[str, Any]:
        """Extract goods description and related details"""
        goods_info = {}
        
        # Extract goods description
        goods_patterns = [
            r'(?i)(?:goods?\s*description|description\s*of\s*goods?|commodity)[:\s]*([^\n\r]+)',
            r'(?i)product[:\s]*([^\n\r]+)',
            r'(?i)item[:\s]*([^\n\r]+)'
        ]
        
        descriptions = []
        for pattern in goods_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                desc = match.group(1).strip()
                if len(desc) > 5:  # Filter out very short matches
                    descriptions.append(desc)
        
        if descriptions:
            goods_info['goods_description'] = list(set(descriptions))
        
        # Extract origin country
        country_patterns = [
            r'(?i)(?:country\s*of\s*origin|origin)[:\s]*([A-Za-z\s]+?)(?=\n|\r|$|\s{2,})',
            r'(?i)made\s*in[:\s]*([A-Za-z\s]+?)(?=\n|\r|$|\s{2,})'
        ]
        
        for pattern in country_patterns:
            match = re.search(pattern, text)
            if match:
                goods_info['origin_country'] = match.group(1).strip()
                break
        
        return goods_info

    def extract_invoice_terms(self, text: str) -> Optional[str]:
        """Extract Incoterms (FOB, CIF, etc.)"""
        for pattern in self.incoterms_patterns:
            match = re.search(pattern, text)
            if match:
                term = match.group(0).upper()
                # Normalize common variations
                if 'FREE ON BOARD' in term:
                    return 'FOB'
                elif 'COST INSURANCE AND FREIGHT' in term:
                    return 'CIF'
                elif 'COST AND FREIGHT' in term:
                    return 'CFR'
                else:
                    return term
        return None

    def extract_dates(self, text: str) -> Dict[str, str]:
        """Extract various dates from text"""
        dates = {}
        
        date_fields = {
            'invoice_date': [r'(?i)invoice\s*date[:\s]*([^\n\r]+)'],
            'shipping_date': [r'(?i)(?:ship|dispatch|departure)\s*date[:\s]*([^\n\r]+)'],
            'arrival_date': [r'(?i)(?:arrival|eta|delivery)\s*date[:\s]*([^\n\r]+)'],
            'valuation_date': [r'(?i)valuation\s*date[:\s]*([^\n\r]+)']
        }
        
        for date_type, patterns in date_fields.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    date_str = match.group(1).strip()
                    if self._validate_date_string(date_str):
                        dates[date_type] = date_str
                        break
        
        return dates

    def _validate_date_string(self, date_str: str) -> bool:
        """Validate if string looks like a date"""
        if len(date_str.strip()) < 6:
            return False
        
        # Check if it matches common date patterns
        for pattern in self.date_patterns:
            if re.search(pattern, date_str, re.IGNORECASE):
                return True
        
        return False

    def extract_companies(self, text: str) -> Dict[str, str]:
        """Extract company names using NER and patterns"""
        doc = self.nlp(text)
        companies = {}
        
        # Company role patterns
        company_patterns = {
            'exporter': [
                r'(?i)(?:exporter|shipper|consignor|seller)[:\s]*([^\n\r]+?)(?=\n\s*[A-Z]|\n\s*\n|\r|$)',
            ],
            'importer': [
                r'(?i)(?:importer|consignee|buyer|purchaser)[:\s]*([^\n\r]+?)(?=\n\s*[A-Z]|\n\s*\n|\r|$)',
            ],
            'supplier': [
                r'(?i)(?:supplier|vendor)[:\s]*([^\n\r]+?)(?=\n\s*[A-Z]|\n\s*\n|\r|$)',
            ]
        }
        
        for role, patterns in company_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.MULTILINE)
                if match:
                    company_name = match.group(1).strip()
                    if len(company_name) > 3:
                        companies[role] = company_name
                        break
        
        return companies

    def process(self, invoice_text: str) -> B650ExtractedData:
        """Main processing function that extracts all B650-relevant information"""
        extracted = B650ExtractedData()
        
        # Extract owner details (Section A)
        owner_details = self.extract_owner_details(invoice_text)
        for key, value in owner_details.items():
            setattr(extracted, key, value)
        
        # Extract companies
        companies = self.extract_companies(invoice_text)
        extracted.owner_name = companies.get('importer') or companies.get('consignee')
        extracted.supplier_name = companies.get('exporter') or companies.get('supplier')
        
        # Extract valuation information
        extracted.valuation_elements = self.extract_valuation_elements(invoice_text)
        extracted.invoice_term_type = self.extract_invoice_terms(invoice_text)
        
        # Extract dates
        dates = self.extract_dates(invoice_text)
        extracted.valuation_date = dates.get('valuation_date') or dates.get('invoice_date')
        extracted.first_arrival_date = dates.get('arrival_date') or dates.get('shipping_date')
        
        # Extract transport details (Section B)
        extracted.mode_of_transport = self.extract_transport_mode(invoice_text)
        
        if extracted.mode_of_transport:
            transport_details = self.extract_transport_details(invoice_text, extracted.mode_of_transport)
            for key, value in transport_details.items():
                if hasattr(extracted, key):
                    setattr(extracted, key, value)
        
        # Extract delivery address
        delivery_details = self.extract_delivery_address(invoice_text)
        for key, value in delivery_details.items():
            setattr(extracted, key, value)
        
        # Extract goods details (Section C)
        goods_details = self.extract_goods_details(invoice_text)
        for key, value in goods_details.items():
            setattr(extracted, key, value)
        
        return extracted

    def to_b650_structure(self, extracted_data: B650ExtractedData) -> Dict[str, Any]:
        """Convert extracted data to B650 form structure"""
        return {
            "section_a_owner_details": {
                "owner_name": extracted_data.owner_name,
                "owner_id": extracted_data.owner_id,
                "owner_reference": extracted_data.owner_reference,
                "contact_details": {
                    "phone": extracted_data.owner_phone,
                    "fax": extracted_data.owner_fax,
                    "email": extracted_data.owner_email
                },
                "valuation_date": extracted_data.valuation_date,
                "invoice_term_type": extracted_data.invoice_term_type,
                "valuation_elements": extracted_data.valuation_elements
            },
            "section_b_transport_details": {
                "mode_of_transport": extracted_data.mode_of_transport,
                "air_transport": {
                    "airline_code": extracted_data.airline_code,
                    "master_air_waybill": extracted_data.master_air_waybill,
                    "house_air_waybill": extracted_data.house_air_waybill
                } if extracted_data.mode_of_transport == 'AIR' else None,
                "sea_transport": {
                    "vessel_name": extracted_data.vessel_name,
                    "vessel_id": extracted_data.vessel_id,
                    "voyage_number": extracted_data.voyage_number,
                    "container_number": extracted_data.container_number,
                    "ocean_bill_of_lading": extracted_data.ocean_bill_of_lading,
                    "house_bill_of_lading": extracted_data.house_bill_of_lading,
                    "cargo_type": extracted_data.cargo_type
                } if extracted_data.mode_of_transport == 'SEA' else None,
                "common_fields": {
                    "loading_port": extracted_data.loading_port,
                    "first_arrival_port": extracted_data.first_arrival_port,
                    "discharge_port": extracted_data.discharge_port,
                    "first_arrival_date": extracted_data.first_arrival_date,
                    "gross_weight": extracted_data.gross_weight,
                    "gross_weight_unit": extracted_data.gross_weight_unit,
                    "number_of_packages": extracted_data.number_of_packages,
                    "marks_and_numbers": extracted_data.marks_and_numbers
                },
                "delivery_address": {
                    "name": extracted_data.delivery_name,
                    "address": extracted_data.delivery_address,
                    "locality": extracted_data.delivery_locality,
                    "state": extracted_data.delivery_state,
                    "postcode": extracted_data.delivery_postcode,
                    "country": extracted_data.delivery_country or "AUSTRALIA",
                    "phone": extracted_data.delivery_phone
                }
            },
            "section_c_tariff_details": {
                "goods_description": extracted_data.goods_description,
                "supplier_name": extracted_data.supplier_name,
                "supplier_id": extracted_data.supplier_id,
                "vendor_id": extracted_data.vendor_id,
                "tariff_classification": extracted_data.tariff_classification,
                "origin_country": extracted_data.origin_country,
                "preference_origin_country": extracted_data.preference_origin_country,
                "price": {
                    "amount": extracted_data.price_amount,
                    "currency": extracted_data.price_currency
                },
                "quantity": {
                    "value": extracted_data.quantity,
                    "unit": extracted_data.quantity_unit
                },
                "permit_numbers": extracted_data.permit_numbers
            }
        }


def filter_none_values(data):
    """Recursively filters out None values, empty dictionaries, and empty lists."""
    if isinstance(data, dict):
        # Recursively filter dictionary values
        filtered_dict = {k: filter_none_values(v) for k, v in data.items() if v is not None}
        # Remove keys with empty dictionary or list values after filtering
        return {k: v for k, v in filtered_dict.items() if v != {} and v != []}
    elif isinstance(data, list):
        # Recursively filter list items
        filtered_list = [filter_none_values(item) for item in data if item is not None]
        # Remove empty dictionaries or lists from the filtered list
        return [item for item in filtered_list if item != {} and item != []]
    else:
        return data



def b650_preprocessor(text: str):
    # Initialize preprocessor
    preprocessor = B650InvoicePreprocessor()

    # Process the invoice
    result = preprocessor.process(text)
    b650_structure = preprocessor.to_b650_structure(result)
    filtered_b650_structure = filter_none_values(b650_structure)
    return filtered_b650_structure


# Example usage
# if __name__ == "__main__":
sample_invoice = """
   YANTAIRIMAMACHINERYCO.,LTD.XIBEIYUINDUSTRY SHBNE250400002
ZONE,LAIZHOU,SHANDONG,CHINA
TEL/FAX:+86-535-6805690
AHG0233130P08
BRADLEYTHOMAS
ADDRESS:25MOLLERST,GORDONVALEQLD4865
AUSTRALIA
TEL:0481042746
EMAIL:
BRADLEY@THOMASARBORICULTURE.COM.AU
ASEA360CONSOLIDATIONPTYLTD
SAMEASCONSIGNEE
9/2TULLAMARINEPARKROAD,TULLAMARINEVIC3043
POBOX659,TULLAMARINEVIC3043
TEL:+61383460166
FAX:+61393387447
ANLGIPPSLAND 082S SHANGHAI,CHINA
BRISBANE,AUSTRALIA BRISBANE,AUSTRALIA
1PKGS SAIDTOCONTAIN 237KGS 0.92CBM
GRAPPLE
YT250305-07 HYDRAULICROTATOR
SEGU9412081/M1429568 40NOR
CFS-CFS
FREIGHTPREPAID
OCEANFREIGHT ASARRANGED
SAYTOTAL:ONEPKGSONLY
SHANGHAI MAY04,2025
SHANGHAI

[OCR Text]
Werd World Jaguar Logistics Inc.
COMBINED TRANSPORT BILL OF LADING

Shipper

YANTAI RIMA MACHINERY CO., LTD, XIBETYU INDUSTRY DOC No: SHBNE250400002
ZONE, LAIZHOU, SHANDONG, CHINA ae
TEL/FAX:+86-535-6805690

B/L No: AHG0233130P08

ensignee
RADLEYTHOMAS
DDRESS : 25 MOLLER ST, GORDONVALE QLD 4865

cst COPY
EL:0481042746

MAIL:
RADLEY@THOMASARBORICULTURE.COM.AU

Peo

Bos

Notify Party(Gomplete name and address) For delivery of goods Please apply to:
SAME AS CONSIGNEE ASEA360 CONSOLIDATION PTY LTD
9/2 TULLAMARINE PARK ROAD, TULLAMARINE VIC 3043
PO BOX 659, TULLAMARINE VIC 3043
TEL: +613 8346 0166
FAX: +613 9338 7447

Place of Receipt

ANL GIPPSLAND 0825 Port SHANGHATCHINA
BRISBANE AUSTRALIA Place SRISBANE, AUSTRALIA

PARTICULARS FURNISHED BY SHIPPER

Marks and numbers No. of pkgs Description of goods Gross weight Measurement
1PKGS SAID TO CONTAIN 237KGS 0.92CBM
GRAPPLE
YT250305-07 HYDRAULIC ROTATOR,

SEGU9412081/M1429568 40NOR

CFS-CFS
FREIGHT PREPAID
FREIGHT&CHARGE REVENUE TONS RATE COLLECT
OCEAN FREIGHT ED
SAY TOTAL:ONE PKGS ONLY

The goods and instructions are accepted and dealt with subject to the Standard Conditions printed overleaf.

Taken in charge in apparent good order and condition, unless otherwise noted herein, at the place of receipt for iransport and delivery as mentioned above
One of these Combined Transport Bills of lading must be surrendered duly endorsed in exchange for the goods. In Witness whereof the original Combined.
Transport Bills of Lading all of this tenor and date have been signed in the number stated below, one of which being accomplished the other(s) to be void.

Freight amount Place and date of issue
SHANGHAI MAY 04, 2025
Freight Payable at
SHANGHAI

Cargo Insurance through the undersigned

not covered [1] Covered according to attached Polic
    """
    
    # Initialize preprocessor
preprocessor = B650InvoicePreprocessor()
    
    # # Process the invoice
    # result = preprocessor.process(sample_invoice)
    # b650_structure = preprocessor.to_b650_structure(result)
    
    # print("=" * 60)
    # print("B650 PREPROCESSED DATA")
    # print("=" * 60)
    
    # print("\nSECTION A - OWNER DETAILS:")
    # section_a = b650_structure["section_a_owner_details"]
    # print(f"Owner Name: {section_a['owner_name']}")
    # print(f"Owner ID (ABN): {section_a['owner_id']}")
    # print(f"Phone: {section_a['contact_details']['phone']}")
    # print(f"Email: {section_a['contact_details']['email']}")
    # print(f"Valuation Date: {section_a['valuation_date']}")
    # print(f"Invoice Terms: {section_a['invoice_term_type']}")
    
    # if section_a['valuation_elements']:
    #     print("\nValuation Elements:")
    #     for element, details in section_a['valuation_elements'].items():
    #         print(f"  {element}: {details['currency']} {details['amount']}")
    
    # print("\nSECTION B - TRANSPORT DETAILS:")
    # section_b = b650_structure["section_b_transport_details"]
    # print(f"Mode of Transport: {section_b['mode_of_transport']}")
    
    # common = section_b['common_fields']
    # print(f"Loading Port: {common['loading_port']}")
    # print(f"Discharge Port: {common['discharge_port']}")
    # print(f"First Arrival Date: {common['first_arrival_date']}")
    # print(f"Gross Weight: {common['gross_weight']} {common['gross_weight_unit']}")
    # print(f"Number of Packages: {common['number_of_packages']}")
    
    # if section_b['sea_transport']:
    #     sea = section_b['sea_transport']
    #     print(f"\nSea Transport Details:")
    #     print(f"  Vessel Name: {sea['vessel_name']}")
    #     print(f"  Voyage Number: {sea['voyage_number']}")
    #     print(f"  Container Number: {sea['container_number']}")
    #     print(f"  Ocean B/L: {sea['ocean_bill_of_lading']}")
    
    # delivery = section_b['delivery_address']
    # print(f"\nDelivery Address:")
    # print(f"  Address: {delivery['address']}")
    # print(f"  State: {delivery['state']}")
    # print(f"  Postcode: {delivery['postcode']}")
    # print(f"  Country: {delivery['country']}")
    
    # print("\nSECTION C - TARIFF DETAILS:")
    # section_c = b650_structure["section_c_tariff_details"]
    # print(f"Goods Description: {section_c['goods_description']}")
    # print(f"Supplier Name: {section_c['supplier_name']}")
    # print(f"Origin Country: {section_c['origin_country']}")
    
    # if section_c['price']['amount']:
    #     print(f"Price: {section_c['price']['currency']} {section_c['price']['amount']}")
    # if section_c['quantity']['value']:
    #     print(f"Quantity: {section_c['quantity']['value']} {section_c['quantity']['unit']}")
    
    # print("\n" + "=" * 60)
    # print("READY FOR LLM MAPPING TO B650 FORM")
    # print("=" * 60)
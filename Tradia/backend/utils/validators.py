import re
from typing import Dict, Any, List, Optional
from decimal import Decimal


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_currency_code(currency: str) -> bool:
    """Validate ISO 4217 currency code"""
    valid_currencies = ['AUD', 'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'CHF', 'CNY']
    return currency.upper() in valid_currencies


def validate_weight_unit(unit: str) -> bool:
    """Validate weight unit"""
    valid_units = ['kg', 'g', 'lb', 'oz', 'ton']
    return unit.lower() in valid_units


def validate_declaration_type(declaration_type: str) -> bool:
    """Validate declaration type"""
    return declaration_type.lower() in ['import', 'export']


def validate_item_data(item: Dict[str, Any]) -> List[str]:
    """Validate item data and return list of errors"""
    errors = []
    
    # Required fields
    if not item.get('item_title'):
        errors.append("Item title is required")
    
    # Optional field validations
    if 'item_weight' in item and item['item_weight'] is not None:
        try:
            weight = Decimal(str(item['item_weight']))
            if weight < 0:
                errors.append("Item weight must be positive")
        except (ValueError, TypeError):
            errors.append("Invalid item weight format")
    
    if 'item_price' in item and item['item_price'] is not None:
        try:
            price = Decimal(str(item['item_price']))
            if price < 0:
                errors.append("Item price must be positive")
        except (ValueError, TypeError):
            errors.append("Invalid item price format")
    
    if 'item_currency' in item and item['item_currency']:
        if not validate_currency_code(item['item_currency']):
            errors.append("Invalid currency code")
    
    if 'item_weight_unit' in item and item['item_weight_unit']:
        if not validate_weight_unit(item['item_weight_unit']):
            errors.append("Invalid weight unit")
    
    return errors


def validate_declaration_data(data: Dict[str, Any]) -> List[str]:
    """Validate declaration data and return list of errors"""
    errors = []
    
    # Validate basic fields
    if 'exporter_name' in data and data['exporter_name']:
        if len(data['exporter_name']) > 255:
            errors.append("Exporter name too long")
    
    if 'importer_name' in data and data['importer_name']:
        if len(data['importer_name']) > 255:
            errors.append("Importer name too long")
    
    # Validate numeric fields
    if 'total_weight' in data and data['total_weight'] is not None:
        try:
            weight = Decimal(str(data['total_weight']))
            if weight < 0:
                errors.append("Total weight must be positive")
        except (ValueError, TypeError):
            errors.append("Invalid total weight format")
    
    if 'total_value' in data and data['total_value'] is not None:
        try:
            value = Decimal(str(data['total_value']))
            if value < 0:
                errors.append("Total value must be positive")
        except (ValueError, TypeError):
            errors.append("Invalid total value format")
    
    # Validate items if present
    if 'items' in data and isinstance(data['items'], list):
        for i, item in enumerate(data['items']):
            item_errors = validate_item_data(item)
            for error in item_errors:
                errors.append(f"Item {i+1}: {error}")
    
    return errors


def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Sanitize text input"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def validate_file_upload(filename: str, content_type: str, max_size_mb: int = 10) -> List[str]:
    """Validate file upload"""
    errors = []
    
    # Check file extension
    allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if f'.{file_ext}' not in allowed_extensions:
        errors.append(f"File type .{file_ext} not allowed. Allowed: {', '.join(allowed_extensions)}")
    
    # Check content type
    allowed_content_types = [
        'application/pdf',
        'image/png',
        'image/jpeg',
        'image/jpg',
        'image/tiff',
        'image/bmp'
    ]
    
    if content_type not in allowed_content_types:
        errors.append(f"Content type {content_type} not allowed")
    
    return errors

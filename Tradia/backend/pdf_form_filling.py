#!/usr/bin/env python3
"""
B650 Import Declaration PDF Form Filler - Proper Solutions

This script provides multiple reliable methods to fill PDF forms without coordinate guessing.

Method 1: Using pdfplumber to extract form field positions
Method 2: Using PyMuPDF (fitz) for precise form filling
Method 3: Using pdfrw for form field manipulation

Install dependencies (choose one approach):

Method 1: pip install pdfplumber PyPDF2
Method 2: pip install PyMuPDF
Method 3: pip install pdfrw

"""

# Method 1: Using PyMuPDF (fitz) - Most Reliable
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# Method 2: Using pdfrw
try:
    from pdfrw import PdfReader as PDFRWReader, PdfWriter as PDFRWWriter, PdfDict, PdfName
    PDFRW_AVAILABLE = True
except ImportError:
    PDFRW_AVAILABLE = False

# Method 3: Using pdfplumber for field detection
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

import datetime
import os


class B650FormFillerPyMuPDF:
    """Form filler using PyMuPDF - works with actual form fields"""
    
    def __init__(self, template_path, output_path):
        self.template_path = template_path
        self.output_path = output_path
        self.form_data = {}
    
    def set_data(self, data):
        self.form_data = data
        return self
    
    def get_form_fields(self):
        """Get all form fields from the PDF"""
        if not PYMUPDF_AVAILABLE:
            print("PyMuPDF not available. Install with: pip install PyMuPDF")
            return None
        
        try:
            doc = fitz.open(self.template_path)
            fields = {}
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                widgets = page.widgets()
                
                for widget in widgets:
                    field_name = widget.field_name
                    field_type = widget.field_type_string
                    field_value = widget.field_value
                    
                    fields[field_name] = {
                        'type': field_type,
                        'page': page_num,
                        'current_value': field_value,
                        'rect': widget.rect
                    }
            
            doc.close()
            return fields
            
        except Exception as e:
            print(f"Error reading form fields: {e}")
            return None
    
    def print_form_fields(self):
        """Print all available form fields"""
        fields = self.get_form_fields()
        if fields:
            print("Available PDF Form Fields:")
            print("=" * 50)
            for field_name, field_info in fields.items():
                print(f"Field: {field_name}")
                print(f"  Type: {field_info['type']}")
                print(f"  Page: {field_info['page'] + 1}")
                print(f"  Current: {field_info['current_value']}")
                print("-" * 30)
        else:
            print("No form fields found or PyMuPDF not available.")
    
    def fill_form(self):
        """Fill the form using PyMuPDF"""
        if not PYMUPDF_AVAILABLE:
            print("PyMuPDF not available. Please install: pip install PyMuPDF")
            return False
        
        try:
            doc = fitz.open(self.template_path)
            
            # Fill form fields
            filled_count = 0
            for page_num in range(len(doc)):
                page = doc[page_num]
                widgets = page.widgets()
                
                for widget in widgets:
                    field_name = widget.field_name
                    
                    # Look for matching data
                    value_to_set = None
                    
                    # Direct match
                    if field_name in self.form_data:
                        value_to_set = self.form_data[field_name]
                    else:
                        # Fuzzy matching
                        field_name_lower = field_name.lower()
                        for data_key, data_value in self.form_data.items():
                            if data_key.lower() in field_name_lower or field_name_lower in data_key.lower():
                                value_to_set = data_value
                                break
                    
                    if value_to_set is not None:
                        widget.field_value = str(value_to_set)
                        widget.update()
                        filled_count += 1
                        print(f"✓ Filled '{field_name}' = '{value_to_set}'")
            
            # Save the filled document
            doc.save(self.output_path)
            doc.close()
            
            print(f"\n✅ Success! Filled {filled_count} fields.")
            print(f"📄 Saved as: {self.output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error filling form: {e}")
            return False


class B650FormFillerPDFRW:
    """Form filler using pdfrw - alternative approach"""
    
    def __init__(self, template_path, output_path):
        self.template_path = template_path
        self.output_path = output_path
        self.form_data = {}
    
    def set_data(self, data):
        self.form_data = data
        return self
    
    def get_form_fields(self):
        """Get form fields using pdfrw"""
        if not PDFRW_AVAILABLE:
            print("pdfrw not available. Install with: pip install pdfrw")
            return None
        
        try:
            reader = PDFRWReader(self.template_path)
            fields = {}
            
            if reader.Root.AcroForm:
                for field in reader.Root.AcroForm.Fields:
                    field_name = field.T
                    if field_name:
                        # Remove parentheses from field name
                        clean_name = field_name.strip('()')
                        fields[clean_name] = {
                            'type': field.FT,
                            'value': field.V
                        }
            
            return fields
            
        except Exception as e:
            print(f"Error reading fields with pdfrw: {e}")
            return None
    
    def fill_form(self):
        """Fill form using pdfrw"""
        if not PDFRW_AVAILABLE:
            print("pdfrw not available. Please install: pip install pdfrw")
            return False
        
        try:
            reader = PDFRWReader(self.template_path)
            
            # Update form fields
            if reader.Root.AcroForm and reader.Root.AcroForm.Fields:
                filled_count = 0
                
                for field in reader.Root.AcroForm.Fields:
                    field_name = field.T
                    if field_name:
                        clean_name = field_name.strip('()')
                        
                        # Look for matching data
                        if clean_name in self.form_data:
                            field.V = f'({self.form_data[clean_name]})'
                            field.AP = ''  # Clear appearance stream to force regeneration
                            filled_count += 1
                            print(f"✓ Filled '{clean_name}' = '{self.form_data[clean_name]}'")
                
                # Make form non-editable (flatten)
                reader.Root.AcroForm.NeedAppearances = PdfDict()
                reader.Root.AcroForm.NeedAppearances.update(PdfDict(Yes=PdfName.Yes))
                
                # Save
                PDFRWWriter(self.output_path, trailer=reader).write()
                
                print(f"\n✅ Success! Filled {filled_count} fields using pdfrw.")
                print(f"📄 Saved as: {self.output_path}")
                return True
            else:
                print("No AcroForm fields found in PDF.")
                return False
                
        except Exception as e:
            print(f"❌ Error with pdfrw: {e}")
            return False


def analyze_pdf_structure(pdf_path):
    """Analyze PDF to understand its structure and available fields"""
    print(f"🔍 Analyzing PDF: {pdf_path}")
    print("=" * 50)
    
    # Try PyMuPDF first
    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(pdf_path)
            print(f"📄 Pages: {len(doc)}")
            
            total_widgets = 0
            for page_num in range(len(doc)):
                page = doc[page_num]
                widgets = page.widgets()
                
                if widgets:
                    print(f"\n📋 Page {page_num + 1} - Form Fields:")
                    for widget in widgets:
                        print(f"  • {widget.field_name} ({widget.field_type_string})")
                        total_widgets += 1
                else:
                    print(f"\n📋 Page {page_num + 1} - No form fields")
            
            print(f"\n📊 Total form fields found: {total_widgets}")
            doc.close()
            
            if total_widgets == 0:
                print("⚠️  This PDF has no fillable form fields.")
                print("   You may need to use a different PDF or create form fields.")
            
            return total_widgets > 0
            
        except Exception as e:
            print(f"Error analyzing with PyMuPDF: {e}")
    
    # Try pdfrw as fallback
    if PDFRW_AVAILABLE:
        try:
            reader = PDFRWReader(pdf_path)
            if reader.Root.AcroForm:
                fields = reader.Root.AcroForm.Fields
                print(f"\n📊 pdfrw found {len(fields)} form fields")
                return True
            else:
                print("\n⚠️  No AcroForm found with pdfrw")
        except Exception as e:
            print(f"Error analyzing with pdfrw: {e}")
    
    return False


def create_sample_data():
    """Create sample data matching common PDF field names"""
    current_date = datetime.datetime.now().strftime('%d/%m/%Y')
    
    return {
        # Common field name variations
        'OwnerName': 'ABC Import Company Pty Ltd',
        'Owner name': 'ABC Import Company Pty Ltd',
        'owner_name': 'ABC Import Company Pty Ltd',
        
        'OwnerID': '12345678901',
        'Owner ID': '12345678901',
        'ABN': '12345678901',
        
        'OwnerPhone': '+61 2 1234 5678',
        'Phone': '+61 2 1234 5678',
        'Contact phone': '+61 2 1234 5678',
        
        'OwnerEmail': 'imports@abc.com.au',
        'Email': 'imports@abc.com.au',
        'Owner email': 'imports@abc.com.au',
        
        'Invoice Total': 15000.00,
        'Invoice total': 15000.00,
        'invoice total': 15000.00,
        ' Amount1': 15000.00,
        
        'GoodsDescription': 'Electronic Components',
        'Goods description': 'Electronic Components',
        
        'DeclarantName': 'John Smith',
        'Declarant name': 'John Smith',
        'a. Invoice total': 15000.00,
        'Date': current_date,
        'Declaration date': current_date,
        
        # Add more variations as needed
        'AirlineCode': 'QF',
        'LoadingPort': 'LAX',
        'DestinationPort': 'SYD',
        'MasterAWB': '176-12345678',
        'GrossWeight': '250',
        'NumberOfPackages': '5'
    }


def main():
    """Main function with multiple methods"""
    template_file = "b650_unlocked.pdf"
    
    if not os.path.exists(template_file):
        print(f"❌ Template file '{template_file}' not found!")
        return
    
    # First, analyze the PDF structure
    has_fields = analyze_pdf_structure(template_file)
    
    if not has_fields:
        print("\n⚠️  This PDF doesn't appear to have fillable form fields.")
        print("You may need:")
        print("1. A different version of the B650 form with fillable fields")
        print("2. To use PDF form creation software (like Adobe Acrobat)")
        print("3. To use a service that converts static PDFs to fillable forms")
        return
    
    # Create sample data
    sample_data = create_sample_data()
    output_file = f"b650_filled_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    print(f"\n🚀 Attempting to fill form...")
    
    # Try PyMuPDF first (most reliable)
    if PYMUPDF_AVAILABLE:
        print("\n📝 Trying PyMuPDF method...")
        filler = B650FormFillerPyMuPDF(template_file, output_file)
        if filler.set_data(sample_data).fill_form():
            return
    
    # Try pdfrw as backup
    if PDFRW_AVAILABLE:
        print("\n📝 Trying pdfrw method...")
        filler = B650FormFillerPDFRW(template_file, output_file)
        if filler.set_data(sample_data).fill_form():
            return
    
    print("\n❌ All methods failed. The PDF may not have properly configured form fields.")


def inspect_pdf_fields_detailed(pdf_path):
    """
    Detailed inspection of PDF form fields
    This helps you understand exactly what field names to use
    """
    print(f"🔍 Detailed PDF Field Analysis: {pdf_path}")
    print("=" * 60)
    
    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                widgets = page.widgets()
                
                if widgets:
                    print(f"\n📄 PAGE {page_num + 1}")
                    print("-" * 40)
                    
                    for i, widget in enumerate(widgets):
                        print(f"Widget {i + 1}:")
                        print(f"  Field Name: '{widget.field_name}'")
                        print(f"  Field Type: {widget.field_type_string}")
                        print(f"  Current Value: '{widget.field_value}'")
                        print(f"  Rectangle: {widget.rect}")
                        print(f"  Required: {widget.field_flags & 2 == 2}")
                        print()
            
            doc.close()
            return True
            
        except Exception as e:
            print(f"PyMuPDF analysis failed: {e}")
    
    if PDFRW_AVAILABLE:
        try:
            print("\n📝 Trying pdfrw analysis...")
            reader = PDFRWReader(pdf_path)
            
            if reader.Root.AcroForm and reader.Root.AcroForm.Fields:
                print("Form fields found with pdfrw:")
                for i, field in enumerate(reader.Root.AcroForm.Fields):
                    print(f"Field {i + 1}:")
                    print(f"  Name: {field.T}")
                    print(f"  Type: {field.FT}")
                    print(f"  Value: {field.V}")
                    print(f"  Flags: {field.Ff}")
                    print()
                return True
            else:
                print("No AcroForm fields found with pdfrw")
                
        except Exception as e:
            print(f"pdfrw analysis failed: {e}")
    
    return False


def create_fillable_mapping(pdf_path):
    """
    Create a mapping template based on actual PDF fields
    Run this first to see what fields exist, then customize your data
    """
    print("🔧 Creating field mapping template...")
    
    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(pdf_path)
            mapping_template = {}
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                widgets = page.widgets()
                
                for widget in widgets:
                    field_name = widget.field_name
                    if field_name:
                        # Create template entry
                        mapping_template[field_name] = f"<Enter value for {field_name}>"
            
            doc.close()
            
            print("📋 Field mapping template:")
            print("Copy this and replace with your actual values:")
            print("-" * 50)
            print("form_data = {")
            for field_name, placeholder in mapping_template.items():
                print(f"    '{field_name}': '{placeholder}',")
            print("}")
            
            return mapping_template
            
        except Exception as e:
            print(f"Error creating mapping: {e}")
    
    return {}


if __name__ == "__main__":
    template_file = "b650_unlocked.pdf"
    
    if not os.path.exists(template_file):
        print(f"❌ File '{template_file}' not found!")
        print("Please ensure the B650 PDF is in the current directory.")
        exit(1)
    
    print("🔍 B650 PDF Form Analysis and Filling Tool")
    print("=" * 50)
    
    # Check available libraries
    print("📚 Available libraries:")
    print(f"  PyMuPDF (fitz): {'✅' if PYMUPDF_AVAILABLE else '❌'}")
    print(f"  pdfrw: {'✅' if PDFRW_AVAILABLE else '❌'}")
    print(f"  pdfplumber: {'✅' if PDFPLUMBER_AVAILABLE else '❌'}")
    
    if not any([PYMUPDF_AVAILABLE, PDFRW_AVAILABLE]):
        print("\n❌ No suitable PDF libraries found!")
        print("Please install one of these:")
        print("  pip install PyMuPDF")
        print("  pip install pdfrw")
        exit(1)
    
    print(f"\n1️⃣  Analyzing PDF structure...")
    inspect_pdf_fields_detailed(template_file)
    
    print(f"\n2️⃣  Creating field mapping template...")
    create_fillable_mapping(template_file)
    
    print(f"\n3️⃣  Attempting to fill with sample data...")
    main()


# Quick usage for when you know the field names:
"""
# Example usage when you know the exact field names:

# First, run the analysis:
inspect_pdf_fields_detailed('b650_unlocked.pdf')

# Then use the exact field names found:
exact_field_data = {
    'ActualFieldName1': 'Your Value 1',
    'ActualFieldName2': 'Your Value 2',
    # ... use the exact names from the analysis
}

# Fill the form:
if PYMUPDF_AVAILABLE:
    filler = B650FormFillerPyMuPDF('b650_unlocked.pdf', 'output.pdf')
    filler.set_data(exact_field_data).fill_form()
"""
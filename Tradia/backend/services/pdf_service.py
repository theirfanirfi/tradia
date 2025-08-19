from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from typing import Dict, Any, List
import io
import os


class PDFService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1  # Center alignment
        )
        
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=10
        )
        
        self.normal_style = self.styles['Normal']
    
    def generate_declaration_pdf(self, declaration_data: Dict[str, Any], items: List[Dict[str, Any]], declaration_type: str) -> bytes:
        """Generate PDF declaration form"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Build story (content)
        story = []
        
        # Title
        title = Paragraph(f"Australian {declaration_type.title()} Declaration", self.title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Declaration details
        story.extend(self._create_declaration_section(declaration_data))
        story.append(Spacer(1, 20))
        
        # Items table
        story.extend(self._create_items_section(items))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _create_declaration_section(self, data: Dict[str, Any]) -> List:
        """Create declaration details section"""
        story = []
        
        # Header
        header = Paragraph("Declaration Details", self.header_style)
        story.append(header)
        
        # Details table
        details_data = [
            ["Field", "Value"],
            ["Exporter Name", data.get("exporter_name", "N/A")],
            ["Importer Name", data.get("importer_name", "N/A")],
            ["Port of Loading", data.get("port_of_loading", "N/A")],
            ["Port of Discharge", data.get("port_of_discharge", "N/A")],
            ["Total Weight", f"{data.get('total_weight', 0)} kg"],
            ["Total Value", f"AUD {data.get('total_value', 0):.2f}"]
        ]
        
        details_table = Table(details_data, colWidths=[2*inch, 4*inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(details_table)
        return story
    
    def _create_items_section(self, items: List[Dict[str, Any]]) -> List:
        """Create items table section"""
        story = []
        
        # Header
        header = Paragraph("Items Declaration", self.header_style)
        story.append(header)
        
        if not items:
            story.append(Paragraph("No items declared", self.normal_style))
            return story
        
        # Items table
        items_data = [["Item", "Description", "Type", "Weight", "Price"]]
        
        for item in items:
            items_data.append([
                item.get("item_title", "N/A"),
                item.get("item_description", "N/A"),
                item.get("item_type", "N/A"),
                f"{item.get('item_weight', 0)} {item.get('item_weight_unit', 'kg')}",
                f"{item.get('item_currency', 'AUD')} {item.get('item_price', 0):.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8)
        ]))
        
        story.append(items_table)
        return story


# Global instance
pdf_service = PDFService()

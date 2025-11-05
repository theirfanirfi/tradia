from pprint import pprint
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import Dict, Any
import os
from config.database import get_db
from models import UserDeclaration, UserProcess, UserProcessItem, UserDocument
from models.auth import User
from schemas.declaration_schemas import (
    DeclarationResponse,
    UpdateDeclarationRequest,
    GeneratePdfResponse
)
from services.pdf_service import pdf_service
from utils.auth_dependencies import get_current_user
from utils.validators import validate_declaration_data
from tasks.background_tasks import task_b650_extract_section_a_information, task_b650_extract_section_b_information, task_b650_extract_section_c_information
from schemas.B650.import_section_a import B650SectionAHeader
from services.B650_PreLLMService import preprocessor
from schemas.B650.import_section_b import SectionB
from schemas.B650.import_section_c_schema import SECTIONC
import json
from mappings.map_responses_onto_b650 import map_b650_to_formdata
from pdf_form_filling import PYMUPDF_AVAILABLE, B650FormFillerPyMuPDF
import datetime
from fastapi.responses import FileResponse


router = APIRouter(prefix="/api/declaration", tags=["declaration"])


@router.get("/import/{process_id}/section_a", response_model=DeclarationResponse)
async def get_declaration(
    process_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get declaration data for a process"""
    print('declaration for section a received')
    declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
    print('declaration', declaration.declaration_id)
    if declaration and (len(declaration.import_declaration_section_a) ==0 and len(declaration.import_declaration_section_b) ==0 and len(declaration.import_declaration_section_c) ==0):
        print('not declaration')
        task_b650_extract_section_a_information.delay(process_id)
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail="Declarations being ready"
        )
    
    print('not declaration after')
    
    if not declaration.import_declaration_section_c:
        items = db.query(UserProcessItem).filter(UserProcessItem.process_id == process_id).all()
        hs_codes = []
        goods_descriptions = ""
        total_quantity = 0
        unit_of_measure = "KG"
        customs_value = 0.0
        additional_info = ""

        for item in items:
            hs_codes.append(item.item_hs_code or "")
            goods_descriptions = goods_descriptions + item.item_description
            total_quantity += float(item.item_weight or 0)
            unit_of_measure = item.item_weight_unit or unit_of_measure
            customs_value += float(item.item_price or 0)
            additional_info += additional_info + item.item_title

        tariff_line = {
            "tariff_classification": hs_codes,
            "goods_description": goods_descriptions,
            "quantity": total_quantity,
            "unit_of_measure": unit_of_measure,
            "country_of_origin": "",  # Not present in model
            "customs_value": str(customs_value),
            "fob_value": "",  # Placeholder
            "cif_value": "",  # Placeholder
            "origin_country_code": "",  # Placeholder
            "preference_rule_type": "",  # Placeholder
            "preference_scheme_type": "",  # Placeholder
            "tariff_instrument": "",  # Placeholder
            "additional_information": additional_info,
            "tariff_classification_code": hs_codes,
        }
        # json_str = json.dumps(tariff_line)
        print(type(tariff_line))
        print(tariff_line)
        try:
            declaration.import_declaration_section_c = tariff_line
            db.add(declaration)
            db.commit()
        except Exception as e:
            print('exception',e)

    # Attach tariff_line into the declaration response
    response = DeclarationResponse.from_orm(declaration)
    return response
        # return DeclarationResponse.from_orm(declaration)
    
    # return DeclarationResponse.from_orm(declaration)


@router.put("/import/{process_id}/update/section_a", response_model=DeclarationResponse)
async def update_declaration(
    process_id: str,
    request: B650SectionAHeader,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update declaration data"""
    declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Declaration not found"
        )
    
    print(request)
    
    try:
        # Validate data
        # validation_errors = validate_declaration_data(request.schema_details)
        # if validation_errors:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"Validation failed: {'; '.join(validation_errors)}"
        #     )
        
        # Update schema details
        # section_a = B650SectionAHeader(**request)
        json_str = request.model_dump(exclude_none=False, mode='json')
        declaration.import_declaration_section_a = json_str
        db.add(declaration)
        
        db.commit()
        db.refresh(declaration)
        
        return DeclarationResponse.from_orm(declaration)
        
    except Exception as ee:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update declaration: {str(ee)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update declarationn: {str(e)}"
        )



### section b

#todo map section b schema into request for updation

@router.put("/import/{process_id}/update/section_b", response_model=DeclarationResponse)
async def update_declaration_section_b(
    process_id: str,
    request: SectionB,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update declaration data"""
    declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Declaration not found"
        )
    
    print(request)
    
    try:
        # Validate data
        # validation_errors = validate_declaration_data(request.schema_details)
        # if validation_errors:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"Validation failed: {'; '.join(validation_errors)}"
        #     )
        
        # Update schema details
        # section_a = B650SectionAHeader(**request)
        json_str = request.model_dump(exclude_none=False, mode='json')
        declaration.import_declaration_section_b = json_str
        db.add(declaration)
        
        db.commit()
        db.refresh(declaration)
        
        return DeclarationResponse.from_orm(declaration)
        
    except Exception as ee:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update declaration: {str(ee)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update declarationn: {str(e)}"
        )

@router.get("/import/{process_id}/update/section_b", response_model=DeclarationResponse)
async def get_declaration_section_b(
    process_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get declaration data for a process"""
    declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
    if declaration:
        if not declaration.import_declaration_section_b:
            task_b650_extract_section_b_information.delay(process_id)
        

        return DeclarationResponse.from_orm(declaration)


        # return DeclarationResponse.from_orm(declaration)
    raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail="Declarations being ready"
        )

## section c 

@router.get("/import/{process_id}/section_c", response_model=DeclarationResponse)
async def get_declaration_section_c(
    process_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get declaration data for a process"""
    declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
    if not declaration:
        task_b650_extract_section_a_information.delay(process_id)
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail="Declarations being ready"
        )
        # return DeclarationResponse.from_orm(declaration)
    
    return DeclarationResponse.from_orm(declaration)



@router.put("/import/{process_id}/update/section_c", response_model=DeclarationResponse)
async def update_declaration_section_c(
    process_id: str,
    request: SECTIONC,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update declaration data"""
    declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
    if not declaration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Declaration not found"
        )
    
    print(request)
    
    try:
        # Validate data
        # validation_errors = validate_declaration_data(request.schema_details)
        # if validation_errors:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"Validation failed: {'; '.join(validation_errors)}"
        #     )
        
        # Update schema details
        # section_a = B650SectionAHeader(**request)
        json_str = request.model_dump(exclude_none=False, mode='json')
        declaration.import_declaration_section_c = json_str
        db.add(declaration)
        
        db.commit()
        db.refresh(declaration)
        
        return DeclarationResponse.from_orm(declaration)
        
    except Exception as ee:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update declaration: {str(ee)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update declarationn: {str(e)}"
        )




@router.post("/{process_id}/generate-pdf")
async def generate_declaration_pdf(
    process_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate PDF declaration form"""
    try:
        # Get declaration data
        declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
        if not declaration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Declaration not found"
            )

        try:
            user_documents = db.query(UserDocument).filter(UserDocument.process_id == process_id).all()
            total_price = 0

            for ud in user_documents:
                if not ud.llm_response['total_price'] is None:
                    total_price += ud.llm_response['total_price']
        except Exception as ude:
            print(ude)
        
        if not declaration:
            pass

        b650_schema = {
            "header": declaration.import_declaration_section_a,
            "section_b": declaration.import_declaration_section_b,
            "tariff_lines": declaration.import_declaration_section_c,

        }
        print(b650_schema)
        if (not b650_schema['tariff_lines']['tariff_classification'] is None) and len(b650_schema['tariff_lines']['tariff_classification']) > 0:
            b650_schema['tariff_lines']['tariff_classification'] =  b650_schema['tariff_lines']['tariff_classification'][0]
            b650_schema['tariff_lines']['tariff_classification_code'] = b650_schema['tariff_lines']['tariff_classification_code'][0]
        else:
            b650_schema['tariff_lines']['tariff_classification'] =  b650_schema['tariff_lines']['tariff_classification']
            b650_schema['tariff_lines']['tariff_classification_code'] = b650_schema['tariff_lines']['tariff_classification_code']

        header = B650SectionAHeader(**b650_schema['header'])
        section_b = SectionB(**b650_schema['section_b'])
        # try:
        tariff_lines = SECTIONC(**b650_schema['tariff_lines'])


        try:
            mapped_schema = map_b650_to_formdata(header, section_b, tariff_lines, str(total_price))
            if PYMUPDF_AVAILABLE:
                # create uploads/<user_id>/ directory
                uploads_root = os.path.join(os.getcwd(), "uploads")
                user_upload_dir = os.path.join(uploads_root, str(current_user.user_id))
                os.makedirs(user_upload_dir, exist_ok=True)

                # generate filename <user_id>_<timestamp>.pdf
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_filename = f"{current_user.user_id}_{timestamp}.pdf"
                output_pdf_path = os.path.join(user_upload_dir, pdf_filename)


                filler = B650FormFillerPyMuPDF('b650_unlocked.pdf', output_pdf_path)
                filler.set_data(mapped_schema).fill_form()
                filled_ok = filler.set_data(mapped_schema).fill_form()
                if not filled_ok or not os.path.exists(output_pdf_path):
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to fill and generate PDF not filled_ok"
                    )


                # persist generated pdf filename on the UserDeclaration model
                # try:
                #     # store filename (not full path) per request
                #     declaration.generated_pdf = pdf_filename
                #     db.add(declaration)
                #     db.commit()
                #     db.refresh(declaration)
                # except Exception as db_e:
                #     print("Failed to save generated pdf info on declaration:", db_e)

                # return the file so frontend can download it
                return FileResponse(
                    path=output_pdf_path,
                    media_type="application/pdf",
                    filename=pdf_filename
                )
        except Exception as e:
            print(e)
            return HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate PDF: {str(e)}"
            )
        
    except Exception as e:
        print('e',e)
    except Exception as ee:
        print('ee',ee)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )

@router.get("/import/{process_id}/status", response_model=Dict[str, Any])
async def check_declaration_status(
    process_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check the status of the declaration"""
    declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
    if not declaration:
        return {
            "status": False,
            "message": "declaration not found",
        }

    # Check if the sections are empty
    status = {
        "import_section_a": declaration.import_declaration_section_a,
        "import_section_b": declaration.import_declaration_section_b,
        "import_section_c": declaration.import_declaration_section_c,
    }

    return {
        "status": (len(status["import_section_a"]) > 0 and len(status["import_section_b"]) > 0 and len(status["import_section_c"]) > 0),
        "message": "declaration found",
    }
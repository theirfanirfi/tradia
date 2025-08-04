import json
from writeonpdf import fill_pdf_with_llm_json

if __name__ == "__main__":
    # Load LLM chatbot JSON response
    with open("../forms_schema/b650_llm_response.json") as f:
        llm_json = json.load(f)

    # Set template and output paths
    template_path = "../docs/b650_unlocked.pdf"
    output_path = "../docs/b650_filled_test.pdf"

    # Fill the PDF using the mapping-aware logic
    try:
        success = fill_pdf_with_llm_json(llm_json, template_path, output_path, flatten=True)
        if success:
            print("✓ PDF filled and saved to", output_path)
        else:
            print("Failed to fill PDF.")
    except Exception as e:
        print("Error while filling PDF!")
        print("Error message:", e)
        import traceback
        traceback.print_exc() 
#!/usr/bin/env python3
import asyncio
from core.ocr_extractor import extract_text_from_file

async def main():
    path = "/home/abdulwahab-bhai/personal/tradia_ai_backend/backend/scripts/ocr-test.png"
    text = await extract_text_from_file(path)
    print("---- OCR OUTPUT START ----")
    print(text[:1000])  # print first 1k chars
    print("---- OCR OUTPUT END ----")

if __name__ == "__main__":
    asyncio.run(main())

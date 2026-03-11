from __future__ import annotations

import logging
from pathlib import Path

import fitz
import ocrmypdf

from app.config import Settings
from app.models import OCRRequestMessage


class OCRService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)

    def has_text(self, pdf_path: Path) -> bool:
        doc = fitz.open(pdf_path)
        try:
            for page in doc:
                if page.get_text().strip():
                    return True
            return False
        finally:
            doc.close()

    def output_key_for(self, source_key: str) -> str:
        if self.settings.overwrite_source:
            return source_key
        source_path = Path(source_key)
        return str(source_path.with_name(f"{source_path.stem}{self.settings.output_suffix}{source_path.suffix}"))

    def process(self, request: OCRRequestMessage, input_path: Path, output_path: Path) -> tuple[bool, str]:
        ocr_applied = True
        if not self.settings.ocr_force and self.has_text(input_path):
            self.logger.info(
                "PDF ja possui texto. OCR pulado arquivoId=%s key=%s",
                request.arquivo_id,
                request.caminho_arquivo,
            )
            output_path.write_bytes(input_path.read_bytes())
            ocr_applied = False
        else:
            self.logger.info(
                "Iniciando OCR arquivoId=%s key=%s jobs=%s outputType=%s",
                request.arquivo_id,
                request.caminho_arquivo,
                self.settings.ocr_jobs,
                self.settings.ocr_output_type,
            )
            ocrmypdf.ocr(
                str(input_path),
                str(output_path),
                rotate_pages=self.settings.ocr_rotate_pages,
                language=self.settings.ocr_language,
                jobs=self.settings.ocr_jobs,
                clean=self.settings.ocr_clean,
                optimize=self.settings.ocr_optimize,
                output_type=self.settings.ocr_output_type,
                use_threads=self.settings.ocr_use_threads,
                force_ocr=self.settings.ocr_force,
            )
        return ocr_applied, self.output_key_for(request.caminho_arquivo)

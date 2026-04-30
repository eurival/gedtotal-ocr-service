from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

import fitz
import ocrmypdf
import pikepdf

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

    @staticmethod
    def _compute_sha256(file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def _title_from_filename(nome_arquivo: str | None) -> str:
        """Extrai título do nome do arquivo sem extensão."""
        if not nome_arquivo:
            return "Documento OCR GedTotal"
        return Path(nome_arquivo).stem

    def process(self, request: OCRRequestMessage, input_path: Path, output_path: Path) -> tuple[bool, str, str]:
        """Retorna (ocr_applied, output_key, hash_sha256)."""
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

        self._reapply_base_metadata(request, output_path)
        hash_sha256 = self._compute_sha256(output_path)
        self.logger.info("OCR concluido arquivoId=%s hash=%s", request.arquivo_id, hash_sha256)
        return ocr_applied, self.output_key_for(request.caminho_arquivo), hash_sha256

    def _reapply_base_metadata(self, request: OCRRequestMessage, output_path: Path) -> None:
        """Grava metadados PDF conforme Decreto 10.278/2020 (Anexo II)."""
        patched_output = output_path.with_name(f"{output_path.stem}-metadata{output_path.suffix}")
        now_iso = datetime.now(timezone.utc).strftime("D:%Y%m%d%H%M%S+00'00'")
        now_readable = datetime.now(timezone.utc).isoformat()

        try:
            with pikepdf.open(str(output_path)) as pdf:
                # ── Metadados padrão PDF (Decreto 10.278 Art. 7º, Anexo II) ──

                # 1. Título — nome do arquivo sem extensão
                pdf.docinfo["/Title"] = self._title_from_filename(request.nome_arquivo)

                # 2. Autor — pessoa jurídica emissora do documento
                author_parts = []
                if request.nome_cliente:
                    author_parts.append(request.nome_cliente)
                if request.cpfcnpj_cliente:
                    author_parts.append(f"(CNPJ/CPF: {request.cpfcnpj_cliente})")
                pdf.docinfo["/Author"] = " ".join(author_parts) if author_parts else "GedTotal"

                # 3. Assunto — hierarquia documental
                subject_parts = [p for p in [
                    request.nome_departamento,
                    request.nome_projeto,
                    request.nome_formulario,
                ] if p]
                pdf.docinfo["/Subject"] = " / ".join(subject_parts) if subject_parts else "Documento digitalizado GedTotal"

                # 4. Keywords — tipo documental + classificação CONARQ
                kw_parts = []
                if request.tipo_documental:
                    kw_parts.append(request.tipo_documental)
                if request.classificacao_conarq:
                    kw_parts.append(request.classificacao_conarq)
                kw_parts.extend(["GedTotal", "OCR", "PDF/A", "Decreto 10.278/2020"])
                pdf.docinfo["/Keywords"] = ", ".join(kw_parts)

                # Produtor/Criador
                pdf.docinfo["/Creator"] = "GedTotal OCR Service v1.0"
                pdf.docinfo["/Producer"] = "GedTotal OCR Service (OCRmyPDF + Tesseract)"
                pdf.docinfo["/CreationDate"] = now_iso
                pdf.docinfo["/ModDate"] = now_iso

                # ── Metadados customizados GedTotal (rastreabilidade) ──

                # 5. Data e local da digitalização
                pdf.docinfo["/gedtotalDataDigitalizacao"] = now_readable

                # 6. Responsável pela digitalização
                pdf.docinfo["/gedtotalResponsavel"] = "GedTotal OCR Service"

                # 7. Identificador do documento digital
                pdf.docinfo["/gedtotalArquivoId"] = str(request.arquivo_id)

                # Dados de classificação
                pdf.docinfo["/gedtotalOcrApplied"] = "true"
                if request.nome_cliente:
                    pdf.docinfo["/gedtotalCliente"] = request.nome_cliente
                if request.cpfcnpj_cliente:
                    pdf.docinfo["/gedtotalCpfCnpj"] = request.cpfcnpj_cliente
                if request.nome_departamento:
                    pdf.docinfo["/gedtotalDepartamento"] = request.nome_departamento
                if request.nome_projeto:
                    pdf.docinfo["/gedtotalProjeto"] = request.nome_projeto
                if request.nome_formulario:
                    pdf.docinfo["/gedtotalFormulario"] = request.nome_formulario
                if request.tipo_documental:
                    pdf.docinfo["/gedtotalTipoDocumental"] = request.tipo_documental
                if request.classificacao_conarq:
                    pdf.docinfo["/gedtotalClasseConarq"] = request.classificacao_conarq
                if request.trace_id:
                    pdf.docinfo["/gedtotalTraceId"] = request.trace_id

                pdf.save(str(patched_output))

            patched_output.replace(output_path)
        finally:
            if patched_output.exists():
                patched_output.unlink(missing_ok=True)


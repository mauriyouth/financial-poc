-- Migration: Add pdf_preview_path column to documents table
-- Date: 2026-01-18
-- Description: Adds pdf_preview_path column to store PDF conversion path for PPTX files

-- Add the column (nullable since existing documents won't have it)
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS pdf_preview_path VARCHAR(255) DEFAULT NULL;

-- Add a comment to document the purpose
COMMENT ON COLUMN documents.pdf_preview_path IS 'Path to PDF preview file for presentations (PPTX files auto-converted to PDF)';

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ArrowRight,
  ShieldCheck,
  Layers,
  X,
  FileCode,
  RotateCcw,
  Search,
  BookOpen
} from 'lucide-react';
import { api } from '../services/api';
import { UploadResponse } from '../types';
import {
  PipelineStepper,
  StepItem,
  CodeChip,
  Badge,
  Alert,
  EmptyState,
  PageHeader
} from '../components/ui';

export const UploadTender: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(-1);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const navigate = useNavigate();

  const pipelineSteps: StepItem[] = [
    { id: 'upload', label: 'Uploading', description: 'Sending file payload' },
    { id: 'extract', label: 'Extracting Pages', description: 'Parsing PDF & text clauses' },
    { id: 'analyze', label: 'Analyzing Requirements', description: 'Decomposing technical parameters' },
    { id: 'search', label: 'Searching Standards', description: 'Cosine vector retrieval' },
    { id: 'complete', label: 'Completed', description: 'Audit-ready recommendations' },
  ];

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const validateAndSetFile = (selectedFile: File) => {
    const ext = selectedFile.name.toLowerCase().split('.').pop();
    if (ext !== 'pdf' && ext !== 'txt') {
      setError('Unsupported file type. Please upload a valid PDF (.pdf) or Plain Text (.txt) document.');
      setFile(null);
      setUploadResult(null);
      setCurrentStepIndex(-1);
      return;
    }
    if (selectedFile.size > 25 * 1024 * 1024) {
      setError('File size exceeds the 25MB limit. Please upload a smaller document.');
      setFile(null);
      setUploadResult(null);
      setCurrentStepIndex(-1);
      return;
    }
    setError(null);
    setFile(selectedFile);
    setUploadResult(null);
    setCurrentStepIndex(-1);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setError(null);
    setUploadResult(null);
    setCurrentStepIndex(-1);
    const inputEl = document.getElementById('tender-file-input') as HTMLInputElement | null;
    if (inputEl) inputEl.value = '';
  };

  const handleUploadAndProcess = async () => {
    if (!file) return;
    setIsProcessing(true);
    setError(null);

    try {
      // Step 0: Uploading
      setCurrentStepIndex(0);
      await new Promise((r) => setTimeout(r, 600));

      // Step 1: Extracting
      setCurrentStepIndex(1);
      const res = await api.uploadTender(file);

      // Step 2: Analyzing
      setCurrentStepIndex(2);
      await new Promise((r) => setTimeout(r, 800));

      // Step 3: Searching
      setCurrentStepIndex(3);
      await new Promise((r) => setTimeout(r, 800));

      // Step 4: Completed
      setCurrentStepIndex(4);
      setUploadResult(res);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to process tender specification file.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRunSearchForDetected = (stdNumber: string) => {
    navigate(`/search?q=${encodeURIComponent(stdNumber)}`);
  };

  return (
    <div className="space-y-8">
      {/* ── 1. Page Header ─────────────────────────────────────────────────── */}
      <PageHeader
        title="Upload Tender Specification Document"
        description="Ingest procurement specifications (.pdf or .txt) to extract technical clauses, detect cited standards, and match mandatory BIS requirements."
        badge={
          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-bg-sunken text-ink-900 border border-border-default">
            Max 25 MB · PDF / TXT
          </span>
        }
      />

      {/* ── 2. Stepper Status (When Upload Initiated) ───────────────────────── */}
      {currentStepIndex >= 0 && (
        <div className="p-6 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-4">
          <div className="flex items-center justify-between border-b border-border-default pb-3">
            <span className="font-bold text-sm font-serif text-ink-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-brand" />
              Document Processing Pipeline
            </span>
            <span className="text-xs font-mono font-bold text-ink-500">
              {currentStepIndex === 4 ? 'Completed' : 'Active Ingestion'}
            </span>
          </div>

          <PipelineStepper
            steps={pipelineSteps}
            currentStepIndex={currentStepIndex}
            isError={!!error}
            errorMessage={error || undefined}
          />
        </div>
      )}

      {/* ── 3. Drag & Drop Upload Zone ─────────────────────────────────────── */}
      <div className="p-8 sm:p-10 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-6">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center transition-all duration-200 flex flex-col items-center justify-center gap-4 ${
            isDragging
              ? 'border-brand bg-brand/5 shadow-warm'
              : 'border-border-strong hover:border-brand bg-bg-base/40'
          }`}
        >
          <input
            id="tender-file-input"
            type="file"
            accept=".pdf,.txt"
            onChange={handleFileChange}
            disabled={isProcessing}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          />

          <div className="w-16 h-16 rounded-2xl bg-bg-surface text-brand border border-border-default flex items-center justify-center shadow-warm">
            <Upload className="w-8 h-8" />
          </div>

          <div className="space-y-1.5 max-w-md">
            <h3 className="text-lg font-bold font-serif text-ink-900">
              Drag and drop tender document here
            </h3>
            <p className="text-sm text-ink-500 font-medium">
              Accepts official PDF tender documents, schedules of requirements, or plain text specification drafts up to 25MB.
            </p>
          </div>

          <div className="pt-2">
            <span className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-warm">
              Select Document from Computer
            </span>
          </div>
        </div>

        {/* Selected File Chip */}
        {file && (
          <div className="p-4 rounded-xl border border-border-strong bg-bg-sunken flex items-center justify-between gap-4 animate-slide-up">
            <div className="flex items-center gap-3 min-w-0">
              <div className="p-2.5 rounded-lg bg-bg-surface border border-border-default text-brand">
                {file.name.endsWith('.pdf') ? (
                  <FileText className="w-5 h-5 text-danger" />
                ) : (
                  <FileCode className="w-5 h-5 text-brand" />
                )}
              </div>
              <div className="min-w-0">
                <p className="font-bold text-sm text-ink-900 truncate">{file.name}</p>
                <div className="flex items-center gap-2 text-xs text-ink-500 font-mono">
                  <span>{formatFileSize(file.size)}</span>
                  <span>•</span>
                  <span className="uppercase">{file.name.split('.').pop()}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {!isProcessing && (
                <button
                  type="button"
                  onClick={handleRemoveFile}
                  className="p-1.5 rounded-lg text-ink-500 hover:text-danger hover:bg-bg-surface transition-colors"
                  title="Remove file"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>
        )}

        {/* Process Action Button */}
        {file && !uploadResult && (
          <div className="flex justify-end pt-2">
            <button
              onClick={handleUploadAndProcess}
              disabled={isProcessing}
              className="px-8 py-3 rounded-xl bg-brand hover:bg-brand-hover text-white text-sm font-bold transition-all shadow-warm flex items-center gap-2 disabled:opacity-50"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Processing Specification...</span>
                </>
              ) : (
                <>
                  <span>Extract & Analyze Document</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && !isProcessing && (
        <Alert variant="error" title="Processing Error">
          {error}
        </Alert>
      )}

      {/* ── 4. Upload & Ingestion Results ───────────────────────────────────── */}
      {uploadResult && (
        <div className="p-8 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-6 animate-slide-up">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-default pb-4">
            <div className="space-y-1">
              <span className="text-[11px] font-mono font-bold tracking-wider uppercase text-success flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-success" />
                Ingestion Completed Successfully
              </span>
              <h3 className="text-xl font-bold font-serif text-ink-900">
                Extracted Document Artifacts
              </h3>
            </div>

            <button
              onClick={handleRemoveFile}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-border-default bg-bg-sunken hover:bg-bg-surface text-xs font-bold text-ink-900 transition-colors shadow-warm-sm"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Upload Another Tender</span>
            </button>
          </div>

          {/* Metric Stats Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl border border-border-default bg-bg-sunken space-y-1">
              <span className="text-[11px] uppercase font-bold text-ink-500">Document ID</span>
              <p className="font-mono text-xs font-bold text-ink-900 truncate">
                {uploadResult.document_id}
              </p>
            </div>
            <div className="p-4 rounded-xl border border-border-default bg-bg-sunken space-y-1">
              <span className="text-[11px] uppercase font-bold text-ink-500">Pages Extracted</span>
              <p className="font-mono text-2xl font-extrabold text-ink-900 tabular-nums">
                {uploadResult.pages_extracted}
              </p>
            </div>
            <div className="p-4 rounded-xl border border-border-default bg-bg-sunken space-y-1">
              <span className="text-[11px] uppercase font-bold text-ink-500">Chunks Indexed</span>
              <p className="font-mono text-2xl font-extrabold text-ink-900 tabular-nums">
                {uploadResult.total_chunks}
              </p>
            </div>
            <div className="p-4 rounded-xl border border-border-default bg-bg-sunken space-y-1">
              <span className="text-[11px] uppercase font-bold text-ink-500">Standards Cited</span>
              <p className="font-mono text-2xl font-extrabold text-brand tabular-nums">
                {uploadResult.detected_explicit_standards?.length || 0}
              </p>
            </div>
          </div>

          {/* Detected Explicit Standards */}
          {uploadResult.detected_explicit_standards && uploadResult.detected_explicit_standards.length > 0 ? (
            <div className="space-y-3 pt-2">
              <span className="text-xs font-bold uppercase tracking-wider text-ink-700 block">
                Explicit Standards Referenced in Tender Text:
              </span>
              <div className="flex flex-wrap gap-2.5">
                {uploadResult.detected_explicit_standards.map((std, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 p-2 px-3 rounded-xl border border-border-default bg-bg-surface shadow-warm-sm"
                  >
                    <CodeChip code={std} variant="primary" />
                    <button
                      onClick={() => handleRunSearchForDetected(std)}
                      className="px-2.5 py-1 rounded-lg bg-bg-sunken hover:bg-brand hover:text-white text-[11px] font-bold text-ink-900 transition-colors"
                      title="Run search on this standard"
                    >
                      Inspect Match
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-xl border border-border-default bg-bg-sunken text-xs text-ink-500 font-medium">
              No explicit Indian Standard numbers were mentioned in the document text. The engine will match standards semantically based on extracted parameters.
            </div>
          )}

          {/* Navigation Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-4 border-t border-border-default">
            <Link
              to={`/pre-publish?doc_id=${uploadResult.document_id}`}
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl border border-border-default bg-bg-sunken hover:bg-bg-surface text-ink-900 text-xs font-bold transition-all shadow-warm-sm flex items-center justify-center gap-2"
            >
              <span>Validate Draft (Rules A–E)</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <Link
              to={`/search?q=${encodeURIComponent(uploadResult.filename)}`}
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-warm flex items-center justify-center gap-2"
            >
              <span>Run Search on Specifications</span>
              <Search className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

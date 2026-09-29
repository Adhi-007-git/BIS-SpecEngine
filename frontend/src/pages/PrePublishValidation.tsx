import React, { useState } from 'react';
import {
  FileCheck2,
  Download,
  Loader2,
  Scale,
  UserCheck,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  HelpCircle,
  FileText
} from 'lucide-react';
import { api } from '../services/api';
import {
  TenderValidationReport,
  ValidationFinding,
  OfficerDecisionType,
  ValidationSeverity
} from '../types';
import { Badge, CodeChip, ConfidenceMeter, Alert, EmptyState, PageHeader } from '../components/ui';

export const PrePublishValidation: React.FC = () => {
  const [inputMode, setInputMode] = useState<'text' | 'document'>('text');
  const [tenderText, setTenderText] = useState<string>('');
  const [documentId, setDocumentId] = useState<string>('');
  const [validating, setValidating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<TenderValidationReport | null>(null);

  // Officer review state
  const [officerId, setOfficerId] = useState<string>('DEV_OFFICER_DEFAULT');
  const [reviewDecision, setReviewDecision] = useState<OfficerDecisionType>('APPROVED_WITH_NOTES');
  const [reviewComments, setReviewComments] = useState<string>('');
  const [submittingReview, setSubmittingReview] = useState<boolean>(false);
  const [reviewSuccessMsg, setReviewSuccessMsg] = useState<string | null>(null);

  // Findings filter & expansion
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [expandedFinding, setExpandedFinding] = useState<string | null>(null);

  // Illustrative test scenarios
  const loadScenario = (type: string) => {
    setError(null);
    if (type === 'superseded') {
      setTenderText(
        "Tender No: CPWD/2026/CIVIL-04\nScope: Construction of reinforced concrete foundation and columns.\n" +
        "Technical Specification:\nAll concrete design and reinforcement detailing must strictly comply with IS 456:1978.\n" +
        "Coarse aggregates must conform to IS 383:2016."
      );
    } else if (type === 'qco_missing') {
      setTenderText(
        "Tender No: MES/2026/ELEC-12\nScope: Supply of electrical wiring and building lighting cables.\n" +
        "Technical Specification:\nSupply of 1100V grade PVC insulated unsheathed single-core copper conductor cables conforming to IS 694:2010.\n" +
        "Packing in 100m coils."
      );
    } else if (type === 'foreign') {
      setTenderText(
        "Tender No: NHAI/2026/STEEL-09\nScope: Fabrication of structural steel bridge trusses.\n" +
        "Technical Specification:\nHigh-strength structural carbon steel plates conforming to ASTM A36 with minimum yield strength of 250 MPa."
      );
    } else if (type === 'active_clean') {
      setTenderText(
        "Tender No: RITES/2026/CIVIL-88\nScope: Construction of multi-storey office complex.\n" +
        "Technical Specification:\nReinforced concrete works to strictly conform to IS 456:2000.\n" +
        "Aggregates to conform to IS 383:2016.\n" +
        "Compressive strength testing shall be performed in accordance with IS 516:1959."
      );
    }
  };

  const handleValidate = async () => {
    setError(null);
    setReviewSuccessMsg(null);

    if (inputMode === 'text' && !tenderText.trim()) {
      setError('Please enter technical specification text to validate.');
      return;
    }
    if (inputMode === 'document' && !documentId.trim()) {
      setError('Please enter a valid uploaded document ID.');
      return;
    }

    setValidating(true);
    try {
      const payload = inputMode === 'text'
        ? { tender_text: tenderText.trim() }
        : { document_id: documentId.trim() };

      const res = await api.validateTender(payload);
      setReport(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Pre-publish validation request failed.');
    } finally {
      setValidating(false);
    }
  };

  const handleOfficerReviewSubmit = async () => {
    if (!report) return;
    setSubmittingReview(true);
    setReviewSuccessMsg(null);
    try {
      const updated = await api.reviewValidationReport(report.validation_id, {
        decision: reviewDecision,
        officer_id: officerId.trim() || 'DEV_OFFICER_DEFAULT',
        comments: reviewComments.trim(),
      });
      setReport(updated);
      setReviewSuccessMsg(`Officer decision '${reviewDecision}' recorded successfully.`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit officer review.');
    } finally {
      setSubmittingReview(false);
    }
  };

  const filteredFindings = report?.findings.filter((f) => {
    if (filterSeverity === 'ALL') return true;
    return f.severity === filterSeverity;
  }) || [];

  return (
    <div className="space-y-8">
      {/* ── 1. Page Header ─────────────────────────────────────────────────── */}
      <PageHeader
        title="Pre-Publish Tender Specification Audit"
        description="Audit tender drafts against Rules A–E to detect superseded codes, missing mandatory QCO obligations, and foreign specification conflicts before publishing."
        badge={
          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-bg-sunken text-ink-900 border border-border-default">
            Feature M10 · Statutory Rules A–E
          </span>
        }
      />

      {/* ── 2. Test Scenarios Bar ───────────────────────────────────────────── */}
      <div className="p-6 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-4">
        <div className="flex items-center justify-between border-b border-border-default pb-3">
          <span className="text-xs font-bold uppercase tracking-wider text-ink-700">
            Quick Test Scenarios (Audit Demonstrators):
          </span>
          <span className="text-[11px] font-mono text-ink-500 font-semibold">
            One-Click Benchmarks
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            type="button"
            onClick={() => loadScenario('superseded')}
            className="p-3.5 rounded-xl border border-warning/40 bg-warning-soft hover:border-warning text-left transition-all shadow-warm-sm"
          >
            <div className="flex items-center justify-between text-warning font-bold text-xs">
              <span>Rule A: Superseded IS</span>
              <span className="text-[10px] font-mono">CPWD</span>
            </div>
            <p className="text-xs text-ink-700 mt-1 font-medium">IS 456:1978 cited instead of active IS 456:2000</p>
          </button>

          <button
            type="button"
            onClick={() => loadScenario('qco_missing')}
            className="p-3.5 rounded-xl border border-danger/40 bg-danger-soft hover:border-danger text-left transition-all shadow-warm-sm"
          >
            <div className="flex items-center justify-between text-danger font-bold text-xs">
              <span>Rule B: QCO Omission</span>
              <span className="text-[10px] font-mono">MES</span>
            </div>
            <p className="text-xs text-ink-700 mt-1 font-medium">IS 694 cable without statutory ISI mark mandate</p>
          </button>

          <button
            type="button"
            onClick={() => loadScenario('foreign')}
            className="p-3.5 rounded-xl border border-accent/40 bg-accent-soft hover:border-accent text-left transition-all shadow-warm-sm"
          >
            <div className="flex items-center justify-between text-accent font-bold text-xs">
              <span>Rule C: Foreign Conflict</span>
              <span className="text-[10px] font-mono">NHAI</span>
            </div>
            <p className="text-xs text-ink-700 mt-1 font-medium">ASTM A36 steel cited without Indian IS 2062 equivalence</p>
          </button>

          <button
            type="button"
            onClick={() => loadScenario('active_clean')}
            className="p-3.5 rounded-xl border border-success/40 bg-success-soft hover:border-success text-left transition-all shadow-warm-sm"
          >
            <div className="flex items-center justify-between text-success font-bold text-xs">
              <span>Clean Tender Draft</span>
              <span className="text-[10px] font-mono">RITES</span>
            </div>
            <p className="text-xs text-ink-700 mt-1 font-medium">Fully conforming IS 456:2000 & IS 383:2016 draft</p>
          </button>
        </div>
      </div>

      {/* ── 3. Tender Input Area ────────────────────────────────────────────── */}
      <div className="p-6 sm:p-8 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-5">
        <div className="flex items-center gap-4 border-b border-border-default pb-3">
          <button
            type="button"
            onClick={() => setInputMode('text')}
            className={`pb-2 text-xs font-bold border-b-2 transition-all ${
              inputMode === 'text'
                ? 'border-brand text-brand'
                : 'border-transparent text-ink-500 hover:text-ink-900'
            }`}
          >
            Paste Specification Draft Text
          </button>
          <button
            type="button"
            onClick={() => setInputMode('document')}
            className={`pb-2 text-xs font-bold border-b-2 transition-all ${
              inputMode === 'document'
                ? 'border-brand text-brand'
                : 'border-transparent text-ink-500 hover:text-ink-900'
            }`}
          >
            Uploaded Document ID
          </button>
        </div>

        {inputMode === 'text' ? (
          <textarea
            rows={6}
            value={tenderText}
            onChange={(e) => setTenderText(e.target.value)}
            placeholder="Paste draft tender technical specifications, bill of quantities, or IS references here..."
            className="w-full px-4 py-3 rounded-xl border border-border-strong bg-bg-base/50 text-xs text-ink-900 placeholder-ink-500 focus:outline-none focus:border-brand font-mono shadow-inner resize-none"
          />
        ) : (
          <input
            type="text"
            value={documentId}
            onChange={(e) => setDocumentId(e.target.value)}
            placeholder="Enter uploaded document ID (e.g. doc_03a4535a)..."
            className="w-full px-4 py-3 rounded-xl border border-border-strong bg-bg-base/50 text-xs font-mono text-ink-900 placeholder-ink-500 focus:outline-none focus:border-brand"
          />
        )}

        <div className="flex justify-end pt-1">
          <button
            onClick={handleValidate}
            disabled={validating}
            className="px-8 py-3 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-warm flex items-center gap-2 disabled:opacity-50"
          >
            {validating ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileCheck2 className="w-4 h-4" />}
            <span>Validate Specification Draft</span>
          </button>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <Alert variant="error" title="Audit Validation Notice">
          {error}
        </Alert>
      )}

      {/* ── 4. Audit Report Findings & Verdict ────────────────────────────── */}
      {report && (
        <div className="space-y-6 animate-slide-up">
          {/* Overall Verdict Banner */}
          {(() => {
            const isReady = report.overall_status === 'NO_BLOCKING_ISSUES_DETECTED';
            const isAmendment = report.overall_status === 'REQUIRES_AMENDMENT';
            const verdictText = isReady
              ? 'READY FOR PUBLICATION'
              : isAmendment
              ? 'REQUIRES AMENDMENT'
              : 'OFFICER REVIEW REQUIRED';
            const overallScore = (report as any).overall_score ?? Math.max(
              0,
              100 - (report.summary_counts.CRITICAL * 30 + report.summary_counts.WARNING * 15 + (report.summary_counts.MANUAL_REVIEW_REQUIRED || 0) * 10)
            );

            return (
              <div
                className={`p-6 sm:p-8 rounded-2xl border-2 shadow-warm space-y-4 ${
                  isReady
                    ? 'border-success/60 bg-success-soft/70'
                    : isAmendment
                    ? 'border-danger/60 bg-danger-soft/70'
                    : 'border-warning/60 bg-warning-soft/70'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <span className="text-[11px] font-mono font-bold tracking-wider uppercase text-ink-700">
                      Overall Specification Verdict
                    </span>
                    <h3 className="text-2xl sm:text-3xl font-extrabold font-serif text-ink-900">
                      {verdictText}
                    </h3>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <span className="text-[11px] uppercase font-bold text-ink-700 block">Compliance Score</span>
                      <span className="font-mono text-3xl sm:text-4xl font-extrabold text-ink-900 tabular-nums">
                        {overallScore}/100
                      </span>
                    </div>
                    <ConfidenceMeter score={overallScore} size="md" className="w-28" />
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs border-t border-border-default pt-3">
                  <div>
                    <span className="text-ink-500 block text-[10px] font-bold uppercase">CRITICAL ISSUES:</span>
                    <span className="font-mono font-bold text-danger text-base tabular-nums">
                      {report.summary_counts.CRITICAL}
                    </span>
                  </div>
                  <div>
                    <span className="text-ink-500 block text-[10px] font-bold uppercase">WARNINGS:</span>
                    <span className="font-mono font-bold text-warning text-base tabular-nums">
                      {report.summary_counts.WARNING}
                    </span>
                  </div>
                  <div>
                    <span className="text-ink-500 block text-[10px] font-bold uppercase">CHECKS EVALUATED:</span>
                    <span className="font-mono font-bold text-brand text-base tabular-nums">
                      {report.checks_completed?.length || report.findings?.length || 0}
                    </span>
                  </div>
                  <div>
                    <span className="text-ink-500 block text-[10px] font-bold uppercase">DOWNLOAD REPORT:</span>
                    <a
                      href={api.getValidationDownloadUrl(report.validation_id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-bold text-brand hover:underline flex items-center gap-1 mt-0.5"
                    >
                      <Download className="w-3.5 h-3.5" /> Certificate
                    </a>
                  </div>
                </div>
              </div>
            );
          })()}

          {/* Rules A-E Findings List */}
          <div className="p-6 sm:p-8 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-default pb-3">
              <h4 className="text-base font-bold font-serif text-ink-900">
                Rule Evaluation Findings ({filteredFindings.length})
              </h4>

              <div className="flex gap-1.5 text-xs">
                {(['ALL', 'CRITICAL', 'WARNING', 'INFO', 'MANUAL_REVIEW_REQUIRED'] as const).map((sev) => (
                  <button
                    key={sev}
                    onClick={() => setFilterSeverity(sev)}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                      filterSeverity === sev
                        ? 'bg-brand text-white shadow-warm-sm'
                        : 'bg-bg-sunken text-ink-700 hover:text-ink-900'
                    }`}
                  >
                    {sev === 'MANUAL_REVIEW_REQUIRED' ? 'MANUAL' : sev}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              {filteredFindings.map((finding) => {
                const isExpanded = expandedFinding === finding.id;
                return (
                  <div
                    key={finding.id}
                    className="p-5 rounded-xl border border-border-default bg-bg-base/40 space-y-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1.5">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`px-2.5 py-0.5 rounded text-[11px] font-bold uppercase ${
                              finding.severity === 'CRITICAL'
                                ? 'bg-danger text-white'
                                : finding.severity === 'WARNING'
                                ? 'bg-warning-soft text-warning border border-warning/40'
                                : 'bg-info-soft text-info border border-info/40'
                            }`}
                          >
                            {finding.severity}
                          </span>
                          <span className="font-mono text-xs font-bold text-ink-700">
                            {finding.rule_id}
                          </span>
                          {finding.standard_identifier && (
                            <CodeChip code={finding.standard_identifier} variant="primary" />
                          )}
                        </div>
                        <p className="font-bold text-sm text-ink-900">
                          {finding.rule_name || finding.rule_id}
                        </p>
                      </div>

                      <button
                        onClick={() => setExpandedFinding(isExpanded ? null : finding.id)}
                        className="text-ink-500 hover:text-ink-900 p-1"
                      >
                        {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                      </button>
                    </div>

                    <p className="text-xs text-ink-700 leading-relaxed font-medium">
                      {finding.description}
                    </p>

                    {/* Excerpt if present */}
                    {finding.clause_excerpt && (
                      <div className="p-3 rounded-lg bg-bg-surface font-mono text-xs text-ink-900 border-l-4 border-l-accent shadow-warm-sm">
                        <span className="text-[10px] uppercase font-bold text-ink-500 block font-sans">Cited Clause:</span>
                        {finding.clause_excerpt}
                      </div>
                    )}

                    {/* Corrective Action */}
                    {finding.recommended_action && (
                      <div className="p-3.5 rounded-xl border border-info/40 bg-info-soft/40 text-xs text-ink-900 space-y-1">
                        <span className="font-bold block text-[10px] uppercase text-info">Recommended Action:</span>
                        <p className="font-medium">{finding.recommended_action}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* ── 5. Procurement Officer Review Sign-Off ────────────────────── */}
          <div className="p-6 sm:p-8 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-4">
            <h4 className="text-base font-bold font-serif text-ink-900 flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-brand" />
              Procurement Officer Final Sign-Off & Attestation
            </h4>

            {reviewSuccessMsg && (
              <Alert variant="verified-knowledge" title="Decision Recorded">
                {reviewSuccessMsg}
              </Alert>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="space-y-1">
                <label className="font-bold text-ink-700">Procurement Officer ID / Designation</label>
                <input
                  type="text"
                  value={officerId}
                  onChange={(e) => setOfficerId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-border-strong bg-bg-base text-ink-900 focus:outline-none focus:border-brand font-mono"
                />
              </div>

              <div className="space-y-1">
                <label className="font-bold text-ink-700">Official Decision</label>
                <select
                  value={reviewDecision}
                  onChange={(e) => setReviewDecision(e.target.value as OfficerDecisionType)}
                  className="w-full px-3 py-2 rounded-xl border border-border-strong bg-bg-base text-ink-900 focus:outline-none focus:border-brand font-bold"
                >
                  <option value="APPROVED_WITH_NOTES">Approved with Compliance Notes</option>
                  <option value="AMENDMENT_REQUESTED">Amendment Requested Before Publishing</option>
                  <option value="REJECTED">Rejected — High Statutory Risk</option>
                </select>
              </div>
            </div>

            <div className="space-y-1 text-xs">
              <label className="font-bold text-ink-700">Official Attestation Comments</label>
              <textarea
                rows={2}
                value={reviewComments}
                onChange={(e) => setReviewComments(e.target.value)}
                placeholder="State officer justification or amendments required before tender publication..."
                className="w-full px-3 py-2 rounded-xl border border-border-strong bg-bg-base text-ink-900 placeholder-ink-500 focus:outline-none focus:border-brand"
              />
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={handleOfficerReviewSubmit}
                disabled={submittingReview}
                className="px-6 py-2.5 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-warm flex items-center gap-2 disabled:opacity-50"
              >
                {submittingReview ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserCheck className="w-4 h-4" />}
                <span>Record Official Attestation</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

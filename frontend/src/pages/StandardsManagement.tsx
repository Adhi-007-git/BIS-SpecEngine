import React, { useEffect, useState, useCallback } from 'react';
import {
  Layers,
  Plus,
  RefreshCw,
  Loader2,
  History,
  Search,
  Edit,
  ArrowRight,
  Database,
  Calendar,
  Check
} from 'lucide-react';
import { api } from '../services/api';
import { VersionHistoryItem, StandardManageAddRequest } from '../types';
import { Badge, CodeChip, EmptyState, Modal, PageHeader } from '../components/ui';

interface AddFormState {
  standard_number: string;
  title: string;
  scope: string;
  edition: string;
  status: string;
  source: string;
  department: string;
  keywords: string;
  supersedes: string;
  normative_references: string;
  test_methods: string;
}

const INITIAL_FORM: AddFormState = {
  standard_number: '',
  title: '',
  scope: '',
  edition: '',
  status: 'Active',
  source: 'Bureau of Indian Standards',
  department: '',
  keywords: '',
  supersedes: '',
  normative_references: '',
  test_methods: '',
};

export const StandardsManagement: React.FC = () => {
  const [standards, setStandards] = useState<Array<{ standard_number: string; title: string; status: string; edition?: string }>>([]);
  const [standardsLoading, setStandardsLoading] = useState(true);
  const [versionHistory, setVersionHistory] = useState<VersionHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [formState, setFormState] = useState<AddFormState>(INITIAL_FORM);
  const [formLoading, setFormLoading] = useState(false);
  const [reindexLoading, setReindexLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [modifyStd, setModifyStd] = useState<{ number: string; status: string; supersedes: string } | null>(null);
  const [modifyLoading, setModifyLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [toastMsg, setToastMsg] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error') => {
    setToastMsg({ message, type });
    setTimeout(() => setToastMsg(null), 4500);
  };

  const fetchStandards = useCallback(async () => {
    setStandardsLoading(true);
    try {
      const data = await api.listStandards();
      setStandards(data);
    } catch {
      showToast('Could not load standards list.', 'error');
    } finally {
      setStandardsLoading(false);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const data = await api.getVersionHistory();
      setVersionHistory(data);
    } catch {
      // Non-critical
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStandards();
    fetchHistory();
  }, [fetchStandards, fetchHistory]);

  const handleFieldChange = (field: keyof AddFormState, value: string) => {
    setFormState((prev) => ({ ...prev, [field]: value }));
  };

  const handleAddStandard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formState.standard_number.trim() || !formState.title.trim()) {
      showToast('Standard Number and Title are required.', 'error');
      return;
    }

    setFormLoading(true);
    try {
      const payload: StandardManageAddRequest = {
        standard_number: formState.standard_number.trim(),
        title: formState.title.trim(),
        scope: formState.scope || undefined,
        edition: formState.edition || undefined,
        status: formState.status || 'Active',
        source: formState.source || 'Bureau of Indian Standards',
        department: formState.department || undefined,
        keywords: formState.keywords ? formState.keywords.split(',').map((k) => k.trim()).filter(Boolean) : [],
        supersedes: formState.supersedes.trim() || undefined,
        normative_references: formState.normative_references ? formState.normative_references.split(',').map((s) => s.trim()).filter(Boolean) : [],
        test_methods: formState.test_methods ? formState.test_methods.split(',').map((s) => s.trim()).filter(Boolean) : [],
      };

      const res = await api.addStandard(payload);
      showToast(res.message || `Standard ${payload.standard_number} added.`, 'success');
      setFormState(INITIAL_FORM);
      setShowAddModal(false);
      fetchStandards();
      fetchHistory();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to add standard.', 'error');
    } finally {
      setFormLoading(false);
    }
  };

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modifyStd) return;
    setModifyLoading(true);
    try {
      const res = await api.updateStandard(modifyStd.number, {
        status: modifyStd.status,
        supersedes: modifyStd.supersedes || undefined,
      });
      showToast(res.message || `Standard ${modifyStd.number} updated to ${modifyStd.status}.`, 'success');
      setModifyStd(null);
      fetchStandards();
      fetchHistory();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to update standard status.', 'error');
    } finally {
      setModifyLoading(false);
    }
  };

  const handleReindex = async () => {
    setReindexLoading(true);
    try {
      const res = await api.reindexSearch();
      showToast(res.message || 'Vector and lexical indices refreshed successfully.', 'success');
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Reindexing failed.', 'error');
    } finally {
      setReindexLoading(false);
    }
  };

  const filteredStandards = standards.filter((s) => {
    const matchesSearch =
      s.standard_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus =
      statusFilter === 'ALL' ||
      s.status.toLowerCase() === statusFilter.toLowerCase();
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-8">
      {/* Toast */}
      {toastMsg && (
        <div className="fixed bottom-6 right-6 z-50 p-4 rounded-xl shadow-warm-lg bg-bg-surface border-2 border-brand text-xs font-bold text-ink-900 animate-slide-up">
          {toastMsg.message}
        </div>
      )}

      {/* ── 1. Page Header ─────────────────────────────────────────────────── */}
      <PageHeader
        title="Standards Management Registry"
        description="Official catalogue of 21 verified Bureau of Indian Standards (BIS) records. Add standards, update lifecycle states, and re-index vector spaces."
        badge={
          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-bg-sunken text-ink-900 border border-border-default">
            {standards.length} Curated Records
          </span>
        }
        action={
          <div className="flex items-center gap-2">
            <button
              onClick={handleReindex}
              disabled={reindexLoading}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-border-default bg-bg-surface hover:bg-bg-sunken text-xs font-bold text-ink-900 transition-colors shadow-warm-sm"
              title="Refresh vector embeddings and lexical keywords in search index"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${reindexLoading ? 'animate-spin' : ''}`} />
              <span>Re-index Vectors</span>
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-warm"
            >
              <Plus className="w-4 h-4" />
              <span>Add Standard</span>
            </button>
          </div>
        }
      />

      {/* ── 2. Filters & Search ────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-1.5 bg-bg-sunken p-1.5 rounded-2xl border border-border-default overflow-x-auto w-full sm:w-auto">
          {['ALL', 'Active', 'Superseded', 'Withdrawn'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                statusFilter === st
                  ? 'bg-bg-surface text-ink-900 border border-border-strong shadow-warm-sm'
                  : 'text-ink-500 hover:text-ink-900'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-2.5 w-4 h-4 text-ink-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search standards by number or title..."
            className="w-full pl-10 pr-4 py-2 rounded-xl border border-border-strong bg-bg-surface text-xs text-ink-900 placeholder-ink-500 focus:outline-none focus:border-brand"
          />
        </div>
      </div>

      {/* ── 3. Data Table of Standards ─────────────────────────────────────── */}
      <div className="rounded-2xl border border-border-default bg-bg-surface shadow-warm overflow-hidden">
        {standardsLoading ? (
          <div className="p-12 text-center space-y-3">
            <Loader2 className="w-8 h-8 text-brand animate-spin mx-auto" />
            <p className="text-xs font-bold text-ink-500 font-mono">Loading official standards registry...</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-bg-sunken border-b border-border-default text-ink-900 uppercase font-bold text-[11px] tracking-wider sticky top-0">
                <tr className="h-12">
                  <th className="px-5 py-3">Standard Number</th>
                  <th className="px-5 py-3">Official Title</th>
                  <th className="px-5 py-3">Edition</th>
                  <th className="px-5 py-3">Lifecycle Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-default">
                {filteredStandards.map((std, idx) => (
                  <tr
                    key={std.standard_number}
                    className={`h-[52px] transition-colors hover:bg-bg-sunken/40 ${
                      idx % 2 === 1 ? 'bg-bg-base/30' : 'bg-bg-surface'
                    }`}
                  >
                    <td className="px-5 py-3 font-mono font-bold whitespace-nowrap">
                      <CodeChip code={std.standard_number} variant="primary" />
                    </td>
                    <td className="px-5 py-3 font-medium text-ink-900 max-w-md truncate">
                      {std.title}
                    </td>
                    <td className="px-5 py-3 font-mono text-ink-700 whitespace-nowrap">
                      {std.edition || 'Current'}
                    </td>
                    <td className="px-5 py-3 whitespace-nowrap">
                      <Badge
                        variant={
                          std.status.toLowerCase() === 'active'
                            ? 'active'
                            : std.status.toLowerCase() === 'superseded'
                            ? 'superseded'
                            : 'withdrawn'
                        }
                      />
                    </td>
                    <td className="px-5 py-3 text-right whitespace-nowrap space-x-2">
                      <button
                        onClick={() =>
                          setModifyStd({
                            number: std.standard_number,
                            status: std.status,
                            supersedes: '',
                          })
                        }
                        className="px-2.5 py-1 rounded-lg border border-border-default bg-bg-surface hover:bg-bg-sunken text-[11px] font-bold text-ink-900 transition-colors shadow-warm-sm"
                      >
                        Modify Status
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── 4. Vertical Version History Timeline ───────────────────────────── */}
      <div className="p-6 sm:p-8 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-5">
        <div className="flex items-center justify-between border-b border-border-default pb-3">
          <h3 className="text-base font-bold font-serif text-ink-900 flex items-center gap-2">
            <History className="w-5 h-5 text-brand" />
            Standard Version & Supersession History
          </h3>
          <span className="text-xs font-mono font-bold text-ink-500">
            {versionHistory.length} Recorded Changes
          </span>
        </div>

        {historyLoading ? (
          <div className="p-6 text-center text-xs text-ink-500">Loading version transitions...</div>
        ) : versionHistory.length === 0 ? (
          <p className="text-xs text-ink-500 italic">No historical version changes catalogued yet.</p>
        ) : (
          <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-border-strong">
            {versionHistory.map((v, i) => (
              <div key={i} className="relative text-xs space-y-1">
                <span className="absolute -left-6 top-1.5 w-2.5 h-2.5 rounded-full bg-brand border-2 border-bg-surface" />
                <div className="flex flex-wrap items-center gap-2 font-mono">
                  <strong className="text-ink-900">{v.standard_number}</strong>
                  <span className="text-ink-500">({v.change_type})</span>
                  <span className="text-[11px] text-ink-500">{v.change_date}</span>
                </div>
                <p className="text-ink-700 font-sans">
                  Status transition:{' '}
                  <strong className="text-ink-900">{v.status}</strong>
                  {v.new_version && ` → New version: ${v.new_version}`}
                  {v.notes && ` • Note: ${v.notes}`}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── 5. Add Standard Modal ──────────────────────────────────────────── */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="Add New Standard to Catalogue"
        subtitle="Registers an official Indian Standard in the verified repository and schedules vector indexing."
      >
        <form onSubmit={handleAddStandard} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="space-y-1">
              <label className="font-bold text-ink-700">Standard Number <span className="text-danger">*</span></label>
              <input
                type="text"
                required
                value={formState.standard_number}
                onChange={(e) => handleFieldChange('standard_number', e.target.value)}
                placeholder="e.g. IS 2062:2011"
                className="w-full px-3 py-2 rounded-lg border border-border-strong bg-bg-base text-ink-900 font-mono focus:outline-none focus:border-brand"
              />
            </div>
            <div className="space-y-1">
              <label className="font-bold text-ink-700">Edition</label>
              <input
                type="text"
                value={formState.edition}
                onChange={(e) => handleFieldChange('edition', e.target.value)}
                placeholder="e.g. Fourth Revision"
                className="w-full px-3 py-2 rounded-lg border border-border-strong bg-bg-base text-ink-900 focus:outline-none focus:border-brand"
              />
            </div>
          </div>

          <div className="space-y-1 text-xs">
            <label className="font-bold text-ink-700">Official Title <span className="text-danger">*</span></label>
            <input
              type="text"
              required
              value={formState.title}
              onChange={(e) => handleFieldChange('title', e.target.value)}
              placeholder="e.g. Hot Rolled Medium and High Tensile Structural Steel"
              className="w-full px-3 py-2 rounded-lg border border-border-strong bg-bg-base text-ink-900 focus:outline-none focus:border-brand"
            />
          </div>

          <div className="space-y-1 text-xs">
            <label className="font-bold text-ink-700">Standard Scope & Summary</label>
            <textarea
              rows={3}
              value={formState.scope}
              onChange={(e) => handleFieldChange('scope', e.target.value)}
              placeholder="Scope description for semantic embedding..."
              className="w-full px-3 py-2 rounded-lg border border-border-strong bg-bg-base text-ink-900 focus:outline-none focus:border-brand"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="space-y-1">
              <label className="font-bold text-ink-700">Lifecycle Status</label>
              <select
                value={formState.status}
                onChange={(e) => handleFieldChange('status', e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border-strong bg-bg-base text-ink-900 focus:outline-none focus:border-brand"
              >
                <option value="Active">Active</option>
                <option value="Superseded">Superseded</option>
                <option value="Withdrawn">Withdrawn</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="font-bold text-ink-700">Supersedes Code</label>
              <input
                type="text"
                value={formState.supersedes}
                onChange={(e) => handleFieldChange('supersedes', e.target.value)}
                placeholder="e.g. IS 2062:2006"
                className="w-full px-3 py-2 rounded-lg border border-border-strong bg-bg-base text-ink-900 font-mono focus:outline-none focus:border-brand"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-border-default">
            <button
              type="button"
              onClick={() => setShowAddModal(false)}
              className="px-4 py-2 rounded-xl border border-border-default text-xs font-semibold text-ink-700 hover:bg-bg-sunken"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={formLoading}
              className="px-5 py-2 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold shadow-warm disabled:opacity-50"
            >
              {formLoading ? 'Adding...' : 'Add Standard'}
            </button>
          </div>
        </form>
      </Modal>

      {/* ── 6. Update Status Modal ─────────────────────────────────────────── */}
      <Modal
        isOpen={!!modifyStd}
        onClose={() => setModifyStd(null)}
        title={`Update Status: ${modifyStd?.number}`}
        subtitle="Alter the lifecycle status in the verified catalogue and trigger an audit history entry."
      >
        {modifyStd && (
          <form onSubmit={handleUpdateStatus} className="space-y-4 text-xs">
            <div className="space-y-1">
              <label className="font-bold text-ink-700">New Lifecycle Status</label>
              <select
                value={modifyStd.status}
                onChange={(e) => setModifyStd({ ...modifyStd, status: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-border-strong bg-bg-base text-ink-900 focus:outline-none focus:border-brand"
              >
                <option value="Active">Active</option>
                <option value="Superseded">Superseded</option>
                <option value="Withdrawn">Withdrawn</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="font-bold text-ink-700">Superseding Standard (if applicable)</label>
              <input
                type="text"
                value={modifyStd.supersedes}
                onChange={(e) => setModifyStd({ ...modifyStd, supersedes: e.target.value })}
                placeholder="e.g. IS 456:2000"
                className="w-full px-3 py-2 rounded-lg border border-border-strong bg-bg-base text-ink-900 font-mono focus:outline-none focus:border-brand"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-border-default">
              <button
                type="button"
                onClick={() => setModifyStd(null)}
                className="px-4 py-2 rounded-xl border border-border-default text-xs font-semibold text-ink-700 hover:bg-bg-sunken"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={modifyLoading}
                className="px-5 py-2 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold shadow-warm disabled:opacity-50"
              >
                {modifyLoading ? 'Updating...' : 'Save Lifecycle Transition'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};

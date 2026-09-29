import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AppShell } from './layouts/AppShell';
import { Dashboard } from './pages/Dashboard';
import { StandardSearch } from './pages/StandardSearch';
import { UploadTender } from './pages/UploadTender';
import { RecommendationResults } from './pages/RecommendationResults';
import { StandardDetails } from './pages/StandardDetails';
import { EvidenceViewer } from './pages/EvidenceViewer';
import { KnowledgeGraphView } from './pages/KnowledgeGraphView';
import { EngineerReview } from './pages/EngineerReview';
import { StandardsManagement } from './pages/StandardsManagement';
import { PrePublishValidation } from './pages/PrePublishValidation';
import { useScrollReveal } from './hooks/useScrollReveal';

const AppContent: React.FC = () => {
  useScrollReveal();
  const location = useLocation();

  return (
    <AppShell>
      {/* Route Views with smooth enter */}
      <div key={location.pathname} className="animate-fade-in">
        <Routes>
          <Route path="/"                      element={<Dashboard />} />
          <Route path="/search"                element={<StandardSearch />} />
          <Route path="/upload"                element={<UploadTender />} />
          <Route path="/results"               element={<RecommendationResults />} />
          <Route path="/standards/:standardId" element={<StandardDetails />} />
          <Route path="/evidence"              element={<EvidenceViewer />} />
          <Route path="/graph/:standardId?"    element={<KnowledgeGraphView />} />
          <Route path="/review"                element={<EngineerReview />} />
          <Route path="/manage"                element={<StandardsManagement />} />
          <Route path="/pre-publish"           element={<PrePublishValidation />} />
          <Route path="*"                      element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </AppShell>
  );
};

export const App: React.FC = () => {
  return (
    <Router>
      <AppContent />
    </Router>
  );
};

export default App;

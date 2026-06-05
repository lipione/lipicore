import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ChatAssistant from './pages/ChatAssistant';
import Messenger from './pages/Messenger';
import EmployeeDirectory from './pages/EmployeeDirectory';
import MarketAndTime from './pages/MarketAndTime';
import Notifications from './pages/Notifications';
import CeoMessages from './pages/CeoMessages';
import StaffInbox from './pages/StaffInbox';
import KnowledgeGaps from './pages/KnowledgeGaps';
import PolicyChangeCenter from './pages/PolicyChangeCenter';
import BankingWorkflowWorkspace from './pages/BankingWorkflowWorkspace';
import AuditEvidence from './pages/AuditEvidence';
import Documents from './pages/Documents';
import OcrExtraction from './pages/OcrExtraction';
import Features from './pages/Features';
import Tasks from './pages/Tasks';
import Users from './pages/Users';
import AuditLogs from './pages/AuditLogs';
import Settings from './pages/Settings';
import SessionHistory from './pages/SessionHistory';
import Analytics from './pages/Analytics';
import Reports from './pages/Reports';
import HelpCenter from './pages/HelpCenter';
import EvaluationCenter from './pages/EvaluationCenter';
import ModelLab from './pages/ModelLab';
import AdminSecurity from './pages/AdminSecurity';
import ComplianceRisk from './pages/ComplianceRisk';
import ComplianceWorkspace from './pages/ComplianceWorkspace';
import LipiCoreProcessNavigator from './pages/LipiCoreProcessNavigator';
import SuperAdminFeatureControls from './pages/SuperAdminFeatureControls';
import MainLayout from './layouts/MainLayout';
import { FeatureGate, FeatureUnavailable } from './contexts/FeatureFlagContext';

// Auth is now httpOnly cookie — we use the cached user profile in localStorage
// as a lightweight client-side indicator. If the cookie is missing/expired the
// first protected API call returns 401 and axios redirects to /login.
const ProtectedRoute = ({ children }) => {
  const user = localStorage.getItem('user');
  return user ? children : <Navigate to="/login" replace />;
};

function App() {
  const isAuthenticated = !!localStorage.getItem('user');

  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Landing />} />
        <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />} />

        {/* Protected routes */}
        <Route path="/" element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
          <Route path="dashboard"      element={<Dashboard />} />
          <Route path="chat"           element={<ChatAssistant />} />
          <Route path="employees"      element={<FeatureGate featureKey="employee_directory" fallback={<FeatureUnavailable featureKey="employee_directory" />}><EmployeeDirectory /></FeatureGate>} />
          <Route path="market-time"    element={<FeatureGate featureKey="market_time" fallback={<FeatureUnavailable featureKey="market_time" />}><MarketAndTime /></FeatureGate>} />
          <Route path="notifications"  element={<FeatureGate featureKey="notifications" fallback={<FeatureUnavailable featureKey="notifications" />}><Notifications /></FeatureGate>} />
          <Route path="ceo-messages"   element={<FeatureGate featureKey="ceo_messages" fallback={<FeatureUnavailable featureKey="ceo_messages" />}><CeoMessages /></FeatureGate>} />
          <Route path="inbox"          element={<FeatureGate featureKey="staff_inbox" fallback={<FeatureUnavailable featureKey="staff_inbox" />}><StaffInbox /></FeatureGate>} />
          <Route path="messenger"      element={<FeatureGate featureKey="staff_inbox" fallback={<FeatureUnavailable featureKey="staff_inbox" />}><Messenger /></FeatureGate>} />
          <Route path="knowledge-gaps" element={<FeatureGate featureKey="knowledge_gaps" fallback={<FeatureUnavailable featureKey="knowledge_gaps" />}><KnowledgeGaps /></FeatureGate>} />
          <Route path="policy-changes" element={<FeatureGate featureKey="policy_changes" fallback={<FeatureUnavailable featureKey="policy_changes" />}><PolicyChangeCenter /></FeatureGate>} />
          <Route path="complaints"     element={<FeatureGate featureKey="complaint_workspace" fallback={<FeatureUnavailable featureKey="complaint_workspace" />}><BankingWorkflowWorkspace title="Complaint Workspace" description="Draft policy-backed customer complaint responses and keep each response case ready for follow-up." endpoint="/complaint-workspace" /></FeatureGate>} />
          <Route path="circular-impact" element={<FeatureGate featureKey="circular_impact_analyzer" fallback={<FeatureUnavailable featureKey="circular_impact_analyzer" />}><BankingWorkflowWorkspace title="Circular Impact Analyzer" description="Assess new circulars against products, branches, and operational workflows before staff action." endpoint="/circular-impact" /></FeatureGate>} />
          <Route path="branch-responses" element={<FeatureGate featureKey="branch_response_builder" fallback={<FeatureUnavailable featureKey="branch_response_builder" />}><BankingWorkflowWorkspace title="Branch Response Builder" description="Prepare consistent branch operation responses with clear source facts and next steps." endpoint="/branch-responses" /></FeatureGate>} />
          <Route path="kyc-case-prep"  element={<FeatureGate featureKey="kyc_case_prep" fallback={<FeatureUnavailable featureKey="kyc_case_prep" />}><BankingWorkflowWorkspace title="KYC Case Prep" description="Assemble KYC review packets, exception notes, and document readiness summaries." endpoint="/kyc-case-prep" /></FeatureGate>} />
          <Route path="checklists"     element={<FeatureGate featureKey="checklist_validator" fallback={<FeatureUnavailable featureKey="checklist_validator" />}><BankingWorkflowWorkspace title="Checklist Validator" description="Compare submitted items against required bank workflow checklists and highlight missing evidence." endpoint="/checklist-workspace" checklist /></FeatureGate>} />
          <Route path="audit-evidence" element={<FeatureGate featureKey="audit_evidence_pack" fallback={<FeatureUnavailable featureKey="audit_evidence_pack" />}><AuditEvidence /></FeatureGate>} />
          <Route path="documents"      element={<Documents />} />
          <Route path="ocr"            element={<OcrExtraction />} />
          <Route path="document-review" element={<Navigate to="/ocr" replace />} />
          <Route path="features"       element={<Features />} />
          <Route path="tasks"          element={<Tasks />} />
          <Route path="support-desk"   element={<Navigate to="/ocr" replace />} />
          <Route path="loan-support"   element={<Navigate to="/ocr" replace />} />
          <Route path="sessions"       element={<SessionHistory />} />
          <Route path="analytics"      element={<Analytics />} />
          <Route path="evaluations"    element={<EvaluationCenter />} />
          <Route path="model-lab"      element={<ModelLab />} />
          <Route path="users"          element={<Users />} />
          <Route path="audit-logs"     element={<AuditLogs />} />
          <Route path="settings"       element={<Settings />} />
          <Route path="help"           element={<HelpCenter />} />
          <Route path="admin/security"    element={<AdminSecurity />} />
          <Route path="admin/users"       element={<Users />} />
          <Route path="admin/features"    element={<SuperAdminFeatureControls />} />
          <Route path="admin/settings"    element={<Settings />} />
          <Route path="compliance"        element={<ComplianceRisk />} />
          <Route path="compliance-workspace" element={<ComplianceWorkspace />} />
          <Route path="regulatory"        element={<ComplianceRisk />} />
          <Route path="reports"           element={<Reports />} />
          <Route path="audit"             element={<AuditLogs />} />
          <Route path="process-navigator" element={<LipiCoreProcessNavigator />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;

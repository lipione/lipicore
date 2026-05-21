import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ChatAssistant from './pages/ChatAssistant';
import Documents from './pages/Documents';
import DocumentReview from './pages/DocumentReview';
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
import LoanSupport from './pages/LoanSupport';
import SupportDesk from './pages/SupportDesk';
import LipiCoreProcessNavigator from './pages/LipiCoreProcessNavigator';
import MainLayout from './layouts/MainLayout';

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
          <Route path="documents"      element={<Documents />} />
          <Route path="document-review" element={<DocumentReview />} />
          <Route path="features"       element={<Features />} />
          <Route path="tasks"          element={<Tasks />} />
          <Route path="support-desk"   element={<SupportDesk />} />
          <Route path="loan-support"   element={<LoanSupport />} />
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

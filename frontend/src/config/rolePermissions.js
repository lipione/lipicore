export const ROLES = {
  STAFF_USER: 'staff_user',
  COMPLIANCE_USER: 'compliance_user',
  COMPLIANCE_OFFICER: 'compliance_officer',
  DOCUMENT_REVIEWER: 'document_reviewer',
  AUDITOR: 'auditor',
  DATA_AUDITOR: 'data_auditor',
  BANK_ADMIN: 'bank_admin',
  SUPER_ADMIN: 'super_admin',
};

export const ROLE_LABELS = {
  staff_user: 'Staff',
  compliance_user: 'Compliance',
  compliance_officer: 'Compliance Officer',
  document_reviewer: 'Reviewer',
  auditor: 'Auditor',
  data_auditor: 'Data Auditor',
  bank_admin: 'Bank Admin',
  super_admin: 'Super Admin',
};

export const ROLE_COLORS = {
  staff_user: { bg: 'bg-slate-100', text: 'text-slate-700', border: 'border-slate-300' },
  compliance_user: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  compliance_officer: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  document_reviewer: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
  auditor: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' },
  data_auditor: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' },
  bank_admin: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
  super_admin: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
};

// Ordered from lowest to highest privilege
const ROLE_RANK = {
  staff_user: 1,
  compliance_user: 2,
  compliance_officer: 2,
  document_reviewer: 3,
  auditor: 4,
  data_auditor: 4,
  bank_admin: 5,
  super_admin: 6,
};

export const PERMISSIONS = {
  // Chat & RAG
  USE_CHAT: 'use_chat',
  USE_CHAT_FILE_UPLOAD: 'use_chat_file_upload',
  USE_MESSENGER: 'use_messenger',

  // Documents
  VIEW_DOCUMENTS: 'view_documents',
  UPLOAD_DOCUMENTS: 'upload_documents',
  DELETE_DOCUMENTS: 'delete_documents',
  MANAGE_DOCUMENT_LIBRARY: 'manage_document_library',

  // Process Navigator
  VIEW_PROCESS_NAVIGATOR: 'view_process_navigator',

  // Reports & Analytics
  VIEW_ANALYTICS: 'view_analytics',
  VIEW_EVALUATIONS: 'view_evaluations',
  VIEW_REPORTS: 'view_reports',
  EXPORT_REPORTS: 'export_reports',

  // Audit
  VIEW_AUDIT_LOGS: 'view_audit_logs',
  EXPORT_AUDIT_LOGS: 'export_audit_logs',

  // Compliance
  VIEW_REGULATORY_LIBRARY: 'view_regulatory_library',
  MANAGE_COMPLIANCE: 'manage_compliance',

  // Administration
  MANAGE_USERS: 'manage_users',
  MANAGE_ROLES: 'manage_roles',
  VIEW_SYSTEM_SETTINGS: 'view_system_settings',
  MANAGE_SYSTEM_SETTINGS: 'manage_system_settings',
  VIEW_TASKS: 'view_tasks',
};

const ROLE_PERMISSIONS = {
  staff_user: [
    PERMISSIONS.USE_CHAT,
    PERMISSIONS.USE_CHAT_FILE_UPLOAD,
    PERMISSIONS.USE_MESSENGER,
    PERMISSIONS.VIEW_DOCUMENTS,
    PERMISSIONS.VIEW_PROCESS_NAVIGATOR,
  ],
  compliance_user: [
    PERMISSIONS.USE_CHAT,
    PERMISSIONS.USE_CHAT_FILE_UPLOAD,
    PERMISSIONS.USE_MESSENGER,
    PERMISSIONS.VIEW_DOCUMENTS,
    PERMISSIONS.UPLOAD_DOCUMENTS,
    PERMISSIONS.VIEW_PROCESS_NAVIGATOR,
    PERMISSIONS.VIEW_REGULATORY_LIBRARY,
    PERMISSIONS.MANAGE_COMPLIANCE,
    PERMISSIONS.VIEW_REPORTS,
  ],
  compliance_officer: [
    PERMISSIONS.USE_CHAT,
    PERMISSIONS.USE_CHAT_FILE_UPLOAD,
    PERMISSIONS.USE_MESSENGER,
    PERMISSIONS.VIEW_DOCUMENTS,
    PERMISSIONS.UPLOAD_DOCUMENTS,
    PERMISSIONS.VIEW_PROCESS_NAVIGATOR,
    PERMISSIONS.VIEW_REGULATORY_LIBRARY,
    PERMISSIONS.MANAGE_COMPLIANCE,
    PERMISSIONS.VIEW_REPORTS,
    PERMISSIONS.VIEW_TASKS,
  ],
  document_reviewer: [
    PERMISSIONS.USE_CHAT,
    PERMISSIONS.USE_CHAT_FILE_UPLOAD,
    PERMISSIONS.USE_MESSENGER,
    PERMISSIONS.VIEW_DOCUMENTS,
    PERMISSIONS.UPLOAD_DOCUMENTS,
    PERMISSIONS.DELETE_DOCUMENTS,
    PERMISSIONS.MANAGE_DOCUMENT_LIBRARY,
    PERMISSIONS.VIEW_PROCESS_NAVIGATOR,
    PERMISSIONS.VIEW_REPORTS,
  ],
  auditor: [
    PERMISSIONS.USE_CHAT,
    PERMISSIONS.USE_CHAT_FILE_UPLOAD,
    PERMISSIONS.USE_MESSENGER,
    PERMISSIONS.VIEW_DOCUMENTS,
    PERMISSIONS.VIEW_PROCESS_NAVIGATOR,
    PERMISSIONS.VIEW_ANALYTICS,
    PERMISSIONS.VIEW_EVALUATIONS,
    PERMISSIONS.VIEW_REPORTS,
    PERMISSIONS.EXPORT_REPORTS,
    PERMISSIONS.VIEW_AUDIT_LOGS,
    PERMISSIONS.EXPORT_AUDIT_LOGS,
    PERMISSIONS.VIEW_REGULATORY_LIBRARY,
    PERMISSIONS.VIEW_TASKS,
  ],
  data_auditor: [
    PERMISSIONS.USE_CHAT,
    PERMISSIONS.USE_CHAT_FILE_UPLOAD,
    PERMISSIONS.USE_MESSENGER,
    PERMISSIONS.VIEW_DOCUMENTS,
    PERMISSIONS.VIEW_PROCESS_NAVIGATOR,
    PERMISSIONS.VIEW_ANALYTICS,
    PERMISSIONS.VIEW_EVALUATIONS,
    PERMISSIONS.VIEW_REPORTS,
    PERMISSIONS.EXPORT_REPORTS,
    PERMISSIONS.VIEW_AUDIT_LOGS,
    PERMISSIONS.EXPORT_AUDIT_LOGS,
    PERMISSIONS.VIEW_REGULATORY_LIBRARY,
    PERMISSIONS.VIEW_TASKS,
  ],
  bank_admin: [
    PERMISSIONS.USE_CHAT,
    PERMISSIONS.USE_CHAT_FILE_UPLOAD,
    PERMISSIONS.USE_MESSENGER,
    PERMISSIONS.VIEW_DOCUMENTS,
    PERMISSIONS.UPLOAD_DOCUMENTS,
    PERMISSIONS.DELETE_DOCUMENTS,
    PERMISSIONS.MANAGE_DOCUMENT_LIBRARY,
    PERMISSIONS.VIEW_PROCESS_NAVIGATOR,
    PERMISSIONS.VIEW_ANALYTICS,
    PERMISSIONS.VIEW_EVALUATIONS,
    PERMISSIONS.VIEW_REPORTS,
    PERMISSIONS.EXPORT_REPORTS,
    PERMISSIONS.VIEW_AUDIT_LOGS,
    PERMISSIONS.EXPORT_AUDIT_LOGS,
    PERMISSIONS.VIEW_REGULATORY_LIBRARY,
    PERMISSIONS.MANAGE_COMPLIANCE,
    PERMISSIONS.MANAGE_USERS,
    PERMISSIONS.VIEW_SYSTEM_SETTINGS,
    PERMISSIONS.VIEW_TASKS,
  ],
  super_admin: Object.values(PERMISSIONS),
};

export function hasPermission(userRole, permission) {
  if (!userRole || !permission) return false;
  const perms = ROLE_PERMISSIONS[userRole] || [];
  return perms.includes(permission);
}

export function hasAnyPermission(userRole, permissions) {
  return permissions.some((p) => hasPermission(userRole, p));
}

export function hasMinRole(userRole, minRole) {
  return (ROLE_RANK[userRole] || 0) >= (ROLE_RANK[minRole] || 0);
}

export function getPermissions(userRole) {
  return ROLE_PERMISSIONS[userRole] || [];
}

export function getCurrentUser() {
  try {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function getCurrentUserRole() {
  const user = getCurrentUser();
  return user?.role || null;
}

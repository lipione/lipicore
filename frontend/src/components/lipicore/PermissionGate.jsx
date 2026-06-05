import { hasPermission, hasAnyPermission, hasMinRole, getCurrentUserRole } from '../../config/rolePermissions';
import { useFeatureFlags } from '../../contexts/FeatureFlagContext';

export default function PermissionGate({ permission, anyOf, minRole, role, featureKey, fallback = null, children }) {
  const userRole = getCurrentUserRole();
  const { isFeatureEnabled } = useFeatureFlags();

  let allowed = true;

  if (permission) allowed = allowed && hasPermission(userRole, permission);
  if (anyOf) allowed = allowed && hasAnyPermission(userRole, anyOf);
  if (minRole) allowed = allowed && hasMinRole(userRole, minRole);
  if (role) allowed = allowed && userRole === role;
  if (featureKey) allowed = allowed && isFeatureEnabled(featureKey);

  return allowed ? children : fallback;
}

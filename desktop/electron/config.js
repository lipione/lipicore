const DEFAULT_APP_URL = "https://ai.silverlining.com.np";
const APPROVED_ORIGINS = [
  "https://ai.silverlining.com.np",
  "https://staging.ai.silverlining.com.np"
];
const approvedOriginSet = new Set(APPROVED_ORIGINS);

function parseOrigins(rawValue) {
  if (!rawValue) {
    return [];
  }

  return rawValue
    .split(",")
    .map((origin) => origin.trim())
    .filter(Boolean);
}

function parseUrl(value, envName) {
  try {
    return new URL(value);
  } catch (_error) {
    throw new Error(`${envName} must be a valid URL`);
  }
}

function assertHttps(url, envName) {
  if (url.protocol !== "https:") {
    throw new Error(`${envName} must use https`);
  }
}

function assertApprovedOrigin(url, envName, message) {
  if (!approvedOriginSet.has(url.origin)) {
    throw new Error(`${envName} ${message}`);
  }
}

function resolveAppUrl(rawValue) {
  if (!rawValue) {
    return DEFAULT_APP_URL;
  }

  const url = parseUrl(rawValue, "LIPICORE_DESKTOP_URL");

  assertHttps(url, "LIPICORE_DESKTOP_URL");
  assertApprovedOrigin(url, "LIPICORE_DESKTOP_URL", "must use an approved origin");

  return url.href;
}

function resolveAllowedOrigins(rawValue) {
  return parseOrigins(rawValue).map((origin) => {
    const url = parseUrl(origin, "LIPICORE_DESKTOP_ALLOWED_ORIGINS");

    assertHttps(url, "LIPICORE_DESKTOP_ALLOWED_ORIGINS");
    assertApprovedOrigin(url, "LIPICORE_DESKTOP_ALLOWED_ORIGINS", "must use approved origins");

    return url.origin;
  });
}

const appUrl = resolveAppUrl(process.env.LIPICORE_DESKTOP_URL);
const configuredOrigins = resolveAllowedOrigins(process.env.LIPICORE_DESKTOP_ALLOWED_ORIGINS);

module.exports = {
  APP_URL: appUrl,
  ALLOWED_ORIGINS: Array.from(new Set([...APPROVED_ORIGINS, ...configuredOrigins])),
  APP_NAME: "LipiCore Desktop",
  IDLE_LOCK_MS: 15 * 60 * 1000
};

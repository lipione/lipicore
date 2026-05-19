const DEFAULT_APP_URL = "https://ai.silverlining.com.np";

function parseOrigins(rawValue) {
  if (!rawValue) {
    return [];
  }

  return rawValue
    .split(",")
    .map((origin) => origin.trim())
    .filter(Boolean);
}

const appUrl = process.env.LIPICORE_DESKTOP_URL || DEFAULT_APP_URL;
const configuredOrigins = parseOrigins(process.env.LIPICORE_DESKTOP_ALLOWED_ORIGINS);
const defaultOrigins = [
  "https://ai.silverlining.com.np",
  "https://staging.ai.silverlining.com.np"
];

module.exports = {
  APP_URL: appUrl,
  ALLOWED_ORIGINS: Array.from(new Set([...defaultOrigins, ...configuredOrigins, new URL(appUrl).origin])),
  APP_NAME: "LipiCore Desktop",
  IDLE_LOCK_MS: 15 * 60 * 1000
};

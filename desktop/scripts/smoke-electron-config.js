const fs = require("node:fs");
const path = require("node:path");
const { APP_URL, ALLOWED_ORIGINS } = require("../electron/config");
const { isAllowedUrl, shouldOpenExternally } = require("../electron/allowed-origins");

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const root = path.resolve(__dirname, "..");
const requiredFiles = [
  "electron/config.js",
  "electron/allowed-origins.js",
  "electron/preload.js",
  "package.json"
];

for (const filePath of requiredFiles) {
  assert(fs.existsSync(path.join(root, filePath)), `Missing ${filePath}`);
}

assert(APP_URL === "https://ai.silverlining.com.np", "Default app URL must be production");
assert(ALLOWED_ORIGINS.includes("https://ai.silverlining.com.np"), "Production origin must be allowed");
assert(isAllowedUrl("https://ai.silverlining.com.np/login"), "Production URL must be allowed");
assert(!isAllowedUrl("http://ai.silverlining.com.np/login"), "HTTP production URL must be blocked");
assert(!isAllowedUrl("https://example.com"), "Unknown HTTPS URL must be blocked");
assert(shouldOpenExternally("https://example.com/help"), "Unknown HTTPS URL should open externally");
assert(shouldOpenExternally("mailto:support@silverlining.com.np"), "Mailto links should open externally");

console.log("Electron desktop config smoke checks passed");

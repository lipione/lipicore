const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

delete process.env.LIPICORE_DESKTOP_URL;
delete process.env.LIPICORE_DESKTOP_ALLOWED_ORIGINS;

const { APP_URL, ALLOWED_ORIGINS } = require("../electron/config");
const { isAllowedUrl, shouldOpenExternally } = require("../electron/allowed-origins");

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const root = path.resolve(__dirname, "..");
const configPath = path.join(root, "electron/config.js");
const requiredFiles = [
  "electron/config.js",
  "electron/allowed-origins.js",
  "electron/main.js",
  "electron/preload.js",
  "splash/splash.html",
  "splash/splash.css",
  "splash/splash.js",
  "assets/logo.svg",
  "package.json"
];

for (const filePath of requiredFiles) {
  assert(fs.existsSync(path.join(root, filePath)), `Missing ${filePath}`);
}

assert(APP_URL === "https://ai.silverlining.com.np", "Default app URL must be production");
assert(ALLOWED_ORIGINS.length === 2, "Only approved default origins should be allowed by default");
assert(ALLOWED_ORIGINS.includes("https://ai.silverlining.com.np"), "Production origin must be allowed");
assert(ALLOWED_ORIGINS.includes("https://staging.ai.silverlining.com.np"), "Staging origin must be allowed");
assert(isAllowedUrl("https://ai.silverlining.com.np/login"), "Production URL must be allowed");
assert(!isAllowedUrl("http://ai.silverlining.com.np/login"), "HTTP production URL must be blocked");
assert(!isAllowedUrl("https://example.com"), "Unknown HTTPS URL must be blocked");
assert(shouldOpenExternally("https://example.com/help"), "Unknown HTTPS URL should open externally");
assert(shouldOpenExternally("mailto:support@silverlining.com.np"), "Mailto links should open externally");

function assertConfigLoadFails(env, expectedMessage) {
  const child = spawnSync(process.execPath, ["-e", `require(${JSON.stringify(configPath)})`], {
    cwd: root,
    env: {
      ...process.env,
      LIPICORE_DESKTOP_URL: "",
      LIPICORE_DESKTOP_ALLOWED_ORIGINS: "",
      ...env
    },
    encoding: "utf8"
  });

  assert(child.status !== 0, `${Object.keys(env).join(", ")} should fail config load`);
  assert(
    child.stderr.includes(expectedMessage),
    `Expected config load error to include "${expectedMessage}", got: ${child.stderr}`
  );
}

function assertConfigLoadSucceeds(env, script) {
  const child = spawnSync(process.execPath, ["-e", script], {
    cwd: root,
    env: {
      ...process.env,
      LIPICORE_DESKTOP_URL: "",
      LIPICORE_DESKTOP_ALLOWED_ORIGINS: "",
      ...env
    },
    encoding: "utf8"
  });

  assert(child.status === 0, `Expected config load to succeed, got: ${child.stderr}`);
}

assertConfigLoadSucceeds(
  { LIPICORE_DESKTOP_URL: "https://staging.ai.silverlining.com.np/dashboard" },
  `
    const { APP_URL, ALLOWED_ORIGINS } = require(${JSON.stringify(configPath)});
    if (APP_URL !== "https://staging.ai.silverlining.com.np/dashboard") {
      throw new Error("Approved app URL with path was not preserved");
    }
    if (ALLOWED_ORIGINS.some((origin) => origin !== new URL(origin).origin)) {
      throw new Error("Allowed origins must be normalized origins");
    }
  `
);
assertConfigLoadFails(
  { LIPICORE_DESKTOP_URL: "http://ai.silverlining.com.np" },
  "LIPICORE_DESKTOP_URL must use https"
);
assertConfigLoadFails(
  { LIPICORE_DESKTOP_URL: "https://evil.test" },
  "LIPICORE_DESKTOP_URL must use an approved origin"
);
assertConfigLoadFails(
  { LIPICORE_DESKTOP_URL: "not-a-url" },
  "LIPICORE_DESKTOP_URL must be a valid URL"
);
assertConfigLoadFails(
  { LIPICORE_DESKTOP_ALLOWED_ORIGINS: "https://evil.test" },
  "LIPICORE_DESKTOP_ALLOWED_ORIGINS must use approved origins"
);
assertConfigLoadFails(
  { LIPICORE_DESKTOP_ALLOWED_ORIGINS: "http://ai.silverlining.com.np" },
  "LIPICORE_DESKTOP_ALLOWED_ORIGINS must use https"
);

console.log("Electron desktop config smoke checks passed");

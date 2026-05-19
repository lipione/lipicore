const { ALLOWED_ORIGINS } = require("./config");

const allowedOriginSet = new Set(ALLOWED_ORIGINS);

function toUrl(value) {
  try {
    return new URL(value);
  } catch (_error) {
    return null;
  }
}

function isAllowedUrl(value) {
  const url = toUrl(value);

  if (!url) {
    return false;
  }

  if (url.protocol !== "https:") {
    return false;
  }

  return allowedOriginSet.has(url.origin);
}

function shouldOpenExternally(value) {
  const url = toUrl(value);

  if (!url) {
    return false;
  }

  return ["http:", "https:", "mailto:", "tel:"].includes(url.protocol) && !isAllowedUrl(value);
}

module.exports = {
  isAllowedUrl,
  shouldOpenExternally
};

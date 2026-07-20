const CONFIG_KEYS = Object.freeze({
  spreadsheetId: "SPREADSHEET_ID",
  serviceAccountJson: "SERVICE_ACCOUNT_JSON",
  deviceTokenHashes: "DEVICE_TOKEN_HASHES_JSON",
  apiVersion: "API_VERSION",
  allowedOrigins: "ALLOWED_ORIGINS",
});

const DEFAULT_API_VERSION = "family-spike-v2";
const PROBE_SHEET_NAME = "Tekniskt test";
const MEMBERS = Object.freeze(["Nicklas", "Ida", "Thor", "Johanna"]);
const SHEETS_API_ROOT = "https://sheets.googleapis.com/v4/spreadsheets/";
const TOKEN_CACHE_KEY = "gumli-service-account-token-v1";

function doGet() {
  const template = HtmlService.createTemplateFromFile("Bridge");
  template.allowedOriginsJson = JSON.stringify(getAllowedOrigins_());
  return template
    .evaluate()
    .setTitle("Gumli Familj API")
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function doPost(event) {
  try {
    const body = JSON.parse(event?.postData?.contents || "{}");
    return jsonOutput_(handleRequest(body));
  } catch (error) {
    return jsonOutput_({ ok: false, error: "INVALID_REQUEST" });
  }
}

function handleRequest(request) {
  const member = authenticateDevice_(request?.deviceToken);
  if (!member) {
    return { ok: false, error: "UNAUTHORIZED" };
  }

  const apiVersion =
    PropertiesService.getScriptProperties().getProperty(CONFIG_KEYS.apiVersion) ||
    DEFAULT_API_VERSION;
  switch (request.action) {
    case "ping":
      return { ok: true, apiVersion: apiVersion, member: member };
    case "probeWrite":
      return probeWrite_(request, apiVersion, member);
    case "probeRead":
      return probeRead_(apiVersion);
    default:
      return { ok: false, error: "UNKNOWN_ACTION", apiVersion: apiVersion };
  }
}

function setupProbeSheet() {
  const metadata = sheetsRequest_("?fields=sheets.properties.title", { method: "get" });
  const exists = (metadata.sheets || []).some(function (sheet) {
    return sheet?.properties?.title === PROBE_SHEET_NAME;
  });
  if (!exists) {
    sheetsRequest_(":batchUpdate", {
      method: "post",
      payload: {
        requests: [{ addSheet: { properties: { title: PROBE_SHEET_NAME } } }],
      },
    });
  }

  sheetsRequest_(valuesPath_("'" + PROBE_SHEET_NAME + "'!A1:D1") + "?valueInputOption=RAW", {
    method: "put",
    payload: {
      range: "'" + PROBE_SHEET_NAME + "'!A1:D1",
      majorDimension: "ROWS",
      values: [["Tidpunkt", "Request-ID", "Enhet", "Resultat"]],
    },
  });
  return { ok: true, sheet: PROBE_SHEET_NAME };
}

function verifyConfiguration() {
  const properties = PropertiesService.getScriptProperties();
  const missing = [
    CONFIG_KEYS.spreadsheetId,
    CONFIG_KEYS.serviceAccountJson,
    CONFIG_KEYS.deviceTokenHashes,
  ].filter(function (key) {
    return !properties.getProperty(key);
  });
  if (missing.length > 0) {
    return { ok: false, missing: missing };
  }

  try {
    getServiceAccount_();
    getDeviceTokenHashes_();
    return { ok: true, missing: [] };
  } catch (error) {
    return { ok: false, missing: [], invalidConfiguration: true };
  }
}

function probeWrite_(request, apiVersion, member) {
  const requestId = String(request.requestId || "").trim();
  if (!requestId || requestId.length > 128) {
    return { ok: false, error: "INVALID_PROBE_DATA", apiVersion: apiVersion };
  }

  const lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) {
    return { ok: false, error: "BUSY", apiVersion: apiVersion };
  }
  try {
    const existingResponse = sheetsRequest_(valuesPath_("'" + PROBE_SHEET_NAME + "'!B2:B"), {
      method: "get",
    });
    const existing = (existingResponse.values || []).some(function (row) {
      return String(row[0] || "") === requestId;
    });
    if (!existing) {
      sheetsRequest_(
        valuesPath_("'" + PROBE_SHEET_NAME + "'!A:D") +
          ":append?valueInputOption=RAW&insertDataOption=INSERT_ROWS",
        {
          method: "post",
          payload: {
            majorDimension: "ROWS",
            values: [[new Date().toISOString(), requestId, member, "OK"]],
          },
        }
      );
    }
    return {
      ok: true,
      apiVersion: apiVersion,
      requestId: requestId,
      member: member,
      duplicate: existing,
    };
  } finally {
    lock.releaseLock();
  }
}

function probeRead_(apiVersion) {
  const response = sheetsRequest_(valuesPath_("'" + PROBE_SHEET_NAME + "'!A2:D"), {
    method: "get",
  });
  const rows = response.values || [];
  if (rows.length === 0) {
    return { ok: true, apiVersion: apiVersion, lastProbe: null };
  }
  const values = rows[rows.length - 1];
  return {
    ok: true,
    apiVersion: apiVersion,
    lastProbe: {
      timestamp: values[0] || "",
      requestId: values[1] || "",
      member: values[2] || "",
      result: values[3] || "",
    },
  };
}

function authenticateDevice_(deviceToken) {
  const token = String(deviceToken || "");
  if (token.length < 32 || token.length > 512) {
    return null;
  }
  const member = getDeviceTokenHashes_()[sha256Hex_(token)];
  return MEMBERS.includes(member) ? member : null;
}

function getDeviceTokenHashes_() {
  const raw = PropertiesService.getScriptProperties().getProperty(
    CONFIG_KEYS.deviceTokenHashes
  );
  const parsed = JSON.parse(raw || "{}");
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("Invalid device token configuration");
  }
  Object.keys(parsed).forEach(function (hash) {
    if (!/^[a-f0-9]{64}$/.test(hash) || !MEMBERS.includes(parsed[hash])) {
      throw new Error("Invalid device token configuration");
    }
  });
  if (Object.keys(parsed).length === 0) {
    throw new Error("Missing device token configuration");
  }
  return parsed;
}

function sha256Hex_(value) {
  return Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,
    value,
    Utilities.Charset.UTF_8
  )
    .map(function (byte) {
      return ((byte + 256) % 256).toString(16).padStart(2, "0");
    })
    .join("");
}

function sheetsRequest_(path, options) {
  const spreadsheetId = PropertiesService.getScriptProperties().getProperty(
    CONFIG_KEYS.spreadsheetId
  );
  if (!spreadsheetId) {
    throw new Error("Missing spreadsheet configuration");
  }

  const requestOptions = {
    method: options.method || "get",
    headers: { Authorization: "Bearer " + getServiceAccountAccessToken_() },
    muteHttpExceptions: true,
  };
  if (options.payload !== undefined) {
    requestOptions.contentType = "application/json";
    requestOptions.payload = JSON.stringify(options.payload);
  }

  const response = UrlFetchApp.fetch(
    SHEETS_API_ROOT + encodeURIComponent(spreadsheetId) + path,
    requestOptions
  );
  const status = response.getResponseCode();
  if (status < 200 || status >= 300) {
    throw new Error("Sheets API request failed (" + status + ")");
  }
  const content = response.getContentText();
  return content ? JSON.parse(content) : {};
}

function valuesPath_(range) {
  return "/values/" + encodeURIComponent(range);
}

function getServiceAccountAccessToken_() {
  const cache = CacheService.getScriptCache();
  const cached = cache.get(TOKEN_CACHE_KEY);
  if (cached) {
    return cached;
  }

  const serviceAccount = getServiceAccount_();
  const now = Math.floor(Date.now() / 1000);
  const header = base64WebSafeJson_({ alg: "RS256", typ: "JWT" });
  const claims = base64WebSafeJson_({
    iss: serviceAccount.client_email,
    scope: "https://www.googleapis.com/auth/spreadsheets",
    aud: serviceAccount.token_uri,
    iat: now,
    exp: now + 3600,
  });
  const unsignedJwt = header + "." + claims;
  const signature = Utilities.computeRsaSha256Signature(
    unsignedJwt,
    serviceAccount.private_key
  );
  const assertion =
    unsignedJwt + "." + Utilities.base64EncodeWebSafe(signature).replace(/=+$/, "");

  const response = UrlFetchApp.fetch(serviceAccount.token_uri, {
    method: "post",
    payload: {
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: assertion,
    },
    muteHttpExceptions: true,
  });
  if (response.getResponseCode() !== 200) {
    throw new Error("Service account authorization failed");
  }
  const tokenResponse = JSON.parse(response.getContentText());
  if (!tokenResponse.access_token) {
    throw new Error("Service account authorization failed");
  }
  cache.put(TOKEN_CACHE_KEY, tokenResponse.access_token, 3300);
  return tokenResponse.access_token;
}

function getServiceAccount_() {
  const raw = PropertiesService.getScriptProperties().getProperty(
    CONFIG_KEYS.serviceAccountJson
  );
  const parsed = JSON.parse(raw || "{}");
  if (
    parsed.type !== "service_account" ||
    !parsed.client_email ||
    !parsed.private_key
  ) {
    throw new Error("Invalid service account configuration");
  }
  return {
    client_email: String(parsed.client_email),
    private_key: String(parsed.private_key),
    token_uri: String(parsed.token_uri || "https://oauth2.googleapis.com/token"),
  };
}

function base64WebSafeJson_(value) {
  return Utilities.base64EncodeWebSafe(JSON.stringify(value)).replace(/=+$/, "");
}

function getAllowedOrigins_() {
  const configured = PropertiesService.getScriptProperties().getProperty(
    CONFIG_KEYS.allowedOrigins
  );
  if (!configured) {
    return ["https://nicklasc.github.io"];
  }
  try {
    const parsed = JSON.parse(configured);
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch (error) {
    return [];
  }
}

function jsonOutput_(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload)).setMimeType(
    ContentService.MimeType.JSON
  );
}

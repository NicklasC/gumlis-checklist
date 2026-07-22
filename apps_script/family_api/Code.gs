const CONFIG_KEYS = Object.freeze({
  spreadsheetId: "SPREADSHEET_ID",
  serviceAccountJson: "SERVICE_ACCOUNT_JSON",
  deviceTokenHashes: "DEVICE_TOKEN_HASHES_JSON",
  apiVersion: "API_VERSION",
  allowedOrigins: "ALLOWED_ORIGINS",
});

const DEFAULT_API_VERSION = "family-spike-v2";
const PROBE_SHEET_NAME = "Tekniskt test";
const TASKS_SHEET_NAME = "Uppgifter";
const MEMBERS_SHEET_NAME = "Medlemmar";
const FAVORITES_SHEET_NAME = "Favoriter";
const MEMBERS = Object.freeze(["Nicklas", "Ida", "Thor", "Johanna"]);
const ASSIGNEES = Object.freeze(["Alla"].concat(MEMBERS));
const ACTORS = Object.freeze(MEMBERS.concat(["Automatik", "Nicklas (Sheet)"]));
const TASK_STATUSES = Object.freeze(["Aktuell", "Senare", "Klar", "Raderad"]);
const STABLE_ERROR_CODES = Object.freeze([
  "UNAUTHORIZED", "INVALID_INPUT", "NOT_FOUND", "VERSION_CONFLICT", "TIMEOUT", "SERVER_ERROR",
]);
const TASK_HEADERS = Object.freeze([
  "Uppgift", "Status", "Ansvarig", "Tilldelad av", "Tilldelad", "Skapad av",
  "Skapad", "Deadline", "Senast ändrad av", "Uppdaterad", "Slutförd av",
  "Slutförd", "ID", "Version",
]);
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
    return jsonOutput_(failureResponse_("INVALID_INPUT", getApiVersion_()));
  }
}

function handleRequest(request) {
  const apiVersion = getApiVersion_();
  const member = authenticateDevice_(request?.deviceToken);
  if (!member) {
    return failureResponse_("UNAUTHORIZED", apiVersion);
  }

  try {
    switch (request.action) {
      case "ping":
        return successResponse_({ member: member }, apiVersion);
      case "bootstrap":
        return successResponse_(bootstrapData_(), apiVersion);
      case "listLater":
        return successResponse_(listLaterData_(), apiVersion);
      case "listHistory":
        return successResponse_(listHistoryData_(), apiVersion);
      case "createTask":
        return successResponse_(createTask_(request, member), apiVersion);
      case "updateTask":
        return successResponse_(updateTask_(request, member), apiVersion);
      case "probeWrite":
        return successResponse_(probeWrite_(request, member), apiVersion);
      case "probeRead":
        return successResponse_(probeRead_(), apiVersion);
      default:
        return failureResponse_("INVALID_INPUT", apiVersion);
    }
  } catch (error) {
    const errorCode = STABLE_ERROR_CODES.includes(error?.apiCode)
      ? error.apiCode
      : "SERVER_ERROR";
    return failureResponse_(errorCode, apiVersion, error?.apiData || null);
  }
}

function getApiVersion_() {
  return (
    PropertiesService.getScriptProperties().getProperty(CONFIG_KEYS.apiVersion) ||
    DEFAULT_API_VERSION
  );
}

function successResponse_(data, apiVersion) {
  return {
    ok: true,
    data: data,
    error: null,
    server_time: new Date().toISOString(),
    api_version: apiVersion,
  };
}

function failureResponse_(errorCode, apiVersion, data) {
  return {
    ok: false,
    data: data || null,
    error: errorCode,
    server_time: new Date().toISOString(),
    api_version: apiVersion,
  };
}

function apiError_(code, data) {
  const error = new Error(code);
  error.apiCode = code;
  error.apiData = data || null;
  return error;
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

function setupFamilySheets() {
  ensureSheetsExist_([TASKS_SHEET_NAME, MEMBERS_SHEET_NAME, FAVORITES_SHEET_NAME]);
  writeValues_("'" + TASKS_SHEET_NAME + "'!A1:N1", [TASK_HEADERS]);
  writeValues_("'" + MEMBERS_SHEET_NAME + "'!A1:C5", [
    ["Namn", "Aktiv", "Sortering"],
    ["Nicklas", true, 1],
    ["Ida", true, 2],
    ["Thor", true, 3],
    ["Johanna", true, 4],
  ]);
  writeValues_("'" + FAVORITES_SHEET_NAME + "'!A1:D1", [
    ["Uppgift", "Aktiv", "Sortering", "ID"],
  ]);
  return {
    ok: true,
    sheets: [TASKS_SHEET_NAME, MEMBERS_SHEET_NAME, FAVORITES_SHEET_NAME],
  };
}

function ensureSheetsExist_(sheetNames) {
  const metadata = sheetsRequest_("?fields=sheets.properties.title", { method: "get" });
  const existing = new Set(
    (metadata.sheets || []).map(function (sheet) {
      return sheet?.properties?.title;
    })
  );
  const requests = sheetNames
    .filter(function (name) {
      return !existing.has(name);
    })
    .map(function (name) {
      return { addSheet: { properties: { title: name } } };
    });
  if (requests.length > 0) {
    sheetsRequest_(":batchUpdate", { method: "post", payload: { requests: requests } });
  }
}

function writeValues_(range, values) {
  sheetsRequest_(valuesPath_(range) + "?valueInputOption=RAW", {
    method: "put",
    payload: { range: range, majorDimension: "ROWS", values: values },
  });
}

function bootstrapData_() {
  const rows = readFamilyRanges_();
  const parsed = parseFamilyRows_(rows);
  return {
    tasks: parsed.tasks.filter(function (task) {
      return task.status === "Aktuell";
    }),
    members: parsed.members.filter(function (member) {
      return member.active;
    }),
    favorites: parsed.favorites.filter(function (favorite) {
      return favorite.active;
    }),
    invalidRows: parsed.invalidRows,
  };
}

function listLaterData_() {
  const rows = readFamilyRanges_();
  const parsed = parseFamilyRows_(rows);
  return {
    tasks: parsed.tasks.filter(function (task) {
      return task.status === "Senare";
    }),
    invalidRows: parsed.invalidRows.filter(function (issue) {
      return issue.sheet === TASKS_SHEET_NAME;
    }),
  };
}

function listHistoryData_() {
  const rows = readFamilyRanges_();
  const parsed = parseFamilyRows_(rows);
  const cutoff = Date.now() - 14 * 24 * 60 * 60 * 1000;
  return {
    tasks: parsed.tasks.filter(function (task) {
      return task.status === "Klar" && task.completed_at && Date.parse(task.completed_at) >= cutoff;
    }),
    invalidRows: parsed.invalidRows.filter(function (issue) {
      return issue.sheet === TASKS_SHEET_NAME;
    }),
  };
}

function createTask_(request, member) {
  const input = taskMutationInput_(request?.task, false);
  return withTaskLock_(function () {
    const rows = readTaskRows_();
    const existing = findTaskById_(rows, input.id);
    if (existing) {
      return { task: existing.task, duplicate: true };
    }

    const now = new Date().toISOString();
    const task = {
      title: input.title,
      status: "Aktuell",
      assignee: input.assignee,
      assigned_by: member,
      assigned_at: now,
      created_by: member,
      created_at: now,
      deadline: input.deadline,
      updated_by: member,
      updated_at: now,
      completed_by: null,
      completed_at: null,
      id: input.id,
      version: 1,
    };
    sheetsRequest_(
      valuesPath_("'" + TASKS_SHEET_NAME + "'!A:N") +
        ":append?valueInputOption=RAW&insertDataOption=INSERT_ROWS",
      {
        method: "post",
        payload: { majorDimension: "ROWS", values: [taskToRow_(task)] },
      }
    );
    return { task: task, duplicate: false };
  });
}

function updateTask_(request, member) {
  const input = taskMutationInput_(request?.task, true);
  return withTaskLock_(function () {
    const rows = readTaskRows_();
    const existing = findTaskById_(rows, input.id);
    if (!existing) {
      throw apiError_("NOT_FOUND");
    }
    if (existing.task.version !== input.version) {
      throw apiError_("VERSION_CONFLICT", { latestTask: existing.task });
    }
    if (!["Aktuell", "Senare"].includes(existing.task.status)) {
      throw apiError_("INVALID_INPUT");
    }

    const now = new Date().toISOString();
    const updated = Object.assign({}, existing.task, {
      title: input.title,
      assignee: input.assignee,
      deadline: input.deadline,
      updated_by: member,
      updated_at: now,
      version: existing.task.version + 1,
    });
    if (input.assignee !== existing.task.assignee) {
      updated.assigned_by = member;
      updated.assigned_at = now;
    }
    const range = "'" + TASKS_SHEET_NAME + "'!A" + existing.rowNumber + ":N" + existing.rowNumber;
    writeValues_(range, [taskToRow_(updated)]);
    return { task: updated };
  });
}

function taskMutationInput_(value, requireVersion) {
  try {
    if (!value || Array.isArray(value) || typeof value !== "object") {
      throw apiError_("INVALID_INPUT");
    }
    const input = {
      id: boundedText_(value.id, 128),
      title: boundedText_(value.title, 200),
      assignee: allowedValue_(value.assignee || "Alla", ASSIGNEES),
      deadline: optionalDate_(value.deadline),
    };
    if (requireVersion) {
      input.version = positiveInteger_(value.version);
    }
    return input;
  } catch (error) {
    if (error?.apiCode) {
      throw error;
    }
    throw apiError_("INVALID_INPUT");
  }
}

function boundedText_(value, maxLength) {
  const normalized = requiredText_(value);
  if (normalized.length > maxLength) {
    throw apiError_("INVALID_INPUT");
  }
  return normalized;
}

function withTaskLock_(callback) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) {
    throw apiError_("TIMEOUT");
  }
  try {
    return callback();
  } finally {
    lock.releaseLock();
  }
}

function readTaskRows_() {
  const response = sheetsRequest_(valuesPath_("'" + TASKS_SHEET_NAME + "'!A2:N"), {
    method: "get",
  });
  return response.values || [];
}

function findTaskById_(rows, taskId) {
  for (let index = 0; index < rows.length; index += 1) {
    const row = rows[index] || [];
    if (String(row[12] || "").trim() === taskId) {
      return { rowNumber: index + 2, task: parseTaskRow_(row) };
    }
  }
  return null;
}

function taskToRow_(task) {
  return [
    task.title,
    task.status,
    task.assignee,
    task.assigned_by,
    task.assigned_at,
    task.created_by,
    task.created_at,
    task.deadline || "",
    task.updated_by,
    task.updated_at,
    task.completed_by || "",
    task.completed_at || "",
    task.id,
    task.version,
  ];
}

function readFamilyRanges_() {
  const ranges = [
    "'" + TASKS_SHEET_NAME + "'!A2:N",
    "'" + MEMBERS_SHEET_NAME + "'!A2:C",
    "'" + FAVORITES_SHEET_NAME + "'!A2:D",
  ];
  const query = ranges
    .map(function (range) {
      return "ranges=" + encodeURIComponent(range);
    })
    .join("&");
  const response = sheetsRequest_("/values:batchGet?" + query, { method: "get" });
  const valueRanges = response.valueRanges || [];
  return {
    tasks: valueRanges[0]?.values || [],
    members: valueRanges[1]?.values || [],
    favorites: valueRanges[2]?.values || [],
  };
}

function parseFamilyRows_(rows) {
  const invalidRows = [];
  const tasks = parseRows_(rows.tasks, TASKS_SHEET_NAME, parseTaskRow_, invalidRows);
  const members = parseRows_(rows.members, MEMBERS_SHEET_NAME, parseMemberRow_, invalidRows)
    .sort(function (left, right) { return left.sort_order - right.sort_order; });
  const favorites = parseRows_(rows.favorites, FAVORITES_SHEET_NAME, parseFavoriteRow_, invalidRows)
    .sort(function (left, right) { return left.sort_order - right.sort_order; });
  return { tasks: tasks, members: members, favorites: favorites, invalidRows: invalidRows };
}

function parseRows_(rows, sheetName, parser, invalidRows) {
  const parsed = [];
  (rows || []).forEach(function (row, index) {
    if ((row || []).every(function (value) {
      const normalized = String(value || "").trim().toLowerCase();
      return normalized === "" || normalized === "false";
    })) {
      return;
    }
    try {
      parsed.push(parser(row || []));
    } catch (error) {
      invalidRows.push({ sheet: sheetName, row: index + 2, error: "INVALID_ROW" });
    }
  });
  return parsed;
}

function parseTaskRow_(row) {
  const task = {
    title: requiredText_(row[0]),
    status: allowedValue_(row[1], TASK_STATUSES),
    assignee: allowedValue_(row[2] || "Alla", ASSIGNEES),
    assigned_by: allowedValue_(row[3], MEMBERS),
    assigned_at: isoTimestamp_(row[4]),
    created_by: allowedValue_(row[5], MEMBERS),
    created_at: isoTimestamp_(row[6]),
    deadline: optionalDate_(row[7]),
    updated_by: allowedValue_(row[8], ACTORS),
    updated_at: isoTimestamp_(row[9]),
    completed_by: optionalAllowedValue_(row[10], MEMBERS),
    completed_at: optionalTimestamp_(row[11]),
    id: requiredText_(row[12]),
    version: positiveInteger_(row[13]),
  };
  const complete = task.status === "Klar";
  const hasCompletion = Boolean(task.completed_by && task.completed_at);
  if (complete !== hasCompletion) {
    throw new Error("Invalid completion fields");
  }
  return task;
}

function parseMemberRow_(row) {
  return {
    name: allowedValue_(row[0], MEMBERS),
    active: booleanValue_(row[1]),
    sort_order: nonNegativeInteger_(row[2]),
  };
}

function parseFavoriteRow_(row) {
  return {
    title: requiredText_(row[0]),
    active: booleanValue_(row[1]),
    sort_order: nonNegativeInteger_(row[2]),
    id: requiredText_(row[3]),
  };
}

function requiredText_(value) {
  const normalized = String(value || "").trim();
  if (!normalized) throw new Error("Missing value");
  return normalized;
}

function allowedValue_(value, allowed) {
  const normalized = requiredText_(value);
  if (!allowed.includes(normalized)) throw new Error("Invalid value");
  return normalized;
}

function optionalAllowedValue_(value, allowed) {
  const normalized = String(value || "").trim();
  return normalized ? allowedValue_(normalized, allowed) : null;
}

function isoTimestamp_(value) {
  const normalized = requiredText_(value);
  if (isNaN(Date.parse(normalized))) throw new Error("Invalid timestamp");
  return new Date(normalized).toISOString();
}

function optionalTimestamp_(value) {
  return String(value || "").trim() ? isoTimestamp_(value) : null;
}

function optionalDate_(value) {
  const normalized = String(value || "").trim();
  if (!normalized) return null;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(normalized) || isNaN(Date.parse(normalized + "T00:00:00Z"))) {
    throw new Error("Invalid date");
  }
  return normalized;
}

function booleanValue_(value) {
  if (value === true || String(value).toLowerCase() === "true") return true;
  if (value === false || String(value).toLowerCase() === "false") return false;
  throw new Error("Invalid boolean");
}

function positiveInteger_(value) {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1) throw new Error("Invalid version");
  return parsed;
}

function nonNegativeInteger_(value) {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 0) throw new Error("Invalid sort order");
  return parsed;
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

function probeWrite_(request, member) {
  const requestId = String(request.requestId || "").trim();
  if (!requestId || requestId.length > 128) {
    throw new Error("Invalid probe data");
  }

  const lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) {
    throw new Error("Probe lock unavailable");
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
      requestId: requestId,
      member: member,
      duplicate: existing,
    };
  } finally {
    lock.releaseLock();
  }
}

function probeRead_() {
  const response = sheetsRequest_(valuesPath_("'" + PROBE_SHEET_NAME + "'!A2:D"), {
    method: "get",
  });
  const rows = response.values || [];
  if (rows.length === 0) {
    return { lastProbe: null };
  }
  const values = rows[rows.length - 1];
  return {
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

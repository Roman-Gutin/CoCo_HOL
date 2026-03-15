/**
 * Snowflake SQL API client.
 *
 * Executes SQL statements via the Snowflake SQL REST API and returns results.
 * Auth is handled via a PAT (Programmatic Access Token) loaded from env vars.
 *
 * All requests go through the Vite dev-server proxy at /api/snowflake to
 * avoid CORS issues when calling Snowflake directly from the browser.
 *
 * Docs: https://docs.snowflake.com/en/developer-guide/sql-api/guide
 */

// ---------------------------------------------------------------------------
// Config — pulled from Vite env vars (prefixed VITE_)
// ---------------------------------------------------------------------------

interface SnowflakeConfig {
  account: string;
  user: string;
  token: string;
  database: string;
  schema: string;
  warehouse: string;
  role: string;
}

function getConfig(): SnowflakeConfig {
  return {
    account: import.meta.env.VITE_SNOWFLAKE_ACCOUNT ?? "",
    user: import.meta.env.VITE_SNOWFLAKE_USER ?? "",
    token: import.meta.env.VITE_SNOWFLAKE_TOKEN ?? "",
    database: import.meta.env.VITE_SNOWFLAKE_DATABASE ?? "DIGITALNATIVECO",
    schema: import.meta.env.VITE_SNOWFLAKE_SCHEMA ?? "MARTS",
    warehouse: import.meta.env.VITE_SNOWFLAKE_WAREHOUSE ?? "COMPUTE_WH",
    role: import.meta.env.VITE_SNOWFLAKE_ROLE ?? "WORKSHOP_ROLE",
  };
}

// ---------------------------------------------------------------------------
// Snowflake REST API response types
// ---------------------------------------------------------------------------

interface SnowflakeColumnType {
  name: string;
  type: string;
  nullable: boolean;
}

interface SnowflakeResultSetMetaData {
  rowType: SnowflakeColumnType[];
  numRows: number;
  format: string;
}

interface SnowflakeAPIResponse {
  resultSetMetaData: SnowflakeResultSetMetaData;
  data: string[][];
  code: string;
  statementHandle: string;
  message: string;
}

// ---------------------------------------------------------------------------
// SQL execution
// ---------------------------------------------------------------------------

export interface QueryResult {
  columns: string[];
  rows: Record<string, unknown>[];
}

/**
 * Execute a SQL statement via the Snowflake SQL API and return typed results.
 * Uses the Vite proxy to avoid CORS issues.
 */
export async function executeSQL(sql: string): Promise<QueryResult> {
  const cfg = getConfig();
  // Route through the Vite dev proxy to avoid CORS
  const url = "/api/snowflake/api/v2/statements";

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      Authorization: `Bearer ${cfg.token}`,
      "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
    },
    body: JSON.stringify({
      statement: sql,
      timeout: 60,
      database: cfg.database,
      schema: cfg.schema,
      warehouse: cfg.warehouse,
      role: cfg.role,
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Snowflake API error ${response.status}: ${body}`);
  }

  const json: SnowflakeAPIResponse = await response.json();

  // Map the Snowflake response format into a simpler { columns, rows } shape.
  // Snowflake returns all values as strings — attempt numeric coercion for
  // columns whose declared type looks numeric.
  const columns: string[] =
    json.resultSetMetaData?.rowType?.map((col) => col.name) ?? [];

  const numericTypes = new Set([
    "fixed",
    "real",
    "float",
    "number",
    "decimal",
    "numeric",
    "int",
    "integer",
    "bigint",
    "smallint",
    "tinyint",
    "byteint",
    "double",
  ]);
  const isNumeric: boolean[] =
    json.resultSetMetaData?.rowType?.map((col) =>
      numericTypes.has(col.type.toLowerCase())
    ) ?? [];

  const rows: Record<string, unknown>[] = (json.data ?? []).map(
    (row: string[]) => {
      const record: Record<string, unknown> = {};
      columns.forEach((col, i) => {
        const raw = row[i];
        if (raw === null || raw === undefined) {
          record[col] = null;
        } else if (isNumeric[i]) {
          record[col] = Number(raw);
        } else if (raw === "true" || raw === "false") {
          record[col] = raw === "true";
        } else {
          record[col] = raw;
        }
      });
      return record;
    }
  );

  return { columns, rows };
}

// ---------------------------------------------------------------------------
// Cortex Agent helper
// ---------------------------------------------------------------------------

/**
 * Send a user message to the Cortex Agent and return its text response.
 *
 * Uses the Cortex REST API endpoint (`/api/v2/cortex/agent:run`) via the
 * Vite proxy. The response is an SSE stream — we parse delta events and
 * collect all text parts into a single string, calling onChunk for streaming.
 */
export async function askCortexAgent(
  userMessage: string,
  onChunk?: (textSoFar: string) => void
): Promise<string> {
  const cfg = getConfig();
  // Route through the Vite dev proxy
  const url = "/api/snowflake/api/v2/cortex/agent:run";

  const augmentedMessage =
    userMessage +
    "\n\nAfter your analysis, suggest: (a) a dbt model or YAML change, (b) a report to build, (c) additional data sources that would help.";

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      Authorization: `Bearer ${cfg.token}`,
      "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
    },
    body: JSON.stringify({
      model: "claude-3-7-sonnet",
      tools: [
        {
          tool_spec: {
            type: "cortex_analyst_text_to_sql",
            name: "analyst",
          },
        },
        {
          tool_spec: {
            type: "cortex_search",
            name: "gong_search",
          },
        },
        {
          tool_spec: {
            type: "cortex_search",
            name: "ticket_search",
          },
        },
        {
          tool_spec: {
            type: "cortex_search",
            name: "csm_notes_search",
          },
        },
      ],
      tool_resources: {
        analyst: {
          semantic_model_file:
            "@DIGITALNATIVECO.MARTS.SEMANTIC_MODELS/account_health.yaml",
          execution_environment: {
            type: "warehouse",
            warehouse: cfg.warehouse,
          },
        },
        gong_search: {
          name: "DIGITALNATIVECO.MARTS.GONG_TRANSCRIPT_SEARCH",
          max_results: 5,
        },
        ticket_search: {
          name: "DIGITALNATIVECO.MARTS.SUPPORT_TICKET_SEARCH",
          max_results: 5,
        },
        csm_notes_search: {
          name: "DIGITALNATIVECO.MARTS.CSM_NOTES_SEARCH",
          max_results: 5,
        },
      },
      messages: [
        {
          role: "user",
          content: [{ type: "text", text: augmentedMessage }],
        },
      ],
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Cortex Agent API error ${response.status}: ${body}`);
  }

  // Parse SSE stream
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("No response body from Cortex Agent");
  }

  const decoder = new TextDecoder();
  let collected = "";
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete lines
    const lines = buffer.split("\n");
    // Keep the last (potentially incomplete) line in the buffer
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();

      // End of stream signals
      if (trimmed === "event: done" || trimmed === "data: [DONE]") {
        continue;
      }

      if (trimmed.startsWith("data: ")) {
        const jsonStr = trimmed.slice(6);
        if (jsonStr === "[DONE]") continue;

        try {
          const event = JSON.parse(jsonStr);
          // Extract text from delta.content array
          const contentParts = event?.delta?.content ?? [];
          for (const part of contentParts) {
            if (part.type === "text" && part.text) {
              collected += part.text;
              onChunk?.(collected);
            }
          }
        } catch {
          // Skip malformed JSON lines (e.g., keep-alive comments)
        }
      }
    }
  }

  return collected || "No response from Cortex Agent.";
}

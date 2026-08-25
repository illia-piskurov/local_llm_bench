import { readFile, writeFile } from "node:fs/promises";

export interface ProfileConfig {
  readonly baseUrl: string;
  /** Name of the environment variable that holds the API key. Optional. */
  readonly apiKeyEnv?: string;
}

export interface ProbeConfig {
  readonly profiles?: Readonly<Record<string, ProfileConfig>>;
  readonly hardware?: string;
  readonly savedHardware?: ReadonlyArray<string>;
  readonly defaults?: {
    readonly profile?: string;
    readonly hardware?: string;
    readonly temperature?: number;
    readonly maxTokens?: number;
    /** HTTP request timeout in milliseconds. Default: 120 000. */
    readonly timeoutMs?: number;
    readonly runsDir?: string;
  };
}

/**
 * Load probe.config.json from the current working directory.
 * Returns an empty object if the file does not exist or cannot be parsed.
 */
export async function loadConfig(): Promise<ProbeConfig> {
  try {
    const text = await readFile("probe.config.json", "utf8");
    return JSON.parse(text) as ProbeConfig;
  } catch {
    return {};
  }
}

/** Save updated config to probe.config.json */
export async function saveHardware(hardwareStr: string): Promise<void> {
  const current = await loadConfig();
  const existingList = current.savedHardware ?? (current.hardware ? [current.hardware] : []);
  const updatedList = Array.from(new Set([hardwareStr, ...existingList]));
  const updatedConfig: ProbeConfig = {
    ...current,
    hardware: hardwareStr,
    savedHardware: updatedList,
    defaults: {
      ...current.defaults,
      hardware: hardwareStr
    }
  };
  try {
    await writeFile("probe.config.json", JSON.stringify(updatedConfig, null, 2) + "\n", "utf8");
  } catch {
    // Non-critical if writing fails (e.g. read-only filesystem)
  }
}

/** Resolve a named profile from config, returning its baseUrl and optional API key. */
export function resolveProfile(
  config: ProbeConfig,
  profileName?: string
): { baseUrl: string; apiKey?: string } | undefined {
  const name = profileName ?? config.defaults?.profile;
  if (!name) return undefined;
  const profile = config.profiles?.[name];
  if (!profile) return undefined;
  const apiKey = profile.apiKeyEnv ? (process.env[profile.apiKeyEnv] ?? undefined) : undefined;
  return apiKey !== undefined ? { baseUrl: profile.baseUrl, apiKey } : { baseUrl: profile.baseUrl };
}

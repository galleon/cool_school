import { StartScreenPrompt } from "@openai/chatkit";

export const THEME_STORAGE_KEY = "schedule-assistant-theme";

const SCHEDULE_API_BASE =
    import.meta.env.VITE_SCHEDULE_API_BASE ?? "/schedule";

/**
 * ChatKit still expects a domain key at runtime. Use any placeholder locally,
 * but register your production domain at
 * https://platform.openai.com/settings/organization/security/domain-allowlist
 * and deploy the real key.
 */
export const SCHEDULE_CHATKIT_API_DOMAIN_KEY =
    import.meta.env.VITE_SCHEDULE_CHATKIT_API_DOMAIN_KEY ?? "domain_pk_localhost_dev";

export const SCHEDULE_CHATKIT_API_URL =
    import.meta.env.VITE_SCHEDULE_CHATKIT_API_URL ??
    `${SCHEDULE_API_BASE}/chatkit`;

export const SCHEDULE_STATE_URL =
    import.meta.env.VITE_SCHEDULE_STATE_URL ??
    `${SCHEDULE_API_BASE}/state`;

export const SCHEDULE_GREETING =
    import.meta.env.VITE_SCHEDULE_GREETING ??
    "Welcome to the Academic Scheduling Assistant. How can I help you with course scheduling and teacher assignments today?";

export const SCHEDULE_STARTER_PROMPTS: StartScreenPrompt[] = [
    {
        label: "Show schedule overview",
        prompt: "Can you show me the current schedule overview with teacher workloads?",
        icon: "lightbulb",
    },
    {
        label: "Swap assignment",
        prompt: "Swap CS101-A from Alice to Bob",
        icon: "sparkle",
    },
    {
        label: "Rebalance workload",
        prompt: "Help me rebalance the teaching workload across all teachers.",
        icon: "compass",
    },
];

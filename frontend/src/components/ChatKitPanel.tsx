import { ChatKit, useChatKit } from "@openai/chatkit-react";
import type { ColorScheme } from "../hooks/useColorScheme";
import {
    SCHEDULE_CHATKIT_API_DOMAIN_KEY,
    SCHEDULE_CHATKIT_API_URL,
    SCHEDULE_GREETING,
    SCHEDULE_STARTER_PROMPTS,
} from "../lib/config";

type ChatKitPanelProps = {
    theme: ColorScheme;
    onThreadChange: (threadId: string | null) => void;
    onResponseCompleted: () => void;
};

export function ChatKitPanel({
    theme,
    onThreadChange,
    onResponseCompleted,
}: ChatKitPanelProps) {

    const chatkit = useChatKit({
        api: {
            url: SCHEDULE_CHATKIT_API_URL,
            domainKey: SCHEDULE_CHATKIT_API_DOMAIN_KEY,
        },
        theme: {
            colorScheme: theme,
            color: {
                grayscale: {
                    hue: 220,
                    tint: 6,
                    shade: theme === "dark" ? -1 : -4,
                },
                accent: {
                    primary: theme === "dark" ? "#f8fafc" : "#0f172a",
                    level: 1,
                },
            },
            radius: "round",
        },
        startScreen: {
            greeting: SCHEDULE_GREETING,
            prompts: SCHEDULE_STARTER_PROMPTS,
        },
        composer: {
            placeholder: "Ask about course scheduling and assignments",
        },
        threadItemActions: {
            feedback: false,
        },
        onResponseEnd: () => {
            onResponseCompleted();
        },
        onThreadChange: ({ threadId }) => {
            onThreadChange(threadId ?? null);
        },
        onError: ({ error }) => {
            // ChatKit displays surfaced errors; we keep logging for debugging.
            console.error("ChatKit error", error);
        },
    });

    return (
        <div className="relative h-full w-full overflow-hidden border border-slate-200/60 bg-white shadow-card dark:border-slate-800/70 dark:bg-slate-900">
            <ChatKit control={chatkit.control} className="block h-full w-full" />
        </div>
    );
}

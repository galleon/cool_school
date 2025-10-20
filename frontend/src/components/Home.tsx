import { useCallback, useState } from "react";
import clsx from "clsx";

import { ChatKitPanel } from "./ChatKitPanel";
import { ScheduleContextPanel } from "./ScheduleContextPanel";
import { ThemeToggle } from "./ThemeToggle";
import { useScheduleContext } from "../hooks/useScheduleContext";
import type { ColorScheme } from "../hooks/useColorScheme";

type HomeProps = {
    scheme: ColorScheme;
    onThemeChange: (scheme: ColorScheme) => void;
};

export default function Home({ scheme, onThemeChange }: HomeProps) {
    const [threadId, setThreadId] = useState<string | null>(null);
    const { schedule, loading, error, refresh } = useScheduleContext(threadId);

    const containerClass = clsx(
        "min-h-screen bg-gradient-to-br transition-colors duration-300",
        scheme === "dark"
            ? "from-slate-950 via-slate-950 to-slate-900 text-slate-100"
            : "from-slate-100 via-white to-slate-200 text-slate-900",
    );

    const handleThreadChange = useCallback((nextThreadId: string | null) => {
        setThreadId(nextThreadId);
    }, []);

    const handleResponseCompleted = useCallback(() => {
        void refresh();
    }, [refresh]);

    return (
        <div className={containerClass}>
            <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-8 px-6 py-8 lg:h-screen lg:max-h-screen lg:py-10">
                <header className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
                    <div className="space-y-3">
                        <p className="text-sm uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
                            Academic scheduling assistant
                        </p>
                        <h1 className="text-3xl font-semibold sm:text-4xl">
                            Teacher-Course Assignment & Timetabling
                        </h1>
                        <p className="max-w-3xl text-sm text-slate-600 dark:text-slate-300">
                            Chat with the scheduling assistant on the left. The right panel shows the current
                            schedule state, teacher workloads, course assignments, and recent scheduling
                            changes.
                        </p>
                    </div>
                    <ThemeToggle value={scheme} onChange={onThemeChange} />
                </header>

                <div className="grid flex-1 grid-cols-1 gap-8 lg:h-[calc(100vh-260px)] lg:grid-cols-[minmax(320px,380px)_1fr] lg:items-stretch xl:grid-cols-[minmax(360px,420px)_1fr]">
                    <section className="flex flex-1 flex-col overflow-hidden rounded-3xl bg-white/80 shadow-[0_45px_90px_-45px_rgba(15,23,42,0.6)] ring-1 ring-slate-200/60 backdrop-blur dark:bg-slate-900/70 dark:shadow-[0_45px_90px_-45px_rgba(15,23,42,0.85)] dark:ring-slate-800/60">
                        <div className="flex flex-1">
                            <ChatKitPanel
                                theme={scheme}
                                onThreadChange={handleThreadChange}
                                onResponseCompleted={handleResponseCompleted}
                            />
                        </div>
                    </section>

                    <ScheduleContextPanel schedule={schedule} loading={loading} error={error} />
                </div>
            </div>
        </div>
    );
}

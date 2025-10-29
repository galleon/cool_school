import { useState } from "react";
import clsx from "clsx";
import { ChatKit, useChatKit } from "@openai/chatkit-react";
import type { ColorScheme } from "../hooks/useColorScheme";
import {
    SCHEDULE_CHATKIT_API_DOMAIN_KEY,
    SCHEDULE_CHATKIT_API_URL,
    SCHEDULE_GREETING,
    SCHEDULE_STARTER_PROMPTS,
} from "../lib/config";
import { ThemeToggle } from "./ThemeToggle";

type LandingPageProps = {
    scheme: ColorScheme;
    onThemeChange: (scheme: ColorScheme) => void;
};

export function LandingPage({ scheme, onThemeChange }: LandingPageProps) {
    const [isChatOpen, setIsChatOpen] = useState(false);

    const chatkit = useChatKit({
        api: {
            url: SCHEDULE_CHATKIT_API_URL,
            domainKey: SCHEDULE_CHATKIT_API_DOMAIN_KEY,
        },
        theme: {
            colorScheme: scheme,
            color: {
                grayscale: {
                    hue: 220,
                    tint: 6,
                    shade: scheme === "dark" ? -1 : -4,
                },
                accent: {
                    primary: scheme === "dark" ? "#f8fafc" : "#0f172a",
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
        onError: ({ error }) => {
            console.error("ChatKit error", error);
        },
    });

    const containerClass = clsx(
        "min-h-screen bg-gradient-to-br transition-colors duration-300",
        scheme === "dark"
            ? "from-slate-950 via-slate-900 to-slate-900 text-slate-100"
            : "from-blue-50 via-white to-indigo-50 text-slate-900",
    );

    return (
        <div className={containerClass}>
            {/* Navigation */}
            <nav
                className={clsx(
                    "sticky top-0 z-40 border-b backdrop-blur-md",
                    scheme === "dark"
                        ? "border-slate-800 bg-slate-950/80"
                        : "border-blue-100 bg-white/80",
                )}
            >
                <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
                    <div className="flex items-center gap-2">
                        <div
                            className={clsx(
                                "flex h-10 w-10 items-center justify-center rounded-lg font-bold",
                                scheme === "dark"
                                    ? "bg-blue-500/20 text-blue-400"
                                    : "bg-blue-100 text-blue-600",
                            )}
                        >
                            📚
                        </div>
                        <span className="text-xl font-bold">Cool School</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setIsChatOpen(true)}
                            className={clsx(
                                "px-4 py-2 rounded-lg font-medium transition-colors",
                                scheme === "dark"
                                    ? "bg-blue-600 hover:bg-blue-700 text-white"
                                    : "bg-blue-600 hover:bg-blue-700 text-white",
                            )}
                        >
                            Chat with Assistant
                        </button>
                        <ThemeToggle value={scheme} onChange={onThemeChange} />
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="mx-auto max-w-6xl px-6 py-16 sm:py-24">
                {/* Hero Section */}
                <section className="mb-20 text-center">
                    <h1 className="mb-6 text-5xl font-bold sm:text-6xl">
                        Welcome to <span className="text-blue-600">Cool School</span>
                    </h1>
                    <p className="mb-8 text-xl text-slate-600 dark:text-slate-300">
                        Empowering education through intelligent academic scheduling and course management.
                    </p>
                    <button
                        onClick={() => setIsChatOpen(true)}
                        className="inline-block rounded-lg bg-blue-600 px-8 py-3 font-semibold text-white hover:bg-blue-700 transition-colors"
                    >
                        Get Started with AI Assistant
                    </button>
                </section>

                {/* Features Section */}
                <section className="mb-20">
                    <h2 className="mb-12 text-center text-4xl font-bold">Our Features</h2>
                    <div className="grid gap-8 md:grid-cols-3">
                        {[
                            {
                                icon: "⚡",
                                title: "Smart Scheduling",
                                description:
                                    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Our AI automatically optimizes course schedules to minimize conflicts.",
                            },
                            {
                                icon: "👥",
                                title: "Teacher Load Balance",
                                description:
                                    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ensure fair distribution of teaching workloads across faculty.",
                            },
                            {
                                icon: "📊",
                                title: "Real-time Analytics",
                                description:
                                    "Ut enim ad minim veniam, quis nostrud exercitation ullamco. Track scheduling metrics and course assignments in real-time.",
                            },
                        ].map((feature, index) => (
                            <div
                                key={index}
                                className={clsx(
                                    "rounded-xl border p-8 transition-all hover:shadow-lg",
                                    scheme === "dark"
                                        ? "border-slate-800 bg-slate-900/50 hover:bg-slate-800/50"
                                        : "border-blue-100 bg-white hover:bg-blue-50",
                                )}
                            >
                                <div className="mb-4 text-4xl">{feature.icon}</div>
                                <h3 className="mb-3 text-xl font-semibold">{feature.title}</h3>
                                <p className="text-slate-600 dark:text-slate-300">
                                    {feature.description}
                                </p>
                            </div>
                        ))}
                    </div>
                </section>

                {/* About Section */}
                <section className="mb-20">
                    <h2 className="mb-8 text-4xl font-bold">About Cool School</h2>
                    <div
                        className={clsx(
                            "rounded-xl border p-12",
                            scheme === "dark"
                                ? "border-slate-800 bg-slate-900/30"
                                : "border-blue-100 bg-white",
                        )}
                    >
                        <p className="mb-4 text-lg text-slate-600 dark:text-slate-300">
                            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
                            incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
                            nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                        </p>
                        <p className="mb-4 text-lg text-slate-600 dark:text-slate-300">
                            Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
                            fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
                            culpa qui officia deserunt mollit anim id est laborum.
                        </p>
                        <p className="text-lg text-slate-600 dark:text-slate-300">
                            Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium
                            doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore
                            veritatis et quasi architecto beatae vitae dicta sunt explicabo.
                        </p>
                    </div>
                </section>

                {/* CTA Section */}
                <section className="text-center">
                    <h2 className="mb-6 text-3xl font-bold">Ready to optimize your schedule?</h2>
                    <p className="mb-8 text-lg text-slate-600 dark:text-slate-300">
                        Chat with our AI assistant to get started with intelligent course scheduling.
                    </p>
                    <button
                        onClick={() => setIsChatOpen(true)}
                        className="inline-block rounded-lg bg-blue-600 px-8 py-3 font-semibold text-white hover:bg-blue-700 transition-colors"
                    >
                        Chat Now
                    </button>
                </section>
            </main>

            {/* Floating Chat Widget */}
            {isChatOpen && (
                <div
                    className={clsx(
                        "fixed bottom-4 right-4 z-50 flex flex-col rounded-2xl shadow-2xl border overflow-hidden",
                        "w-full max-w-sm h-[600px]",
                        scheme === "dark"
                            ? "bg-slate-900 border-slate-800"
                            : "bg-white border-slate-200",
                    )}
                >
                    {/* Chat Header */}
                    <div
                        className={clsx(
                            "flex items-center justify-between border-b px-4 py-3",
                            scheme === "dark" ? "border-slate-800 bg-slate-950" : "border-slate-200 bg-slate-50",
                        )}
                    >
                        <h3 className="font-semibold">Scheduling Assistant</h3>
                        <button
                            onClick={() => setIsChatOpen(false)}
                            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                            aria-label="Close chat"
                        >
                            ✕
                        </button>
                    </div>

                    {/* Chat Content */}
                    <div className="flex-1 overflow-hidden">
                        <ChatKit control={chatkit.control} className="block h-full w-full" />
                    </div>
                </div>
            )}

            {/* Chat Toggle Button (when closed) */}
            {!isChatOpen && (
                <button
                    onClick={() => setIsChatOpen(true)}
                    className={clsx(
                        "fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full shadow-lg transition-all hover:scale-110",
                        scheme === "dark"
                            ? "bg-blue-600 hover:bg-blue-700 text-white"
                            : "bg-blue-600 hover:bg-blue-700 text-white",
                    )}
                    aria-label="Open chat"
                    title="Chat with our AI assistant"
                >
                    💬
                </button>
            )}

            {/* Footer */}
            <footer
                className={clsx(
                    "border-t py-8 text-center text-slate-600 dark:text-slate-400",
                    scheme === "dark" ? "border-slate-800" : "border-slate-200",
                )}
            >
                <p>&copy; 2025 Cool School. All rights reserved.</p>
            </footer>
        </div>
    );
}

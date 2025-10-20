import { BookOpen, Clock, Users, GraduationCap, Calendar } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import clsx from "clsx";

import type { ScheduleState, TimelineEntry, Teacher, Section, Assignment } from "../hooks/useScheduleContext";

type ScheduleContextPanelProps = {
    schedule: ScheduleState | null;
    loading: boolean;
    error: string | null;
};

export function ScheduleContextPanel({ schedule, loading, error }: ScheduleContextPanelProps) {
    if (loading) {
        return (
            <section className="flex h-full flex-col gap-4 rounded-3xl border border-slate-200/60 bg-white/80 p-6 shadow-[0_45px_90px_-45px_rgba(15,23,42,0.5)] ring-1 ring-slate-200/60 backdrop-blur dark:border-slate-800/70 dark:bg-slate-900/70 dark:shadow-[0_45px_95px_-55px_rgba(15,23,42,0.85)] dark:ring-slate-800/60">
                <header>
                    <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100">
                        Schedule overview
                    </h2>
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-300">
                        Loading schedule data…
                    </p>
                </header>
                <div className="flex flex-1 items-center justify-center">
                    <span className="text-sm text-slate-500 dark:text-slate-400">
                        Fetching the latest assignments and timetable…
                    </span>
                </div>
            </section>
        );
    }

    if (error) {
        return (
            <section className="flex h-full flex-col gap-4 rounded-3xl border border-rose-200 bg-rose-50/60 p-6 text-rose-700 shadow-sm dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-200">
                <header>
                    <h2 className="text-xl font-semibold">Schedule overview</h2>
                </header>
                <p className="text-sm">{error}</p>
            </section>
        );
    }

    if (!schedule) {
        return null;
    }

    // Calculate statistics
    const teacherLoads = Object.values(schedule.teachers).map(teacher => {
        const load = calculateTeacherLoad(teacher, schedule.assignments, schedule.sections);
        return {
            teacher,
            load,
            utilization: teacher.max_load_hours > 0 ? (load / teacher.max_load_hours) * 100 : 0
        };
    });

    const totalSections = Object.keys(schedule.sections).length;
    const assignedSections = Object.values(schedule.assignments).filter(a => a.teacher_id).length;
    const overloadedTeachers = teacherLoads.filter(tl => tl.load > tl.teacher.max_load_hours);

    return (
        <section className="flex h-full flex-col gap-6 overflow-hidden rounded-3xl border border-slate-200/60 bg-white/80 p-6 shadow-[0_45px_90px_-45px_rgba(15,23,42,0.5)] ring-1 ring-slate-200/60 backdrop-blur dark:border-slate-800/70 dark:bg-slate-900/70 dark:shadow-[0_45px_95px_-55px_rgba(15,23,42,0.85)] dark:ring-slate-800/60">
            <header className="space-y-3">
                <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                        <p className="text-xs uppercase tracking-[0.25em] text-blue-500 dark:text-blue-300">
                            Academic schedule
                        </p>
                        <h2 className="text-2xl font-semibold text-slate-800 dark:text-slate-100">
                            Current Timetable
                        </h2>
                        <p className="text-sm text-blue-600 dark:text-blue-200">
                            {assignedSections}/{totalSections} sections assigned
                        </p>
                    </div>
                    {overloadedTeachers.length > 0 && (
                        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-medium text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/30 dark:text-rose-200">
                            {overloadedTeachers.length} overloaded teacher{overloadedTeachers.length !== 1 ? 's' : ''}
                        </div>
                    )}
                </div>
            </header>

            <section className="grid gap-3 sm:grid-cols-4">
                <InfoPill icon={Users} label="Teachers">
                    {Object.keys(schedule.teachers).length}
                </InfoPill>
                <InfoPill icon={BookOpen} label="Sections">
                    {totalSections}
                </InfoPill>
                <InfoPill icon={GraduationCap} label="Assigned">
                    {assignedSections}
                </InfoPill>
                <InfoPill icon={Calendar} label="Rooms">
                    {Object.keys(schedule.rooms).length}
                </InfoPill>
            </section>

            <section className="rounded-2xl bg-slate-50/80 p-4 dark:bg-slate-900/60">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                    Teacher workloads
                </h3>
                <div className="mt-4 space-y-3 max-h-48 overflow-y-auto">
                    {teacherLoads.map(({ teacher, load, utilization }) => (
                        <article
                            key={teacher.id}
                            className={clsx(
                                "rounded-xl border p-4 shadow-sm transition",
                                load > teacher.max_load_hours
                                    ? "border-rose-200 bg-rose-50/90 hover:border-rose-300 dark:border-rose-900/40 dark:bg-rose-900/30"
                                    : "border-slate-200 bg-white/90 hover:border-blue-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/70"
                            )}
                        >
                            <div className="flex items-center justify-between gap-3">
                                <div>
                                    <h4 className="text-base font-semibold text-slate-800 dark:text-slate-100">
                                        {teacher.name}
                                    </h4>
                                    <p className="text-sm text-slate-500 dark:text-slate-400">
                                        {teacher.qualified_courses.join(", ")}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className={clsx(
                                        "text-sm font-medium",
                                        load > teacher.max_load_hours
                                            ? "text-rose-600 dark:text-rose-300"
                                            : "text-blue-600 dark:text-blue-300"
                                    )}>
                                        {load.toFixed(1)}/{teacher.max_load_hours} hrs
                                    </p>
                                    <p className="text-xs text-slate-500 dark:text-slate-400">
                                        {utilization.toFixed(0)}% utilization
                                    </p>
                                </div>
                            </div>
                        </article>
                    ))}
                </div>
            </section>

            <section className="flex flex-1 flex-col overflow-hidden rounded-2xl border border-slate-200/70 bg-white/90 dark:border-slate-800/70 dark:bg-slate-900/70">
                <header className="border-b border-slate-200/70 px-4 py-3 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:border-slate-800/70 dark:text-slate-300">
                    Recent scheduling changes
                </header>
                <Timeline entries={schedule.timeline} />
            </section>
        </section>
    );
}

function InfoPill({
    icon: Icon,
    label,
    children,
}: {
    icon: LucideIcon;
    label: string;
    children: React.ReactNode;
}) {
    return (
        <div className="flex items-center gap-3 rounded-2xl border border-slate-200/60 bg-white/90 px-4 py-3 shadow-sm dark:border-slate-800/70 dark:bg-slate-900/70">
            <Icon className="h-5 w-5 text-blue-500 dark:text-blue-300" aria-hidden />
            <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 dark:text-slate-500">
                    {label}
                </p>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                    {children}
                </p>
            </div>
        </div>
    );
}

function Timeline({ entries }: { entries: TimelineEntry[] }) {
    if (!entries.length) {
        return (
            <div className="flex flex-1 items-center justify-center px-6 text-sm text-slate-500 dark:text-slate-400">
                No scheduling changes recorded yet.
            </div>
        );
    }

    return (
        <ul className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
            {entries.map((entry, index) => (
                <li
                    key={`${entry.timestamp}-${index}`}
                    className={clsx(
                        "rounded-xl border px-4 py-3 text-sm leading-relaxed",
                        timelineTone(entry.kind),
                    )}
                >
                    <p className="font-medium text-slate-700 dark:text-slate-100">{entry.entry}</p>
                    <p className="text-xs uppercase tracking-wide text-slate-400 dark:text-slate-500">
                        {formatTimestamp(entry.timestamp)}
                    </p>
                </li>
            ))}
        </ul>
    );
}

function timelineTone(kind: string | undefined) {
    switch (kind) {
        case "success":
        case "assignment":
            return "border-emerald-200/70 bg-emerald-50/80 text-emerald-700 dark:border-emerald-900/40 dark:bg-emerald-900/30 dark:text-emerald-200";
        case "warning":
            return "border-amber-200/70 bg-amber-50/80 text-amber-700 dark:border-amber-900/40 dark:bg-amber-900/30 dark:text-amber-200";
        case "error":
            return "border-rose-200/70 bg-rose-50/80 text-rose-700 dark:border-rose-900/40 dark:bg-rose-900/30 dark:text-rose-200";
        case "system":
            return "border-blue-200/70 bg-blue-50/80 text-blue-700 dark:border-blue-900/40 dark:bg-blue-900/30 dark:text-blue-200";
        default:
            return "border-slate-200/70 bg-slate-50/90 text-slate-600 dark:border-slate-800/70 dark:bg-slate-900/60 dark:text-slate-200";
    }
}

function formatTimestamp(value: string): string {
    try {
        const date = new Date(value);
        return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
    } catch (err) {
        return value;
    }
}

function calculateTeacherLoad(
    teacher: Teacher,
    assignments: Record<string, Assignment>,
    sections: Record<string, Section>
): number {
    let totalHours = 0;
    for (const assignment of Object.values(assignments)) {
        if (assignment.teacher_id === teacher.id) {
            const section = sections[assignment.section_id];
            if (section) {
                // Calculate hours from timeslots (assuming each timeslot is the credit hours)
                for (const timeslot of section.timeslots) {
                    totalHours += timeslot.end_hour - timeslot.start_hour;
                }
            }
        }
    }
    return totalHours;
}

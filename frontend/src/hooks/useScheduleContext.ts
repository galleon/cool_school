import { useCallback, useEffect, useState } from "react";

import { SCHEDULE_STATE_URL } from "../lib/config";

export type TimeSlot = {
    day: number;
    start_hour: number;
    end_hour: number;
};

export type Teacher = {
    id: string;
    name: string;
    max_load_hours: number;
    qualified_courses: string[];
    availability: TimeSlot[];
};

export type Section = {
    id: string;
    course_code: string;
    timeslots: TimeSlot[];
    enrollment: number;
    required_feature: string | null;
};

export type Room = {
    id: string;
    capacity: number;
    features: string[];
};

export type Assignment = {
    section_id: string;
    teacher_id: string | null;
    room_id: string | null;
    assigned_at: string;
};

export type TimelineEntry = {
    timestamp: string;
    kind: string;
    entry: string;
};

export type ScheduleState = {
    teachers: Record<string, Teacher>;
    sections: Record<string, Section>;
    assignments: Record<string, Assignment>;
    rooms: Record<string, Room>;
    timeline: TimelineEntry[];
};

type ScheduleResponse = {
    schedule: ScheduleState;
};

export function useScheduleContext(threadId: string | null) {
    const [schedule, setSchedule] = useState<ScheduleState | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchSchedule = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const url = threadId
                ? `${SCHEDULE_STATE_URL}?thread_id=${encodeURIComponent(threadId)}`
                : SCHEDULE_STATE_URL;
            const response = await fetch(url, {
                headers: { Accept: "application/json" },
            });
            if (!response.ok) {
                throw new Error(`Failed to load schedule context (${response.status})`);
            }
            const payload = (await response.json()) as ScheduleResponse;
            setSchedule(payload.schedule);
        } catch (err) {
            const message = err instanceof Error ? err.message : String(err);
            setError(message);
            setSchedule(null);
        } finally {
            setLoading(false);
        }
    }, [threadId]);

    useEffect(() => {
        void fetchSchedule();
    }, [fetchSchedule]);

    return { schedule, loading, error, refresh: fetchSchedule };
}

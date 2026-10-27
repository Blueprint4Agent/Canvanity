import { useCallback, useEffect, useRef, useState } from "react";
import {
    BoardRequestError,
    createBoard,
    deleteEmptyBoard,
    getBoardHome,
    listBoards,
    type BoardCreateInput,
    type BoardHome,
    type BoardSummary,
} from "../../../api/boards/boardsApi";
import { useAuthContext } from "../../useAuth";
import { useServerConnectivity } from "../../connectivity/useServerConnectivity";
export type { BoardCreateInput, BoardHome, BoardSummary } from "../../../api/boards/boardsApi";

function errorCode(error: unknown): string {
    return error instanceof BoardRequestError ? error.code : "BOARD_UNAVAILABLE";
}
function useBoardQuery<T>(queryKey: string, load: (signal: AbortSignal) => Promise<T>) {
    const { user, loading: authLoading } = useAuthContext();
    const { isDesktop, status } = useServerConnectivity();
    const available = !authLoading && (!isDesktop || status === "online");
    const key = JSON.stringify([user?.id ?? null, queryKey]);
    const [snapshot, setSnapshot] = useState<{
        key: string;
        data?: T;
        error?: string;
        loading: boolean;
    } | null>(null);
    const [revision, setRevision] = useState(0);
    const reload = useCallback(() => setRevision((value) => value + 1), []);
    useEffect(() => {
        if (!available) return;
        const controller = new AbortController();
        setSnapshot({ key, loading: true });
        void load(controller.signal)
            .then((data) => {
                if (!controller.signal.aborted) setSnapshot({ key, data, loading: false });
            })
            .catch((error: unknown) => {
                if (!controller.signal.aborted)
                    setSnapshot({ key, error: errorCode(error), loading: false });
            });
        return () => controller.abort();
    }, [key, available, revision, load]);
    const current = snapshot?.key === key && available ? snapshot : null;
    return {
        data: current?.data,
        error: current?.error,
        loading: authLoading || (current?.loading ?? available),
        available,
        reload,
    };
}
export function useBoards(q: string, mine: boolean, cursor: string | undefined) {
    const load = useCallback(
        (signal: AbortSignal) => listBoards(q, mine, cursor, signal),
        [q, mine, cursor],
    );
    return useBoardQuery(JSON.stringify([q, mine, cursor]), load);
}
export function useBoardHome(slug: string) {
    const load = useCallback((signal: AbortSignal) => getBoardHome(slug, signal), [slug]);
    return useBoardQuery(slug, load);
}
export function useBoardActions() {
    const { user } = useAuthContext();
    const { isDesktop, status } = useServerConnectivity();
    const available = !!user && (!isDesktop || status === "online");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const active = useRef<AbortController | null>(null);
    const owner = user?.id;
    const identity = useRef(owner);
    identity.current = owner;
    useEffect(() => {
        setBusy(false);
        setError(null);
        return () => {
            active.current?.abort();
            active.current = null;
        };
    }, [owner]);
    const submit = useCallback(
        async <T>(action: (signal: AbortSignal) => Promise<T>): Promise<T | undefined> => {
            if (!available || active.current) return undefined;
            const actor = identity.current;
            const controller = new AbortController();
            active.current = controller;
            setBusy(true);
            setError(null);
            try {
                const result = await action(controller.signal);
                return controller.signal.aborted || identity.current !== actor ? undefined : result;
            } catch (error: unknown) {
                if (!controller.signal.aborted) setError(errorCode(error));
                return undefined;
            } finally {
                if (active.current === controller) {
                    active.current = null;
                    setBusy(false);
                }
            }
        },
        [available],
    );
    return {
        busy,
        error,
        available,
        clearError: () => setError(null),
        create: (input: BoardCreateInput) => submit((signal) => createBoard(input, signal)),
        remove: (board: BoardSummary, slug: string) =>
            submit(async (signal) => {
                await deleteEmptyBoard(board.id, board.revision, slug, signal);
                return true;
            }),
    };
}

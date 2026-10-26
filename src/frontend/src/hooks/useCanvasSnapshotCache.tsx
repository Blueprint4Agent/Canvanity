import { createContext, useContext, useMemo, useRef, type ReactNode } from "react";

type SnapshotCache = Map<string, string>;
const Context = createContext<SnapshotCache | null>(null);

/** Replace only account-owned pixels; preserve the mounted page and user input. */
export function CanvasSnapshotCacheProvider({
    children,
    owner,
}: {
    children: ReactNode;
    owner: string | number;
}) {
    const cache = useMemo<SnapshotCache>(() => new Map(), [owner]);
    return <Context.Provider value={cache}>{children}</Context.Provider>;
}
export function useCanvasSnapshotCache() {
    const shared = useContext(Context);
    const local = useRef<SnapshotCache>(new Map());
    return shared ?? local.current;
}

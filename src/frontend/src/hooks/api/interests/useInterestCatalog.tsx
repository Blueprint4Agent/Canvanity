import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
    type ReactNode,
} from "react";
import { getInterests, type InterestItem } from "../../../api/interests/interestsApi";
export type { InterestItem } from "../../../api/interests/interestsApi";
const Context = createContext<{
    items: InterestItem[];
    loading: boolean;
    error: boolean;
    reload: () => void;
}>({ items: [], loading: false, error: true, reload: () => {} });
export function InterestCatalogProvider({ children }: { children: ReactNode }) {
    const [items, setItems] = useState<InterestItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    const [revision, setRevision] = useState(0);
    const reload = useCallback(() => setRevision((value) => value + 1), []);
    useEffect(() => {
        const controller = new AbortController();
        setLoading(true);
        setError(false);
        void getInterests(controller.signal)
            .then((items) => {
                if (!controller.signal.aborted) setItems(items);
            })
            .catch(() => {
                if (!controller.signal.aborted) setError(true);
            })
            .finally(() => {
                if (!controller.signal.aborted) setLoading(false);
            });
        return () => controller.abort();
    }, [revision]);
    const value = useMemo(
        () => ({ items, loading, error, reload }),
        [items, loading, error, reload],
    );
    return <Context.Provider value={value}>{children}</Context.Provider>;
}
export const useInterestCatalog = () => useContext(Context);

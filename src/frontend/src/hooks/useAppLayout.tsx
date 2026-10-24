import { createContext, useContext, type ReactNode } from "react";
import type { AppLayoutMode } from "../service.config";

// Canvanity intentionally exposes one minimal shell. Legacy provider values and
// stored layout previews remain compatible inputs, but cannot change the shell.
const value = {
    mode: "focused" as AppLayoutMode,
    canPreview: false,
    isPreviewing: false,
    resetPreview: () => undefined,
    setMode: (_mode: AppLayoutMode) => undefined,
};
const LayoutContext = createContext(value);
export function AppLayoutProvider({ children }: { children: ReactNode }) {
    return <LayoutContext.Provider value={value}>{children}</LayoutContext.Provider>;
}
export function useAppLayout() {
    return useContext(LayoutContext);
}

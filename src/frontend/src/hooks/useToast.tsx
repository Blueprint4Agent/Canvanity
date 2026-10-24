import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";
import { ToastCard, type ToastTone } from "../components/ui/overlays/ToastCard";

type ShowToast = (message: string, options?: { tone?: ToastTone }) => void;
const ToastContext = createContext<ShowToast | null>(null);

/** One transient notice survives navigation; consumers subscribe only to stable dispatch. */
export function ToastProvider({ children }: { children: ReactNode }) {
    const [notice, setNotice] = useState<{ id: number; message: string; tone: ToastTone } | null>(
        null,
    );
    const sequence = useRef(0);
    const showToast = useCallback<ShowToast>((message, options) => {
        if (message.trim())
            setNotice({
                id: ++sequence.current,
                message: message.trim(),
                tone: options?.tone ?? "neutral",
            });
    }, []);
    return (
        <ToastContext.Provider value={showToast}>
            {children}
            {notice ? (
                <ToastCard
                    key={notice.id}
                    message={notice.message}
                    tone={notice.tone}
                    onDismiss={() => {
                        setNotice((current) => (current?.id === notice.id ? null : current));
                    }}
                />
            ) : null}
        </ToastContext.Provider>
    );
}

export function useToast(): ShowToast {
    const showToast = useContext(ToastContext);
    if (!showToast) throw new Error("useToast must be used inside <ToastProvider>.");
    return showToast;
}

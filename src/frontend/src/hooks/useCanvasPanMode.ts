import { useEffect, useState } from "react";

/** Mouse pan is momentary. Text editing and dialogs keep native Space behavior. */
export function useCanvasPanMode(): boolean {
    const [held, setHeld] = useState(false);
    useEffect(() => {
        let pressed = false;
        const release = () => {
            pressed = false;
            setHeld(false);
        };
        const down = (event: KeyboardEvent) => {
            if (
                event.code !== "Space" ||
                event.ctrlKey ||
                event.metaKey ||
                event.altKey ||
                event.isComposing
            )
                return;
            if (document.querySelector('[role="dialog"]')) return;
            if (
                event.target instanceof Element &&
                event.target.closest(
                    'input,textarea,select,[contenteditable]:not([contenteditable="false"]),[role="textbox"]',
                )
            )
                return;
            event.preventDefault();
            if (!pressed) {
                pressed = true;
                setHeld(true);
            }
        };
        const up = (event: KeyboardEvent) => {
            if (event.code === "Space" && pressed) {
                event.preventDefault();
                release();
            }
        };
        const visibility = () => {
            if (document.hidden) release();
        };
        window.addEventListener("keydown", down, { capture: true });
        window.addEventListener("keyup", up, { capture: true });
        window.addEventListener("blur", release);
        document.addEventListener("visibilitychange", visibility);
        return () => {
            window.removeEventListener("keydown", down, { capture: true });
            window.removeEventListener("keyup", up, { capture: true });
            window.removeEventListener("blur", release);
            document.removeEventListener("visibilitychange", visibility);
        };
    }, []);
    return held;
}

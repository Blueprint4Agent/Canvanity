import { useEffect, type RefObject } from "react";
import { canvasAction, type CanvasAction } from "../canvas/canvasRules";
/** Active mounted surface only; text editing, IME, dialogs and browser chords are excluded. */
export function useCanvasShortcuts(
    viewport: RefObject<HTMLElement>,
    actions: Partial<Record<CanvasAction, () => void>>,
) {
    useEffect(() => {
        const key = (event: KeyboardEvent) => {
            if (
                event.defaultPrevented ||
                !viewport.current ||
                document.querySelector('[role="dialog"], .profile-menu__dropdown')
            )
                return;
            if (
                event.target instanceof HTMLElement &&
                event.target.closest("input,textarea,select,[contenteditable=true],[role=textbox]")
            )
                return;
            const action = canvasAction(event);
            if (action && actions[action]) {
                event.preventDefault();
                actions[action]?.();
            }
        };
        window.addEventListener("keydown", key, { capture: true });
        return () => window.removeEventListener("keydown", key, { capture: true });
    }, [viewport, actions]);
}

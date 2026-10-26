import { useMemo, type ReactNode } from "react";
import { useCanvasCamera } from "../../../hooks/useCanvasCamera";
import { useCanvasPanMode } from "../../../hooks/useCanvasPanMode";
import { useCanvasShortcuts } from "../../../hooks/useCanvasShortcuts";
import { CANVAS_RULES } from "../../../canvas/canvasRules";

import { EXPLORE_SURFACE, EXPLORE_OVERVIEW, INTRO_RECT } from "./exploreTopics";
import { CanvasControls } from "./CanvasControls";
import { useCanvasSnapshot } from "../../../hooks/useCanvasSnapshot";
type Props = { children: ReactNode; label: string; contentVersion?: string };

/** Document and account state remain with the page; chrome matches Plaza. */
export function CommunityCanvas({ children, label, contentVersion = label }: Props) {
    const spaceHeld = useCanvasPanMode();
    const camera = useCanvasCamera(EXPLORE_SURFACE, INTRO_RECT, EXPLORE_OVERVIEW, spaceHeld);
    const snapshot = useCanvasSnapshot(camera.worldRef, EXPLORE_SURFACE, contentVersion);
    const { zoomAt, fit, viewportRef } = camera;
    const actions = useMemo(
        () => ({
            select: () => viewportRef.current?.focus({ preventScroll: true }),
            search: () => {},
            zoomIn: () => zoomAt(CANVAS_RULES.zoomStep),
            zoomOut: () => zoomAt(1 / CANVAS_RULES.zoomStep),
            fit,
        }),
        [zoomAt, fit, viewportRef],
    );
    useCanvasShortcuts(viewportRef, actions);
    return (
        <div className="explore-page community-canvas" data-tool={spaceHeld ? "hand" : "select"}>
            <div
                ref={viewportRef}
                className="explore-viewport"
                tabIndex={0}
                aria-label={label}
                data-dragging={camera.dragging}
                onClickCapture={camera.onClickCapture}
                onPointerDown={camera.onPointerDown}
                onPointerMove={camera.onPointerMove}
                onPointerUp={camera.onPointerUp}
                onPointerCancel={camera.onPointerUp}
                onLostPointerCapture={camera.onPointerUp}
                onKeyDown={(event) => {
                    if (!["+", "=", "-", "0"].includes(event.key)) camera.onKeyDown(event);
                }}
            >
                <div ref={camera.worldRef} className="explore-world">
                    <div className="community-canvas__content">{children}</div>
                </div>
            </div>
            <CanvasControls
                camera={camera}
                snapshot={snapshot}
                spaceHeld={spaceHeld}
                onReset={fit}
            />
        </div>
    );
}

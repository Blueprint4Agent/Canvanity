import { Hand, MousePointer2, Plus, Minus, Scan } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button, Tooltip, KeyboardShortcut, Spinner } from "../../ui";
import { CANVAS_RULES, CANVAS_SHORTCUTS, CANVAS_PAN_KEY } from "../../../canvas/canvasRules";
import type { useCanvasCamera } from "../../../hooks/useCanvasCamera";
import type { useCanvasSnapshot } from "../../../hooks/useCanvasSnapshot";

type Props = {
    camera: ReturnType<typeof useCanvasCamera>;
    snapshot: ReturnType<typeof useCanvasSnapshot>;
    spaceHeld: boolean;
    onReset: () => void;
};

/** Identical controls on every community space; only the scene snapshot changes. */
export function CanvasControls({ camera, snapshot, spaceHeld, onReset }: Props) {
    const { t } = useTranslation();
    const tool = spaceHeld ? "hand" : "select";
    return (
        <>
            <nav className="explore-tools" aria-label={t("explore.tools")}>
                <Tooltip
                    content={
                        <span className="ui-shortcut-hint">
                            {t("explore.select")}
                            <KeyboardShortcut keys={[CANVAS_SHORTCUTS.select.toUpperCase()]} />
                        </span>
                    }
                    side="right"
                >
                    <Button
                        appearance="canvas"
                        iconOnly
                        aria-label={t("explore.select")}
                        aria-pressed={tool === "select"}
                        onClick={() => camera.viewportRef.current?.focus({ preventScroll: true })}
                    >
                        <MousePointer2 size={20} />
                    </Button>
                </Tooltip>
                <Tooltip
                    content={
                        <span className="ui-shortcut-hint">
                            {t("explore.panHold")}
                            <KeyboardShortcut keys={[CANVAS_PAN_KEY]} />
                        </span>
                    }
                    side="right"
                >
                    <span
                        className="explore-pan-hint"
                        tabIndex={0}
                        role="img"
                        aria-label={t("explore.panHold")}
                        data-active={spaceHeld}
                    >
                        <Hand size={20} />
                    </span>
                </Tooltip>
            </nav>
            <div className="explore-map">
                <div className="explore-zoom-tools">
                    <span className="explore-zoom" aria-label={t("explore.zoomLevel")}>
                        {Math.round(camera.zoom * 100)}%
                    </span>
                    <Tooltip
                        content={
                            <span className="ui-shortcut-hint">
                                {t("explore.zoomIn")}
                                <KeyboardShortcut keys={["mod", CANVAS_SHORTCUTS.zoomIn]} />
                            </span>
                        }
                        side="right"
                    >
                        <Button
                            appearance="canvas"
                            iconOnly
                            aria-label={t("explore.zoomIn")}
                            disabled={camera.zoom >= CANVAS_RULES.maxZoom}
                            aria-keyshortcuts="+"
                            onClick={() => camera.zoomAt(CANVAS_RULES.zoomStep)}
                        >
                            <Plus size={20} />
                        </Button>
                    </Tooltip>
                    <Tooltip
                        content={
                            <span className="ui-shortcut-hint">
                                {t("explore.zoomOut")}
                                <KeyboardShortcut keys={["mod", CANVAS_SHORTCUTS.zoomOut]} />
                            </span>
                        }
                        side="right"
                    >
                        <Button
                            appearance="canvas"
                            iconOnly
                            aria-label={t("explore.zoomOut")}
                            disabled={camera.zoom <= CANVAS_RULES.minZoom}
                            aria-keyshortcuts="-"
                            onClick={() => camera.zoomAt(1 / CANVAS_RULES.zoomStep)}
                        >
                            <Minus size={20} />
                        </Button>
                    </Tooltip>
                    <Tooltip
                        content={
                            <span className="ui-shortcut-hint">
                                {t("explore.fit")}
                                <KeyboardShortcut keys={["mod", CANVAS_SHORTCUTS.fit]} />
                            </span>
                        }
                        side="right"
                    >
                        <Button
                            appearance="canvas"
                            iconOnly
                            aria-label={t("explore.fit")}
                            aria-keyshortcuts="0"
                            onClick={onReset}
                        >
                            <Scan size={20} />
                        </Button>
                    </Tooltip>
                </div>
                <Button
                    appearance="canvas"
                    className="explore-minimap"
                    aria-label={t("explore.mapNavigate")}
                    onClick={camera.onMapClick}
                    onPointerDown={camera.onMapPointerDown}
                    onPointerMove={camera.onMapPointerMove}
                    onPointerUp={camera.onMapPointerUp}
                    onPointerCancel={camera.onMapPointerUp}
                    onLostPointerCapture={camera.onMapPointerUp}
                    disabled={!snapshot.image}
                    aria-busy={snapshot.loading}
                >
                    <span className="explore-minimap__canvas" aria-hidden="true">
                        {snapshot.image ? (
                            <img src={snapshot.image} alt="" draggable={false} />
                        ) : (
                            <span className="explore-snapshot-status">
                                {snapshot.failed ? (
                                    t("explore.snapshotError")
                                ) : (
                                    <Spinner
                                        size="sm"
                                        label={t("explore.snapshotLoading")}
                                        hideLabel
                                    />
                                )}
                            </span>
                        )}
                        <span ref={camera.mapWindowRef} className="explore-minimap__viewport" />
                    </span>
                </Button>
                {snapshot.failed ? (
                    <Button appearance="canvas" onClick={snapshot.refresh}>
                        {t("explore.retrySnapshot")}
                    </Button>
                ) : null}
            </div>
        </>
    );
}

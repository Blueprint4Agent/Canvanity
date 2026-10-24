/** Shared interaction contract. A UI menu and a stored document have distinct owners. */
export type CanvasSurface = {
    kind: "ui" | "document";
    bounds: { width: number; height: number };
};
export type CanvasCamera = { x: number; y: number; zoom: number };
export const CANVAS_RULES = {
    minZoom: 0.25,
    maxZoom: 2,
    zoomStep: 1.2,
    gridSize: 28,
    panStep: 56,
} as const;
export const CANVAS_SHORTCUTS = {
    select: "v",
    search: "/",
    zoomIn: "+",
    zoomOut: "-",
    fit: "0",
} as const;
export const CANVAS_PAN_KEY = "space";
export type CanvasAction = keyof typeof CANVAS_SHORTCUTS;
export function canvasAction(
    event: Pick<KeyboardEvent, "key" | "ctrlKey" | "metaKey" | "altKey" | "isComposing">,
): CanvasAction | null {
    if (event.altKey || event.isComposing) return null;
    if ((event.ctrlKey || event.metaKey) && !["+", "=", "-", "0"].includes(event.key)) return null;
    const key = event.key === "=" ? "+" : event.key.toLowerCase();
    return (
        (Object.keys(CANVAS_SHORTCUTS) as CanvasAction[]).find(
            (action) => CANVAS_SHORTCUTS[action] === key,
        ) ?? null
    );
}
export function validateSurface(surface: CanvasSurface): CanvasSurface {
    if (
        ![surface.bounds.width, surface.bounds.height].every(
            (value) => Number.isFinite(value) && value > 0,
        )
    )
        throw new Error("Canvas bounds must be positive finite dimensions");
    return surface;
}
export function clampZoom(value: number): number {
    return Math.max(
        CANVAS_RULES.minZoom,
        Math.min(CANVAS_RULES.maxZoom, Number.isFinite(value) ? value : 1),
    );
}
/** Center undersized worlds; larger worlds may pan only as far as their edges. */
export function constrainCamera(
    camera: CanvasCamera,
    surface: CanvasSurface,
    viewport: { width: number; height: number },
): CanvasCamera {
    const zoom = clampZoom(camera.zoom);
    const axis = (position: number, size: number, available: number) =>
        size * zoom <= available
            ? (available - size * zoom) / 2
            : Math.max(
                  available - size * zoom,
                  Math.min(0, Number.isFinite(position) ? position : 0),
              );
    return {
        x: axis(camera.x, surface.bounds.width, viewport.width),
        y: axis(camera.y, surface.bounds.height, viewport.height),
        zoom,
    };
}

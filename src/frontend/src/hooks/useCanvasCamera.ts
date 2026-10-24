import { useCallback, useEffect, useRef, useState } from "react";
import type { KeyboardEvent, PointerEvent, MouseEvent } from "react";
import {
    clampZoom,
    constrainCamera,
    validateSurface,
    CANVAS_RULES,
    type CanvasSurface,
} from "../canvas/canvasRules";

type Camera = import("../canvas/canvasRules").CanvasCamera;
type Point = { x: number; y: number };
const distance = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y);

/** High-frequency camera geometry stays outside React's content render loop. */
export function useCanvasCamera(
    surface: CanvasSurface,
    initialFocus?: { x: number; y: number; width: number; height: number },
    initialOverview?: { x: number; y: number; width: number; height: number },
    panEnabled = false,
) {
    validateSurface(surface);
    const WORLD = surface.bounds;
    const viewportRef = useRef<HTMLDivElement>(null);
    const worldRef = useRef<HTMLDivElement>(null);
    const mapWindowRef = useRef<HTMLSpanElement>(null);
    const camera = useRef<Camera>({ x: 0, y: 0, zoom: 1 });
    const frame = useRef<number | null>(null);
    const rendered = useRef<Camera | null>(null);
    const animate = useRef(false);
    const lastFrame = useRef(0);
    const pointers = useRef(new Map<number, Point>());
    const suppressClick = useRef(false);
    const gesture = useRef<{ camera: Camera; points: Point[] } | null>(null);
    const [zoom, setZoom] = useState(1);
    const [dragging, setDragging] = useState(false);

    useEffect(() => {
        if (!panEnabled) {
            for (const id of pointers.current.keys()) {
                if (viewportRef.current?.hasPointerCapture(id))
                    viewportRef.current.releasePointerCapture(id);
            }
            pointers.current.clear();
            gesture.current = null;
            setDragging(false);
        }
    }, [panEnabled]);

    const paint = useCallback(
        (smooth = false) => {
            animate.current =
                smooth && !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
            if (worldRef.current) worldRef.current.dataset.cameraMoving = String(animate.current);
            if (frame.current !== null) return;
            const draw = (time: number) => {
                frame.current = null;
                const viewport = viewportRef.current;
                const world = worldRef.current;
                if (!viewport || !world) return;
                const target = constrainCamera(camera.current, surface, {
                    width: viewport.clientWidth,
                    height: viewport.clientHeight,
                });
                camera.current = target;
                const previous = rendered.current ?? target;
                const progress = animate.current
                    ? 1 - Math.exp(-Math.min(40, time - (lastFrame.current || time - 16)) / 65)
                    : 1;
                const next = constrainCamera(
                    {
                        x: previous.x + (target.x - previous.x) * progress,
                        y: previous.y + (target.y - previous.y) * progress,
                        zoom: previous.zoom + (target.zoom - previous.zoom) * progress,
                    },
                    surface,
                    { width: viewport.clientWidth, height: viewport.clientHeight },
                );
                rendered.current = next;
                lastFrame.current = time;
                world.style.transform = `translate3d(${next.x}px, ${next.y}px, 0) scale(${next.zoom})`;
                world.style.width = `${WORLD.width}px`;
                world.style.height = `${WORLD.height}px`;
                viewport.style.backgroundSize = `${CANVAS_RULES.gridSize * next.zoom}px ${CANVAS_RULES.gridSize * next.zoom}px`;
                viewport.style.backgroundPosition = `${next.x}px ${next.y}px`;
                const mapWindow = mapWindowRef.current;
                if (mapWindow) {
                    mapWindow.hidden =
                        viewport.clientWidth >= WORLD.width * next.zoom &&
                        viewport.clientHeight >= WORLD.height * next.zoom;
                    mapWindow.style.left = `${Math.max(0, -next.x / next.zoom / WORLD.width) * 100}%`;
                    mapWindow.style.top = `${Math.max(0, -next.y / next.zoom / WORLD.height) * 100}%`;
                    mapWindow.style.width = `${Math.min(1, viewport.clientWidth / next.zoom / WORLD.width) * 100}%`;
                    mapWindow.style.height = `${Math.min(1, viewport.clientHeight / next.zoom / WORLD.height) * 100}%`;
                }
                const pending =
                    Math.abs(next.zoom - target.zoom) > 0.0001 ||
                    Math.abs(next.x - target.x) > 0.1 ||
                    Math.abs(next.y - target.y) > 0.1;
                world.dataset.cameraMoving = String(animate.current && pending);
                if (animate.current && pending) frame.current = requestAnimationFrame(draw);
                else {
                    animate.current = false;
                    lastFrame.current = 0;
                }
            };
            frame.current = requestAnimationFrame(draw);
        },
        [surface, WORLD.width, WORLD.height],
    );
    const focus = useCallback(
        (rect: { x: number; y: number; width: number; height: number }) => {
            const viewport = viewportRef.current;
            if (!viewport) return;
            const next = clampZoom(
                Math.min(
                    1.2,
                    (viewport.clientWidth - 56) / rect.width,
                    (viewport.clientHeight - 120) / rect.height,
                ),
            );
            camera.current = {
                x: viewport.clientWidth / 2 - (rect.x + rect.width / 2) * next,
                y: viewport.clientHeight / 2 - (rect.y + rect.height / 2) * next,
                zoom: next,
            };
            setZoom(next);
            paint(true);
        },
        [paint],
    );
    const fit = useCallback(() => {
        const viewport = viewportRef.current;
        if (!viewport) return;
        const next = clampZoom(
            Math.min(
                1,
                (viewport.clientWidth - 80) / WORLD.width,
                (viewport.clientHeight - 60) / WORLD.height,
            ),
        );
        camera.current = {
            x: (viewport.clientWidth - WORLD.width * next) / 2,
            y: (viewport.clientHeight - WORLD.height * next) / 2,
            zoom: next,
        };
        setZoom(next);
        paint(true);
    }, [paint]);
    const zoomAt = useCallback(
        (factor: number, point?: Point) => {
            const viewport = viewportRef.current;
            if (!viewport) return;
            const origin = point ?? { x: viewport.clientWidth / 2, y: viewport.clientHeight / 2 };
            const previous = camera.current;
            const next = clampZoom(previous.zoom * factor);
            camera.current = {
                x: origin.x - ((origin.x - previous.x) * next) / previous.zoom,
                y: origin.y - ((origin.y - previous.y) * next) / previous.zoom,
                zoom: next,
            };
            setZoom(next);
            paint(true);
        },
        [paint],
    );
    const move = useCallback(
        (x: number, y: number) => {
            camera.current = {
                ...camera.current,
                x: camera.current.x + x,
                y: camera.current.y + y,
            };
            paint();
        },
        [paint],
    );
    useEffect(() => {
        const viewport = viewportRef.current;
        if (!viewport) return;
        const resize = () =>
            viewport.clientWidth < 700 && initialFocus
                ? focus(initialFocus)
                : initialOverview
                  ? focus(initialOverview)
                  : fit();
        const observer = new ResizeObserver(resize);
        observer.observe(viewport);
        let nativePinch = false;
        const wheel = (event: WheelEvent) => {
            event.preventDefault();
            if (nativePinch) return;
            const multiplier =
                event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? viewport.clientHeight : 1;
            // Trackpad pinch is delivered as Ctrl+wheel in Chromium/Firefox.
            if (event.altKey || event.ctrlKey || event.metaKey) {
                const bounds = viewport.getBoundingClientRect();
                zoomAt(Math.exp(-event.deltaY * multiplier * 0.006), {
                    x: event.clientX - bounds.left,
                    y: event.clientY - bounds.top,
                });
            } else move(-event.deltaX * multiplier, -event.deltaY * multiplier);
        };
        let gestureScale = 1;
        const nativeGesture = (event: Event) => {
            event.preventDefault();
            const gestureEvent = event as Event & {
                scale: number;
                clientX: number;
                clientY: number;
            };
            if (event.type === "gesturestart") {
                nativePinch = true;
                gestureScale = 1;
                return;
            }
            if (event.type === "gestureend") {
                nativePinch = false;
                return;
            }
            if (!Number.isFinite(gestureEvent.scale) || gestureEvent.scale <= 0) return;
            const rect = viewport.getBoundingClientRect();
            zoomAt(gestureEvent.scale / gestureScale, {
                x: gestureEvent.clientX - rect.left,
                y: gestureEvent.clientY - rect.top,
            });
            gestureScale = gestureEvent.scale;
        };
        viewport.addEventListener("gesturestart", nativeGesture, { passive: false });
        viewport.addEventListener("gesturechange", nativeGesture, { passive: false });
        viewport.addEventListener("gestureend", nativeGesture, { passive: false });
        viewport.addEventListener("wheel", wheel, { passive: false });
        resize();
        return () => {
            observer.disconnect();
            viewport.removeEventListener("wheel", wheel);
            viewport.removeEventListener("gesturestart", nativeGesture);
            viewport.removeEventListener("gesturechange", nativeGesture);
            viewport.removeEventListener("gestureend", nativeGesture);
            if (frame.current !== null) cancelAnimationFrame(frame.current);
            frame.current = null;
            pointers.current.clear();
        };
    }, [fit, focus, move, zoomAt, initialFocus, initialOverview]);
    const beginGesture = () => {
        gesture.current = { camera: { ...camera.current }, points: [...pointers.current.values()] };
    };
    const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
        if (event.button !== 0 || (event.pointerType !== "touch" && !panEnabled)) return;
        if (!pointers.current.size) suppressClick.current = false;
        if (rendered.current) camera.current = { ...rendered.current };
        animate.current = false;
        pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY });
        beginGesture();
        if (event.pointerType !== "touch") {
            event.preventDefault();
            event.currentTarget.setPointerCapture(event.pointerId);
            event.currentTarget.focus({ preventScroll: true });
            setDragging(true);
        }
    };
    const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
        if (!pointers.current.has(event.pointerId) || !gesture.current) return;
        pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY });
        const current = [...pointers.current.values()];
        const start = gesture.current;
        if (event.pointerType === "touch") {
            if (current.length === 1 && distance(current[0], start.points[0]) < 5) return;
            suppressClick.current = true;
            event.currentTarget.setPointerCapture(event.pointerId);
            setDragging(true);
        }
        if (current.length >= 2 && start.points.length >= 2) {
            const viewport = viewportRef.current!;
            const bounds = viewport.getBoundingClientRect();
            const origin = {
                x: (start.points[0].x + start.points[1].x) / 2 - bounds.left,
                y: (start.points[0].y + start.points[1].y) / 2 - bounds.top,
            };
            const next = clampZoom(
                (start.camera.zoom * distance(current[0], current[1])) /
                    Math.max(1, distance(start.points[0], start.points[1])),
            );
            const midpoint = {
                x: (current[0].x + current[1].x) / 2 - bounds.left,
                y: (current[0].y + current[1].y) / 2 - bounds.top,
            };
            camera.current = {
                x: midpoint.x - ((origin.x - start.camera.x) * next) / start.camera.zoom,
                y: midpoint.y - ((origin.y - start.camera.y) * next) / start.camera.zoom,
                zoom: next,
            };
        } else
            camera.current = {
                ...start.camera,
                x: start.camera.x + current[0].x - start.points[0].x,
                y: start.camera.y + current[0].y - start.points[0].y,
            };
        paint();
    };
    const onClickCapture = (event: MouseEvent<HTMLDivElement>) => {
        if (suppressClick.current) {
            suppressClick.current = false;
            event.preventDefault();
            event.stopPropagation();
        }
    };
    const onPointerUp = (event: PointerEvent<HTMLDivElement>) => {
        pointers.current.delete(event.pointerId);
        if (event.currentTarget.hasPointerCapture(event.pointerId))
            event.currentTarget.releasePointerCapture(event.pointerId);
        if (pointers.current.size) beginGesture();
        else {
            gesture.current = null;
            setDragging(false);
            setZoom(camera.current.zoom);
        }
    };
    const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
        if (
            event.target !== event.currentTarget ||
            event.ctrlKey ||
            event.metaKey ||
            event.altKey ||
            event.nativeEvent.isComposing
        )
            return;
        const steps: Record<string, [number, number]> = {
            ArrowLeft: [CANVAS_RULES.panStep, 0],
            ArrowRight: [-CANVAS_RULES.panStep, 0],
            ArrowUp: [0, CANVAS_RULES.panStep],
            ArrowDown: [0, -CANVAS_RULES.panStep],
        };
        if (steps[event.key]) {
            event.preventDefault();
            move(...steps[event.key]);
        }
    };
    const mapDragging = useRef(false);
    const navigateMap = (element: HTMLButtonElement, clientX: number, clientY: number) => {
        const rect = element.getBoundingClientRect();
        const viewport = viewportRef.current;
        if (!viewport) return;
        const x = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
        const y = Math.max(0, Math.min(1, (clientY - rect.top) / rect.height));
        camera.current = {
            ...camera.current,
            x: viewport.clientWidth / 2 - x * WORLD.width * camera.current.zoom,
            y: viewport.clientHeight / 2 - y * WORLD.height * camera.current.zoom,
        };
        paint();
    };
    const onMapClick = (event: MouseEvent<HTMLButtonElement>) => {
        const r = event.currentTarget.getBoundingClientRect();
        navigateMap(
            event.currentTarget,
            event.detail === 0 ? r.left + r.width / 2 : event.clientX,
            event.detail === 0 ? r.top + r.height / 2 : event.clientY,
        );
    };
    const onMapPointerDown = (event: PointerEvent<HTMLButtonElement>) => {
        if (event.button !== 0) return;
        mapDragging.current = true;
        event.currentTarget.setPointerCapture(event.pointerId);
        navigateMap(event.currentTarget, event.clientX, event.clientY);
    };
    const onMapPointerMove = (event: PointerEvent<HTMLButtonElement>) => {
        if (mapDragging.current) navigateMap(event.currentTarget, event.clientX, event.clientY);
    };
    const onMapPointerUp = (event: PointerEvent<HTMLButtonElement>) => {
        mapDragging.current = false;
        if (event.currentTarget.hasPointerCapture(event.pointerId))
            event.currentTarget.releasePointerCapture(event.pointerId);
    };
    return {
        viewportRef,
        worldRef,
        mapWindowRef,
        zoom,
        dragging,
        fit,
        focus,
        zoomAt,
        onMapClick,
        onMapPointerDown,
        onMapPointerMove,
        onMapPointerUp,
        onClickCapture,
        onPointerDown,
        onPointerMove,
        onPointerUp,
        onKeyDown,
    };
}

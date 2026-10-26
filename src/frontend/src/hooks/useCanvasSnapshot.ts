import { useCanvasSnapshotCache } from "./useCanvasSnapshotCache";
import { useCallback, useEffect, useRef, useState, type RefObject } from "react";
import { CANVAS_RULES, type CanvasSurface } from "../canvas/canvasRules";

// Font resources are public and shared across scenes; pixels stay in the account provider.
let fontCSS: Promise<string> | undefined;
let captureQueue: Promise<void> = Promise.resolve();

/** Scene snapshots refresh on content/appearance changes, never on camera movement. */
export function useCanvasSnapshot(
    worldRef: RefObject<HTMLDivElement>,
    surface: CanvasSurface,
    contentVersion: string,
) {
    const WORLD = surface.bounds;
    const cache = useCanvasSnapshotCache();
    const [snapshot, setSnapshot] = useState<{ owner: typeof cache; image: string } | null>(null);
    const image = snapshot?.owner === cache ? snapshot.image : null;
    const [failed, setFailed] = useState(false);
    const [loading, setLoading] = useState(true);
    const [retry, setRetry] = useState(0);
    const generation = useRef(0);
    const refresh = useCallback(() => setRetry((value) => value + 1), []);
    useEffect(() => {
        let disposed = false;
        let timer: number | undefined;
        const capture = async (key: string, current: number) => {
            const node = worldRef.current;
            if (!node || disposed || current !== generation.current) return;
            const existing = cache.get(key);
            if (existing && retry === 0) {
                setSnapshot({ owner: cache, image: existing });
                setLoading(false);
                return;
            }
            setLoading(true);
            try {
                await Promise.all(
                    Array.from(node.querySelectorAll("img")).map((img) =>
                        img.decode().catch(() => undefined),
                    ),
                );
                await document.fonts.ready;
                const { toCanvas, getFontEmbedCSS } = await import("html-to-image");
                fontCSS ??= getFontEmbedCSS(document.body).catch((error) => {
                    fontCSS = undefined;
                    throw error;
                });
                const fontEmbedCSS = await fontCSS;
                if (disposed || current !== generation.current) return;
                const background = getComputedStyle(node.parentElement!);
                const canvas = await toCanvas(node, {
                    width: WORLD.width,
                    height: WORLD.height,
                    canvasWidth: 288,
                    canvasHeight: Math.round((288 * WORLD.height) / WORLD.width),
                    pixelRatio: 1,
                    fontEmbedCSS,
                    backgroundColor: background.backgroundColor,
                    style: {
                        ["--page-enter-animation" as string]: "none",
                        transform: "none",
                        transformOrigin: "0 0",
                        transition: "none",
                        willChange: "auto",
                        backgroundImage: background.backgroundImage,
                        backgroundSize: `${CANVAS_RULES.gridSize}px ${CANVAS_RULES.gridSize}px`,
                        backgroundPosition: "0 0",
                    },
                });
                if (disposed || current !== generation.current) return;
                const nextImage = canvas.toDataURL("image/png");
                if (cache.size >= 8) cache.delete(cache.keys().next().value!);
                cache.set(key, nextImage);
                setSnapshot({ owner: cache, image: nextImage });
                setFailed(false);
            } catch {
                if (!disposed && current === generation.current) setFailed(true);
            } finally {
                if (!disposed && current === generation.current) setLoading(false);
            }
        };
        const schedule = () => {
            const current = ++generation.current;
            if (timer !== undefined) clearTimeout(timer);
            const theme = document.documentElement.dataset.theme ?? "system";
            const scheme = window.matchMedia("(prefers-color-scheme: dark)").matches;
            const key = JSON.stringify([contentVersion, WORLD.width, WORLD.height, theme, scheme]);
            const cached = cache.get(key);
            if (cached && retry === 0) {
                setSnapshot({ owner: cache, image: cached });
                setLoading(false);
                setFailed(false);
                return;
            }
            setLoading(true);
            timer = window.setTimeout(() => {
                // Stale queued scenes exit before cloning. Never clone two DOM trees at once.
                captureQueue = captureQueue
                    .then(() => capture(key, current))
                    .catch(() => undefined);
            }, 180);
        };
        const appearance = new MutationObserver(schedule);
        appearance.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ["data-theme"],
        });
        const scheme = window.matchMedia("(prefers-color-scheme: dark)");
        scheme.addEventListener("change", schedule);
        schedule();
        void document.fonts?.ready.then(() => {
            if (!disposed) schedule();
        });
        return () => {
            disposed = true;
            generation.current++;
            if (timer !== undefined) clearTimeout(timer);
            appearance.disconnect();
            scheme.removeEventListener("change", schedule);
        };
    }, [worldRef, surface, contentVersion, retry, cache]);
    return { image, failed, loading, refresh };
}

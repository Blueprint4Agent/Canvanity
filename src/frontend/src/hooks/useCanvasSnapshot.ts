import { useCallback, useEffect, useRef, useState, type RefObject } from "react";
import { CANVAS_RULES, type CanvasSurface } from "../canvas/canvasRules";

/** Scene snapshots refresh on content/appearance changes, never on camera movement. */
export function useCanvasSnapshot(
    worldRef: RefObject<HTMLDivElement>,
    surface: CanvasSurface,
    contentVersion: string,
) {
    const WORLD = surface.bounds;
    const [image, setImage] = useState<string | null>(null);
    const [failed, setFailed] = useState(false);
    const [loading, setLoading] = useState(true);
    const [retry, setRetry] = useState(0);
    const generation = useRef(0);
    const refresh = useCallback(() => setRetry((value) => value + 1), []);
    useEffect(() => {
        let disposed = false;
        let timer: number | undefined;
        const capture = async () => {
            const node = worldRef.current;
            if (!node || disposed) return;
            const current = ++generation.current;
            setLoading(true);
            try {
                await Promise.all(
                    Array.from(node.querySelectorAll("img")).map((img) =>
                        img.decode().catch(() => undefined),
                    ),
                );
                await document.fonts.ready;
                const { toCanvas } = await import("html-to-image");
                if (disposed || current !== generation.current) return;
                const background = getComputedStyle(node.parentElement!);
                const canvas = await toCanvas(node, {
                    width: WORLD.width,
                    height: WORLD.height,
                    canvasWidth: 288,
                    canvasHeight: Math.round((288 * WORLD.height) / WORLD.width),
                    pixelRatio: 1,
                    skipFonts: false,
                    backgroundColor: background.backgroundColor,
                    style: {
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
                setImage(canvas.toDataURL("image/png"));
                setFailed(false);
            } catch {
                if (!disposed && current === generation.current) setFailed(true);
            } finally {
                if (!disposed && current === generation.current) setLoading(false);
            }
        };
        const schedule = () => {
            if (timer !== undefined) clearTimeout(timer);
            timer = window.setTimeout(() => {
                void capture();
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
    }, [worldRef, surface, contentVersion, retry]);
    return { image, failed, loading, refresh };
}

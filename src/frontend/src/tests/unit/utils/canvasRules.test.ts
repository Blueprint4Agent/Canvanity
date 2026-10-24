import { describe, expect, it } from "vitest";
import {
    canvasAction,
    clampZoom,
    constrainCamera,
    validateSurface,
} from "../../../canvas/canvasRules";
describe("finite shared canvas contract", () => {
    it.each(["ui", "document"] as const)("bounds %s at every camera entry point", (kind) => {
        const surface = validateSurface({ kind, bounds: { width: 1440, height: 1000 } });
        expect(
            constrainCamera({ x: 100000, y: -100000, zoom: 1 }, surface, {
                width: 800,
                height: 600,
            }),
        ).toEqual({ x: 0, y: -400, zoom: 1 });
        expect(
            constrainCamera({ x: 999, y: -999, zoom: 0.25 }, surface, { width: 800, height: 600 }),
        ).toEqual({ x: 220, y: 175, zoom: 0.25 });
    });
    it("rejects unbounded surfaces and clamps both zoom limits", () => {
        expect(() =>
            validateSurface({ kind: "document", bounds: { width: Infinity, height: 100 } }),
        ).toThrow();
        expect(clampZoom(-99)).toBe(0.25);
        expect(clampZoom(99)).toBe(2);
        expect(clampZoom(NaN)).toBe(1);
    });
    it("reserves zoom chords for the canvas and excludes other browser chords and IME", () => {
        const base = {
            key: "+",
            ctrlKey: false,
            metaKey: false,
            altKey: false,
            isComposing: false,
        };
        expect(canvasAction(base)).toBe("zoomIn");
        for (const key of ["altKey", "isComposing"])
            expect(canvasAction({ ...base, [key]: true })).toBeNull();
        expect(canvasAction({ ...base, ctrlKey: true })).toBe("zoomIn");
        expect(canvasAction({ ...base, metaKey: true, key: "-" })).toBe("zoomOut");
        expect(canvasAction({ ...base, ctrlKey: true, key: "h" })).toBeNull();
        expect(canvasAction({ ...base, key: "H" })).toBeNull();
    });
});

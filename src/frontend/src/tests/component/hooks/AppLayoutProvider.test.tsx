import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AppLayoutProvider, useAppLayout } from "../../../hooks/useAppLayout";
import { serviceConfig, type AppLayoutMode } from "../../../service.config";
function Probe() {
    const layout = useAppLayout();
    return (
        <>
            <output>{layout.mode}</output>
            <input aria-label="Draft" />
            <button disabled={!layout.canPreview} onClick={() => layout.setMode("sidebar")}>
                Preview
            </button>
        </>
    );
}
describe("Canvanity minimal shell", () => {
    it.each(["sidebar", "topnav", "focused"] as AppLayoutMode[])(
        "normalizes legacy %s configuration and stored previews",
        (legacy) => {
            serviceConfig.layout = legacy;
            localStorage.setItem("blueprint_layout_preview", legacy);
            const { rerender } = render(
                <AppLayoutProvider>
                    <Probe />
                </AppLayoutProvider>,
            );
            expect(screen.getByRole("status")).toHaveTextContent("focused");
            expect(screen.getByRole("button")).toBeDisabled();
            fireEvent.change(screen.getByRole("textbox"), { target: { value: "unsaved" } });
            rerender(
                <AppLayoutProvider>
                    <Probe />
                </AppLayoutProvider>,
            );
            expect(screen.getByRole("textbox")).toHaveValue("unsaved");
            serviceConfig.layout = "focused";
        },
    );
});

import { describe, expect, it } from "vitest";
import { resolveLoginReturnPath } from "../../../utils/authReturnPath";

describe("login return destination", () => {
    it.each(["/profile", "/my-canvas", "/board", "/b/agent-lab"])(
        "preserves supported route %s",
        (path) => {
            expect(resolveLoginReturnPath(path)).toBe(path);
        },
    );
    it.each([
        null,
        "",
        "https://example.com",
        "//example.com",
        "/b/../../admin",
        "/b/agent?next=//example.com",
        "/b/%2fexample.com",
        "/admin",
    ])("rejects unsupported destination %s", (path) => {
        expect(resolveLoginReturnPath(path)).toBe("/home");
    });
});

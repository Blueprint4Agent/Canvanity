/** Login destinations are known internal routes, never arbitrary redirects. */
export function resolveLoginReturnPath(value: string | null): string {
    if (!value) return "/home";
    return ["/profile", "/my-canvas", "/board"].includes(value) ||
        /^\/b\/[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value)
        ? value
        : "/home";
}

export type ButtonAppearance =
    | "default"
    | "pill"
    | "pill-secondary"
    | "text"
    | "canvas"
    | "canvas-card";

export function buttonClassName(
    appearance: ButtonAppearance,
    iconOnly = false,
    className?: string,
): string {
    return `ui-button${iconOnly ? " ui-button--icon" : ""}${appearance !== "default" ? ` ui-button--${appearance}` : ""}${className ? ` ${className}` : ""}`;
}

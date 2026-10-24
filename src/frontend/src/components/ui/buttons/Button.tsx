import type { ButtonHTMLAttributes, ReactNode } from "react";
import { buttonClassName, type ButtonAppearance } from "../../../utils/buttonStyles";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
    children: ReactNode;
    loading?: boolean;
    iconOnly?: boolean;
    appearance?: ButtonAppearance;
};

export function Button({
    children,
    className,
    type = "button",
    loading = false,
    appearance = "default",
    iconOnly = false,
    disabled,
    ...props
}: ButtonProps) {
    const nextClassName = buttonClassName(appearance, iconOnly, className);
    const isDisabled = Boolean(disabled || loading);

    return (
        <button type={type} className={nextClassName} disabled={isDisabled} {...props}>
            <span className="ui-button__content">
                {loading ? <span className="ui-button__spinner" aria-hidden="true" /> : null}
                <span className="ui-button__label">{children}</span>
            </span>
        </button>
    );
}

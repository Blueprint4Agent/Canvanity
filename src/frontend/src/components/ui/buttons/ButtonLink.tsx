import { Link, type LinkProps } from "react-router-dom";
import { buttonClassName, type ButtonAppearance } from "../../../utils/buttonStyles";

type ButtonLinkProps = LinkProps & { appearance?: ButtonAppearance };

/** Navigation keeps anchor semantics while sharing the button's visual variants. */
export function ButtonLink({
    appearance = "default",
    className,
    children,
    ...props
}: ButtonLinkProps) {
    return (
        <Link className={buttonClassName(appearance, false, className)} {...props}>
            <span className="ui-button__content">
                <span className="ui-button__label">{children}</span>
            </span>
        </Link>
    );
}

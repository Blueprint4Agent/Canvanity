import { useId, useState } from "react";
import { ChevronDown } from "lucide-react";
import { Button } from "../ui";
import { useAppNavigation } from "../../hooks/useAppNavigation";
import { NavLink, useLocation } from "react-router-dom";

export function SectionNavigation() {
    const { items, label, hasSections, isSettings, isAdminPanel, isSectionActive } =
        useAppNavigation();
    const location = useLocation();
    const id = useId();
    const path = location.pathname + location.search;
    const [openPath, setOpenPath] = useState<string | null>(null);
    const open = openPath === path;
    if (!hasSections) return null;
    return (
        <aside className={`section-navigation${open ? " section-navigation--open" : ""}`}>
            <div className="section-navigation__editorial" aria-hidden="true">
                <img
                    src={isSettings ? "/images/explore/build.webp" : "/images/explore/agent.webp"}
                    alt=""
                    width="720"
                    height="400"
                />
                <span>{isSettings ? "Settings" : "Admin"}</span>
            </div>
            <h2 className="section-navigation__title">{label}</h2>
            <Button
                className="section-navigation__toggle"
                appearance="text"
                aria-expanded={open}
                aria-controls={id}
                onClick={() => setOpenPath(open ? null : path)}
            >
                {label}
                <ChevronDown aria-hidden="true" />
            </Button>
            <nav id={id} aria-label={label}>
                {items.map(({ path, label, icon: Icon, section }) => (
                    <NavLink
                        key={path}
                        to={path}
                        end={isAdminPanel}
                        aria-current={
                            isSettings ? (isSectionActive(section) ? "page" : false) : undefined
                        }
                        className={({ isActive }) =>
                            `section-navigation__item ui-action ui-action--pencil${(isSettings ? isSectionActive(section) : isActive) ? " section-navigation__item--active" : ""}`
                        }
                    >
                        <Icon aria-hidden="true" />
                        <span>{label}</span>
                    </NavLink>
                ))}
            </nav>
        </aside>
    );
}

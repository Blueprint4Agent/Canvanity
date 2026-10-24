import { useCallback, type ReactNode } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuthContext } from "../../hooks/useAuth";
import { useAppNavigation } from "../../hooks/useAppNavigation";
import { useAppShortcuts } from "../../hooks/useAppShortcuts";
import { profileSidebarPath } from "../../utils/profileNavigation";
import type { SubscriptionTier } from "../../utils/billingPlans";
import { SectionNavigation } from "./SectionNavigation";
import { MinimalHeader } from "./MinimalHeader";

type AppLayoutProps = {
    children: ReactNode;
    subscriptionTier?: SubscriptionTier | null;
    inboxUnread?: number | null;
};
export function AppLayout({ children, subscriptionTier, inboxUnread }: AppLayoutProps) {
    const { hasSections } = useAppNavigation();
    const navigate = useNavigate();
    const location = useLocation();
    const { user } = useAuthContext();
    // Preserve the existing account shortcut contract without a sidebar.
    const toggleSidebar = useCallback(
        () => document.querySelector<HTMLButtonElement>(".profile-menu__trigger")?.click(),
        [],
    );
    const openSettings = useCallback(() => navigate("/settings"), [navigate]);
    const openProfile = useCallback(
        () => navigate("/profile", { state: { profileSidebarPath: profileSidebarPath(location) } }),
        [navigate, location],
    );
    useAppShortcuts({ toggleSidebar, openSettings, openProfile: user ? openProfile : undefined });
    return (
        <div
            data-layout="focused"
            className="app-shell app-shell--focused app-shell--minimal app-shell--settings"
        >
            <MinimalHeader subscriptionTier={subscriptionTier} inboxUnread={inboxUnread} />
            <main className={`app-main${hasSections ? " app-main--workspace" : ""}`}>
                <div className={`app-main__content${hasSections ? " app-workspace" : ""}`}>
                    {hasSections ? <SectionNavigation /> : null}
                    <div className="app-page-content">{children}</div>
                </div>
            </main>
        </div>
    );
}

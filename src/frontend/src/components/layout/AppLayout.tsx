import { useCommunityReturnPath } from "../../hooks/useCommunityReturnPath";
import { useCallback, useLayoutEffect, useRef, type ReactNode } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuthContext } from "../../hooks/useAuth";
import { useAppNavigation } from "../../hooks/useAppNavigation";
import { useAppShortcuts } from "../../hooks/useAppShortcuts";
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
    const communityReturnPath = useCommunityReturnPath();
    const navigate = useNavigate();
    const location = useLocation();
    const contentRef = useRef<HTMLDivElement>(null);
    useLayoutEffect(() => {
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
        const root = contentRef.current;
        if (!root) return;
        // Animate content only. Keep camera transforms and persistent controls untouched.
        const scene = root.querySelector<HTMLElement>(
            ".explore-content, .community-canvas__content",
        );
        if (["/home", "/my-canvas", "/board"].includes(location.pathname) && !scene) return;
        const content = scene ?? root;
        const animation = content.animate?.(
            [
                { opacity: 0, translate: "0 7px" },
                { opacity: 1, translate: "0 0" },
            ],
            { duration: 220, easing: "cubic-bezier(0.2, 0.7, 0.3, 1)" },
        );
        return () => animation?.cancel();
    }, [location.pathname, location.search]);
    const { user } = useAuthContext();
    const openSettings = useCallback(() => navigate("/settings"), [navigate]);
    const openProfile = useCallback(() => navigate("/profile"), [navigate]);
    useAppShortcuts({ openSettings, openProfile: user ? openProfile : undefined });
    return (
        <div
            data-layout="focused"
            className="app-shell app-shell--focused app-shell--minimal app-shell--settings"
        >
            <MinimalHeader
                subscriptionTier={subscriptionTier}
                inboxUnread={inboxUnread}
                showCommunityNavigation={!hasSections}
                communityReturnPath={communityReturnPath}
            />
            <main className={`app-main${hasSections ? " app-main--workspace" : ""}`}>
                <div className={`app-main__content${hasSections ? " app-workspace" : ""}`}>
                    {hasSections ? <SectionNavigation /> : null}
                    <div ref={contentRef} className="app-page-content">
                        {children}
                    </div>
                </div>
            </main>
        </div>
    );
}

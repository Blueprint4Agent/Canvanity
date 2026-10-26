import { useState } from "react";
import { BookOpen, Coffee, Compass, Palette, PanelsTopLeft } from "lucide-react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuthContext } from "../../hooks/useAuth";
import { useAppConfig } from "../../hooks/useFeatures";
import { useToast } from "../../hooks/useToast";
import { useServerConnectivity } from "../../hooks/connectivity/useServerConnectivity";
import { getCoffeeSupportUrl } from "../../utils/coffeeSupport";
import type { SubscriptionTier } from "../../utils/billingPlans";
import { BrandBanner, Tooltip } from "../ui";
import { ProfileDropdown } from "./ProfileDropdown";
import { ConnectivityStatus } from "./ConnectivityStatus";

type MinimalHeaderProps = {
    showCommunityNavigation?: boolean;
    communityReturnPath?: string;
    subscriptionTier?: SubscriptionTier | null;
    inboxUnread?: number | null;
};
export function MinimalHeader({
    subscriptionTier,
    inboxUnread,
    showCommunityNavigation = true,
    communityReturnPath = "/home",
}: MinimalHeaderProps) {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const { user, profileImageUrl, logout } = useAuthContext();
    const { data } = useAppConfig();
    const { isDesktop, status } = useServerConnectivity();
    const toast = useToast();
    const [busy, setBusy] = useState(false);
    const coffeeUrl = getCoffeeSupportUrl(
        data?.app_mode,
        import.meta.env.VITE_BUY_ME_A_COFFEE_ENABLED,
        import.meta.env.VITE_BUY_ME_A_COFFEE_URL,
    );
    const resources =
        data?.app_mode === "development"
            ? [
                  {
                      href: "https://github.com/Blueprint4Agent/B4FastAPI",
                      label: t("nav.sidebar.github"),
                      icon: null,
                  },
                  {
                      href: "https://blueprint4agent.github.io/docs",
                      label: t("nav.sidebar.documentation"),
                      icon: BookOpen,
                  },
                  ...(coffeeUrl
                      ? [{ href: coffeeUrl, label: "Buy Me a Coffee", icon: Coffee }]
                      : []),
              ]
            : [];
    const blocked = isDesktop && status !== "online";
    return (
        <header className="app-header app-header--minimal" aria-label={t("nav.brand")}>
            <Link
                to={communityReturnPath}
                className="minimal-header__brand"
                aria-label={t("community.backToSpace")}
            >
                <BrandBanner />
            </Link>
            {showCommunityNavigation ? (
                <nav className="community-navigation" aria-label={t("community.navigation")}>
                    <NavLink to="/home">
                        <Compass size={16} aria-hidden="true" /> Plaza
                    </NavLink>
                    <NavLink to={user ? "/my-canvas" : "/login?next=%2Fmy-canvas"}>
                        <Palette size={16} aria-hidden="true" /> My Canvas
                    </NavLink>
                    <NavLink to="/board">
                        <PanelsTopLeft size={16} aria-hidden="true" /> Board
                    </NavLink>
                </nav>
            ) : null}
            <div className="minimal-header__actions">
                <ConnectivityStatus placement="navbar" />
                {resources.map(({ href, label, icon: Icon }) => (
                    <Tooltip key={href} content={label} side="bottom">
                        <a
                            href={href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="minimal-header__resource ui-action"
                            aria-label={label}
                        >
                            {Icon ? (
                                <Icon size={19} aria-hidden="true" />
                            ) : (
                                <span className="app-sidebar__github-mark" aria-hidden="true" />
                            )}
                        </a>
                    </Tooltip>
                ))}
                <span className="minimal-header__divider" />
                <ProfileDropdown
                    tooltipSide="bottom"
                    subscriptionTier={subscriptionTier}
                    showPlans={Boolean(data?.billing_enabled)}
                    showLogin={!user && Boolean(data?.login_enabled)}
                    showAdmin={user?.role === "admin" || user?.role === "manager"}
                    showDevelopmentLinks={data?.app_mode === "development"}
                    showAdminDemo={Boolean(data?.demo_enabled) && user?.role !== "admin"}
                    inboxUnread={inboxUnread}
                    allowAccountSwitching={Boolean(data?.login_enabled && user)}
                    avatarLabel={user?.name?.slice(0, 1) ?? "C"}
                    avatarImageUrl={profileImageUrl}
                    busy={busy}
                    displayName={user?.name ?? t("profile.guestName")}
                    email={user?.email}
                    showLogout={Boolean(user && data?.login_enabled)}
                    logoutDisabled={blocked}
                    logoutDisabledTitle={t("nav.logoutUnavailable")}
                    onLogout={() => {
                        if (blocked) return;
                        setBusy(true);
                        void logout()
                            .then(() => {
                                toast(t("toast.logoutSuccess"));
                                navigate("/home", { replace: true });
                            })
                            .catch(() => toast(t("toast.logoutError")))
                            .finally(() => setBusy(false));
                    }}
                />
            </div>
        </header>
    );
}

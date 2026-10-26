import { useInterestCatalog } from "../../hooks/api/interests/useInterestCatalog";
import { ProfileInterestTags } from "../../components/features/profile/ProfileInterestsField";
import { Mail, ArrowUpRight } from "lucide-react";
import { Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { CommunityCanvas } from "../../components/features/explore/CommunityCanvas";
import { UserAvatar, ButtonLink } from "../../components/ui";
import { useAuthContext } from "../../hooks/useAuth";
import { LoadingPage } from "../main/LoadingPage";

export function MyCanvasPage() {
    const { t, i18n } = useTranslation();
    const catalog = useInterestCatalog();
    const { user, loading, profileImageUrl } = useAuthContext();
    if (loading) return <LoadingPage />;
    if (!user) return <Navigate to="/login?next=%2Fmy-canvas" replace />;
    return (
        <CommunityCanvas
            label="My Canvas"
            contentVersion={JSON.stringify([
                "my-canvas",
                i18n.resolvedLanguage,
                user.id,
                user.name,
                user.email,
                user.bio,
                user.handle,
                user.interests,
                catalog.items,
                profileImageUrl,
            ])}
        >
            <header className="community-heading">
                <h1>My Canvas</h1>
                <p className="explore-intro__tagline">{t("community.mySubtitle")}</p>
            </header>
            <section className="my-canvas-identity" aria-label={t("community.identity")}>
                <UserAvatar imageUrl={profileImageUrl} label={user.name} />
                <div className="my-canvas-identity__text">
                    <p className="community-heading__eyebrow">Hello, this is me</p>
                    <h2>{user.name}</h2>
                    {user.handle ? (
                        <p className="my-canvas-identity__handle">@{user.handle}</p>
                    ) : null}
                    <p>{user.bio || t("settings.profile.emptyBio")}</p>
                    <a className="my-canvas-identity__email" href={`mailto:${user.email}`}>
                        <Mail size={18} aria-hidden="true" />
                        {user.email}
                    </a>
                    <div className="profile-interests">
                        <ProfileInterestTags
                            interests={user.interests ?? []}
                            catalog={catalog.items}
                        />
                    </div>
                </div>
                <ButtonLink to="/profile" appearance="canvas" className="my-canvas-identity__edit">
                    {t("settings.profile.edit")}
                    <ArrowUpRight size={16} aria-hidden="true" />
                </ButtonLink>
            </section>
        </CommunityCanvas>
    );
}

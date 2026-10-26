import { ArrowUpRight } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { CommunityCanvas } from "../../components/features/explore/CommunityCanvas";
import { EXPLORE_TOPICS } from "../../components/features/explore/exploreTopics";

export function BoardPage() {
    const { t, i18n } = useTranslation();
    return (
        <CommunityCanvas label="Board" contentVersion={`board:${i18n.resolvedLanguage}`}>
            <header className="community-heading">
                <h1>Board</h1>
                <p className="explore-intro__tagline">{t("community.boardSubtitle")}</p>
            </header>
            <div className="community-boards">
                {EXPLORE_TOPICS.map((topic) => (
                    <Link
                        key={topic.id}
                        to={`/home?topic=${topic.id}`}
                        className={`community-board community-board--${topic.id}`}
                    >
                        <img src={`/images/explore/${topic.id}.webp`} alt="" draggable={false} />
                        <div className="community-board__caption">
                            <h2>{t(`explore.topics.${topic.id}.label`)}</h2>
                            <p>{t(`explore.topics.${topic.id}.description`)}</p>
                            <span>
                                {t("community.visit")} <ArrowUpRight size={18} aria-hidden="true" />
                            </span>
                        </div>
                    </Link>
                ))}
            </div>
            <p className="community-example">{t("community.example")}</p>
        </CommunityCanvas>
    );
}

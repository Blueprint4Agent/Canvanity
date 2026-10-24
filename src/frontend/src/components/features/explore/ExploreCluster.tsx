import { memo } from "react";
import { UserRound, Heart, MessageSquare } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "../../ui";
import type { ExploreTopic, ExploreTopicId } from "./exploreTopics";
type ExploreClusterProps = {
    topic: ExploreTopic;
    active: boolean;
    onSelect: (id: ExploreTopicId) => void;
};
export const ExploreCluster = memo(function ExploreCluster({
    topic,
    active,
    onSelect,
}: ExploreClusterProps) {
    const { t, i18n } = useTranslation();
    return (
        <section
            className={`explore-cluster explore-cluster--${topic.id}`}
            data-active={active}
            aria-label={t(`explore.topics.${topic.id}.label`)}
        >
            <header className="explore-feed-heading">
                <h2>{t(`explore.topics.${topic.id}.label`)}</h2>
                <p className="explore-topic__handwriting">
                    {t(`explore.topics.${topic.id}.handwriting`)}
                </p>
            </header>
            <div className="explore-posts">
                {topic.posts.map((post, index) => (
                    <Button
                        key={post.id}
                        appearance="text"
                        className={`explore-topic explore-topic--${index + 1}`}
                        onClick={() => onSelect(topic.id)}
                        aria-label={t("explore.openSample", {
                            title: t(`explore.posts.${post.id}`),
                            name: t(`explore.authors.${post.author}`),
                        })}
                    >
                        <img
                            className="explore-topic__image"
                            src={`/images/explore/${post.image}.webp`}
                            width="720"
                            height="400"
                            alt=""
                            draggable={false}
                        />
                        <span className="explore-post-meta">
                            <span className="explore-post-author">
                                <UserRound size={20} aria-hidden="true" />
                                {t(`explore.authors.${post.author}`)}
                            </span>
                            {post.comments !== undefined ? (
                                <span
                                    aria-label={t("explore.commentCount", { count: post.comments })}
                                >
                                    <MessageSquare size={20} aria-hidden="true" />
                                    {post.comments.toLocaleString(i18n.resolvedLanguage)}
                                </span>
                            ) : null}
                            <span aria-label={t("explore.likeCount", { count: post.likes })}>
                                <Heart size={22} aria-hidden="true" />
                                {post.likes.toLocaleString(i18n.resolvedLanguage)}
                            </span>
                        </span>
                    </Button>
                ))}
            </div>
        </section>
    );
});

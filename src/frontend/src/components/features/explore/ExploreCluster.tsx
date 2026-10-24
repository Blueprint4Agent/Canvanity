import { memo } from "react";
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
    const { t } = useTranslation();
    return (
        <section
            className={`explore-cluster explore-cluster--${topic.id}`}
            data-active={active}
            aria-label={t(`explore.topics.${topic.id}.label`)}
        >
            <Button
                appearance="text"
                className="explore-topic"
                aria-pressed={active}
                onClick={() => onSelect(topic.id)}
            >
                <img
                    className="explore-topic__image"
                    src={`/images/explore/${topic.id}.webp`}
                    width="640"
                    height="400"
                    alt=""
                    draggable={false}
                />
                <span className="explore-topic__title">
                    {t(`explore.topics.${topic.id}.label`)}
                </span>
                <span className="explore-topic__handwriting">
                    {t(`explore.topics.${topic.id}.handwriting`)}
                </span>
            </Button>
        </section>
    );
});

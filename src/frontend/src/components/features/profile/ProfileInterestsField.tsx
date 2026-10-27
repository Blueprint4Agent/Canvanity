import { useId, useState } from "react";
import { Check, Plus, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button, InputField, InlineMessage, Spinner } from "../../ui";
import { interestLabel, type InterestItem } from "../../../utils/profileInterests";

type Catalog = { items: InterestItem[]; loading: boolean; error: boolean; reload: () => void };
type TagsProps = {
    interests: readonly string[];
    catalog: InterestItem[];
    onRemove?: (interest: string) => void;
    busy?: boolean;
};
export function ProfileInterestTags({ interests, catalog, onRemove, busy }: TagsProps) {
    const { t, i18n } = useTranslation();
    return (
        <>
            {interests.map((interest) => {
                const label = interestLabel(interest, catalog, i18n.resolvedLanguage ?? "ko");
                return (
                    <span className="profile-interest-tag" key={interest}>
                        <span>{label}</span>
                        {onRemove ? (
                            <Button
                                appearance="canvas"
                                iconOnly
                                className="profile-interest-tag__remove"
                                disabled={busy}
                                onClick={() => onRemove(interest)}
                                aria-label={t("settings.profile.removeInterest", {
                                    interest: label,
                                })}
                            >
                                <X size={13} aria-hidden="true" />
                            </Button>
                        ) : null}
                    </span>
                );
            })}
        </>
    );
}

type Props = {
    interests: string[];
    onChange: (interests: string[]) => void;
    busy: boolean;
    catalog: Catalog;
    maxSelections?: number;
    selectionHelp?: string;
};
export function ProfileInterestsField({
    interests,
    onChange,
    busy,
    catalog,
    maxSelections = 8,
    selectionHelp,
}: Props) {
    const { t, i18n } = useTranslation();
    const [query, setQuery] = useState("");
    const id = useId();
    const search = query.trim().toLocaleLowerCase();
    const matches = catalog.items.filter((item) =>
        [item.id, item.name_ko, item.name_en, ...(item.aliases ?? [])].some((value) =>
            value.toLocaleLowerCase().includes(search),
        ),
    );
    const full = interests.length >= maxSelections;
    return (
        <section className="profile-interest-picker" aria-labelledby={id}>
            <div className="profile-interest-picker__heading">
                <h3 id={id}>{t("settings.profile.interests")}</h3>
                <span>
                    {interests.length}/{maxSelections}
                </span>
            </div>
            <div className="profile-interests profile-interest-picker__selected">
                <ProfileInterestTags
                    interests={interests}
                    catalog={catalog.items}
                    busy={busy}
                    onRemove={(value) => onChange(interests.filter((item) => item !== value))}
                />
            </div>
            <InputField
                type="search"
                label={t("settings.profile.searchInterests")}
                placeholder={t("settings.profile.searchInterestsPlaceholder")}
                value={query}
                onValueChange={setQuery}
                maxLength={80}
                disabled={busy || catalog.loading || catalog.error}
                onKeyDown={(event) => {
                    if (event.key === "Enter") event.preventDefault();
                }}
            />
            {catalog.loading ? (
                <Spinner size="sm" label={t("settings.profile.interestCatalogLoading")} />
            ) : catalog.error ? (
                <div>
                    <InlineMessage tone="error">
                        {t("settings.profile.interestCatalogError")}
                    </InlineMessage>
                    <Button appearance="canvas" onClick={catalog.reload}>
                        {t("settings.profile.interestRetry")}
                    </Button>
                </div>
            ) : (
                <div
                    className="profile-interest-picker__results"
                    role="group"
                    aria-label={t("settings.profile.interestSuggestions")}
                >
                    {matches.map((item) => (
                        <Button
                            key={item.id}
                            appearance="canvas"
                            disabled={busy || (full && !interests.includes(item.id))}
                            aria-pressed={interests.includes(item.id)}
                            onClick={() =>
                                onChange(
                                    interests.includes(item.id)
                                        ? interests.filter((value) => value !== item.id)
                                        : [...interests, item.id],
                                )
                            }
                        >
                            {interests.includes(item.id) ? (
                                <Check size={14} aria-hidden="true" />
                            ) : (
                                <Plus size={14} aria-hidden="true" />
                            )}
                            {interestLabel(item.id, catalog.items, i18n.resolvedLanguage ?? "ko")}
                        </Button>
                    ))}
                    {!matches.length ? (
                        <p className="muted">{t("settings.profile.noInterestResults")}</p>
                    ) : null}
                </div>
            )}
            <p className="muted">
                {selectionHelp ??
                    t(
                        full
                            ? "settings.profile.interestsFull"
                            : "settings.profile.interestsPickerHelp",
                    )}
            </p>
        </section>
    );
}

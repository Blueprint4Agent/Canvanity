import { useTranslation } from "react-i18next";
import { ChevronRight } from "lucide-react";
import type { CurrentPlan } from "../../../hooks/api/billing/useCurrentPlan";
import { Button, InlineMessage } from "../../ui";

export function CurrentPlanRow({ plan, onOpen }: { plan: CurrentPlan; onOpen: () => void }) {
    const { t } = useTranslation();
    return (
        <article className="settings-row">
            <div>
                <h2>{t("settings.account.currentPlan")}</h2>
                <p className="muted">{plan.label}</p>
                {plan.error ? <InlineMessage tone="error">{plan.error}</InlineMessage> : null}
            </div>
            {plan.error ? (
                <Button appearance="canvas" onClick={plan.reload}>
                    {t("settings.profile.retry")}
                </Button>
            ) : plan.enabled ? (
                <Button
                    appearance="canvas"
                    iconOnly
                    onClick={onOpen}
                    aria-label={t("settings.account.managePlan")}
                    title={t("settings.account.managePlan")}
                >
                    <ChevronRight aria-hidden="true" />
                </Button>
            ) : null}
        </article>
    );
}

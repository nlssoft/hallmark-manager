import { useNavigate } from "react-router-dom";
import type {
    DashboardSection,
    DashboardCardProp,
} from "../types/frontedTypes/dashboard";
import useRouting from "../hooks/useRouting";

const colorMap = {
    emerald: {
        bg: "bg-emerald-100",
        text: "text-emerald-700",
    },
    amber: {
        bg: "bg-amber-100",
        text: "text-amber-700",
    },
    indigo: {
        bg: "bg-indigo-100",
        text: "text-indigo-700",
    },
    sky: {
        bg: "bg-sky-100",
        text: "text-sky-700",
    },
    red: {
        bg: "bg-orange-100",
        text: "text-orange-700",
    },
    violet: {
        bg: "bg-violet-100",
        text: "text-violet-700",
    },
    rose: {
        bg: "bg-rose-100",
        text: "text-rose-700",
    },
    slate: {
        bg: "bg-slate-100",
        text: "text-slate-700",
    },
} as const;

function DashboardCard({ isParent, sections }: DashboardCardProp) {
    const nav = useRouting();

    let visibleSections = sections.filter((section) => !section.disabled);

    if (isParent) {
        visibleSections = visibleSections.filter(
            (section) =>
                section.allowed === "parent" || section.allowed === "both"
        );
    } else {
        visibleSections = visibleSections.filter(
            (section) =>
                section.allowed === "employee" || section.allowed === "both"
        );
    }

    return (
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {visibleSections.map((s) => {
                const Icon = s.icon;
                const color = colorMap[s.color];

                return (
                    <button
                        key={s.id}
                        onClick={() => nav.go(s.route)}
                        className="m-3 flex min-h-60 cursor-pointer flex-col items-start gap-5 rounded-2xl border border-transparent bg-white px-8 py-12 text-left shadow-lg transition-all duration-300 ease-out hover:translate-y-2 hover:border-amber-200 hover:shadow-xl"
                    >
                        <div
                            className={`flex h-12 w-12 items-center justify-center rounded-xl ${color.bg}`}
                        >
                            <Icon className={`h-6 w-6 ${color.text}`} />
                        </div>

                        <h2 className="text-2xl font-semibold text-stone-900">
                            {s.title}
                        </h2>

                        <p className="leading-relaxed text-stone-600">
                            {s.description}
                        </p>
                    </button>
                );
            })}
        </div>
    );
}

export default DashboardCard;

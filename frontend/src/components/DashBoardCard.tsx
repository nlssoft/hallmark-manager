import { useNavigate } from "react-router-dom";
import type { DashboardSection, DashboardCardProp } from "../types/dashboard";

function DashboardCard({ isParent, sections }: DashboardCardProp) {
  const navigate = useNavigate();

  function handleRouting(section: DashboardSection) {
    navigate(section.route);
  }

  let visibleSections = sections.filter((section) => !section.disabled);

  if (isParent) {
    visibleSections = visibleSections.filter(
      (section) => section.allowed === "parent" || section.allowed === "both",
    );
  } else {
    visibleSections = visibleSections.filter(
      (section) => section.allowed === "employee" || section.allowed === "both",
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
      {visibleSections.map((s) => (
        <button
          key={s.id}
          onClick={() => handleRouting(s)}
          className="flex flex-col items-start text-left h-60
          bg-white gap-5 border-stone-200 px-6 py-8
          rounded-2xl m-3 shadow-lg hover:shadow-xl
          hover:translate-y-2 cursor-pointer transition-all duration-300 ease-out "
        >
          <div className="text-stone-900 text-2xl font-semi-bold">{s.title}</div>
          <div className="text-stone-600 leading-relaxed">{s.description}</div>
        </button>
      ))}
    </div>
  );
}

export default DashboardCard;

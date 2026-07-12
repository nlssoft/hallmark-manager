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
    <div>
      {visibleSections.map((s) => (
        <button
          key={s.id}
          onClick={() => handleRouting(s)}
          className="flex gap-10 border-gray-200 px-10 py-10 rounded-2xl m-3 shadow-lg "
        >
          <div className="text-gray-900 text-3xl">{s.title}</div>
          <div className="text-gray-600 text-sm">{s.description}</div>
        </button>
      ))}
    </div>
  );
}

export default DashboardCard;

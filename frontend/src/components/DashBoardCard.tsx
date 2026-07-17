import { useNavigate } from "react-router-dom";
import type { DashboardSection, DashboardCardProp } from "../types/dashboard";


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
      {visibleSections.map((s) => {
        const Icon= s.icon
        const color = colorMap[s.color];


        return(<button
          key={s.id}
          onClick={() => handleRouting(s)}
          className="flex flex-col items-start text-left min-h-56
          bg-white gap-5 border border-transparent  px-8 py-8
          rounded-2xl m-3 shadow-lg hover:shadow-xl
          hover:translate-y-2 hover:border-amber-200
          cursor-pointer transition-all 
          duration-300 ease-out "
        >
         
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color.bg}`}>
            <Icon className={`w-6 h-6 ${color.text}`}/>
          </div>

          <h2 className="text-stone-900 text-2xl font-semibold">
              {s.title}
          </h2>

          <p className="text-stone-600 leading-relaxed">
            {s.description}
          </p>

        </button>)
})}
    </div>
  )
}

export default DashboardCard;

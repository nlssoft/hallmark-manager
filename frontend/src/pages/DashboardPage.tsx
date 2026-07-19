import DashboardCard from "../components/DashBoardCard";
import NavBar from "../components/NavBar";
import { useAuth } from "../hooks/useAuth";
import type { DashboardSection } from "../types/frontedTypes/dashboard";
import {
  Users,
  UserRound,
  LayersPlus,
  Wallet,
  ClipboardList,
  ChartColumn,
  HandCoins,
  EyeDashed,
} from "lucide-react";

const b = "both";
const p = "parent";


const dashboardSections: DashboardSection[] = [
  {
    id: "groups",
    title: "Groups",
    description:
      "Group customers together, assign service rates once, and apply them automatically when creating work entries.",
    route: "/groups",
    disabled: false,
    allowed: p,
    icon: Users,
    color: "indigo",
  },
  {
    id: "customers",
    title: "Customers",
    description:
      "Add, edit, and manage all your customer details in one place.",
    route: "/customers",
    disabled: false,
    allowed: b,
    icon: UserRound,
    color: "sky"

  },
  {
    id: "services",
    title: "Services",
    description:
      "Create and manage the services you offer, ready to use in every work entry.",
    route: "/services",
    disabled: false,
    allowed: p,
    icon: LayersPlus,
    color: "amber"
  },
  {
    id: "work-entries",
    title: "Work Entries",
    description:
      "Log work by selecting a customer and service, then enter quantity, discount, and other details.",
    route: "/work-entries",
    disabled: false,
    allowed: p,
    icon: ClipboardList,
    color: "red"
  },
  {
    id: "payments",
    title: "Payments",
    description:
      "Record customer payments and track exactly how much of each one remains and where it was used.",
    route: "/payments",
    disabled: false,
    allowed: p,
    icon: Wallet,
    color: "emerald"
  },
  {
    id: "audit-logs",
    title: "Audit Logs",
    description:
      "See a full history of every edit and deletion made to work entries and payments.",
    route: "/audit-logs",
    disabled: false,
    allowed: p,
    icon: EyeDashed,
    color: "violet"
  },
  {
    id: "requests",
    title: "Requests",
    description:
      "Employees request payment approval on their work entries, admins approve or reject them.",
    route: "/requests",
    disabled: false,
    allowed: b,
    icon: HandCoins,
    color: "rose"
  },
  {
    id: "summary",
    title: "Summary",
    description:
      "Get a clear read on your business total work, payments by customers, and much more.",
    route: "/summary",
    disabled: false,
    allowed: b,
    icon: ChartColumn,
    color: "slate"
  },
];

function DashboardPage() {
  const { isParent } = useAuth();

  return (
    <div className="min-h-screen bg-stone-50 ">
      <NavBar/>
      <main className="p-10 max-auto">
        <DashboardCard isParent={isParent} sections={dashboardSections} />
      </main>
    </div>
  );
}

export default DashboardPage;

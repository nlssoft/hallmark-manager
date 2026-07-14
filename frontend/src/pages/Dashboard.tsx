import DashboardCard from "../components/DashBoardCard";
import { useAuth } from "../hooks/useAuth";
import type { DashboardSection } from "../types/dashboard";
import {
  Users,
  UserRound,
  Wrench,
  Wallet,
  ClipboardList,
  ChartColumn,
  Bell,
  History,
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

  },
  {
    id: "services",
    title: "Services",
    description:
      "Create and manage the services you offer, ready to use in every work entry.",
    route: "/services",
    disabled: false,
    allowed: p,
    icon: Wrench,
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
  },
  {
    id: "audit-logs",
    title: "Audit Logs",
    description:
      "See a full history of every edit and deletion made to work entries and payments.",
    route: "/audit-logs",
    disabled: false,
    allowed: p,
    icon: History,
  },
  {
    id: "requests",
    title: "Requests",
    description:
      "Employees request payment approval on their work entries, admins approve or reject them.",
    route: "/requests",
    disabled: false,
    allowed: b,
    icon: Bell,
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
  },
];

function Dashboard() {
  const { isParent } = useAuth();

  return (
    <div className="min-h-screen bg-stone-50 ">
      <main className=" max-w-7xl p-10 max-auto ">
        <DashboardCard isParent={isParent} sections={dashboardSections} />;
      </main>
    </div>
  );
}

export default Dashboard;

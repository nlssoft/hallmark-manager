import type { LucideIcon } from "lucide-react";

export interface DashboardSection {
  id: string;
  title: string;
  description: string;
  route: string;
  disabled: boolean;
  allowed: string;
  icon: LucideIcon;
}

export interface DashboardCardProp {
  isParent: boolean;
  sections: DashboardSection[];
}

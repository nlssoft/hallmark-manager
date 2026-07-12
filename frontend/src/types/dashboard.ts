export interface DashboardSection {
  id: string;
  title: string;
  description: string;
  route: string;
  disabled: boolean;
  allowed: string;
}

export interface DashboardCardProp {
  isParent: boolean;
  sections: DashboardSection[];
}

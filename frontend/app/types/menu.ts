export interface menuItems {
  headTitle1?: string;
  headTitle2?: string;
  type?: string;
  title?: string;
  icon?: string;
  badgeType?: string;
  badgeValue?: string;
  active: boolean;
  path?: string;
  bookmark?: boolean;
  children?: menuItems[];
}

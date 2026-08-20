import {
  Briefcase,
  Clipboard,
  CreditCard,
  FileText,
  Home,
  Shield,
  Tool,
  Users,
} from "react-feather";

export const MENUITEMS = [
  {
    menutitle: "Dwella Suite",
    Items: [
      {
        title: "Dashboard",
        icon: Home,
        path: "/dashboard",
        type: "link",
        active: false,
      },
      {
        title: "Properties",
        icon: Briefcase,
        path: "/properties",
        type: "link",
        active: false,
      },
      {
        title: "Tenants",
        icon: Users,
        path: "/tenants",
        type: "link",
        active: false,
      },
      {
        title: "Leases",
        icon: FileText,
        path: "/leases",
        type: "link",
        active: false,
      },
      {
        title: "Billing",
        icon: CreditCard,
        path: "/billing",
        type: "link",
        active: false,
      },
      {
        title: "Maintenance",
        icon: Tool,
        path: "/maintenance",
        type: "link",
        active: false,
      },
      {
        title: "Reports",
        icon: Clipboard,
        path: "/reports",
        type: "link",
        active: false,
      },
      {
        title: "Security",
        icon: Shield,
        path: "/security",
        type: "link",
        active: false,
      },
    ],
  },
];

export interface KanbanItem {
  id: number;
  list?: number;
  title?: string;
  place?: string;
  image?: string;
  priority?: string;
  badge?: string;
  date?: string;
  more?: string;
  img?: string;
}
export interface BreadcrumbsProps {
  title?: string;
  main?: string;
  sub?: string;
}
export interface DataItem {
  id: number;
  fillstar: boolean;
  image: string;
  title: string;
  website_url: string;
  desc: string;
  collection: string;
}

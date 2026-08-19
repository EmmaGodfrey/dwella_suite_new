interface courses {
  id?: number;
  image?: string;
  dd?: string;
  mm?: string;
  yy?: string;
  author?: string;
  hits?: number;
  title?: string;
  descr?: string;
  descr_count?: number;
  category?: number;
  price?: number;
  status?: number;
  comments?: comments[];
  special?: number;
}
interface comments {
  username?: string;
  role?: string;
  descr?: string;
  image?: string;
  hits?: string;
  comments?: string;
}

export default courses;

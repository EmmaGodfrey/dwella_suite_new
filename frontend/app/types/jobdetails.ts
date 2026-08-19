interface details {
  id: number;
  image: string;
  title: string;
  description: string;
  company: string;
  city: string;
  country: string;
  stars: number;
  date: string;
  priority: number;
  resp: resp[];
  reqs: reqs[];
  skills: skill[];
}
interface resp {
  title: string;
}
interface reqs {
  title: string;
}
interface skill {
  title: string;
}

export default details;

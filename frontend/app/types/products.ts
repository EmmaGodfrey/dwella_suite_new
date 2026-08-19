export interface product {
  sku: number;
  name: string;
  images: string[];
  shortDescription: string;
  description: string;
  details: string;
  salePrice: number;
  price: number;
  sale: boolean;
  off?: boolean;
  category: string[];
  colors: string[];
  size: string[];
  brand: string;
  tags: string[];
  stock: number;
  quantity: number;
}

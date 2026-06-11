import type { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: 'https://knowledge-search.askatlas.info/',
      priority: 1.0,
    },
  ];
}

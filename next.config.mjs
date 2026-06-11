/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export: `npm run build` writes a fully static site to out/.
  output: 'export',
  images: { unoptimized: true },
  trailingSlash: true,
};
export default nextConfig;

import './landing.css';
import './brochure.css';

export const metadata = {
  title: 'Think Rugs | Licensed Brands',
  description:
    'Think Rugs licensed brand collections: Scion Living, Harlequin, Clarke & Clarke, House Llewelyn-Bowen, Catherine Lansfield and Catherine Lansfield Kids rugs, each presented in its own interactive brochure.',
};

// One font request covers every brand: Poppins (Think Rugs and Scion),
// Hanken Grotesk (Harlequin), Jost (Clarke & Clarke and LLB body) and
// Cormorant Garamond (LLB display).
const FONTS =
  'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&family=Hanken+Grotesk:wght@300;400;500;600&family=Jost:wght@300;400;500;600&family=Cormorant+Garamond:wght@500;600;700&display=swap';

export default function RootLayout({ children }) {
  return (
    <html lang="en-GB">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href={FONTS} rel="stylesheet" />
        <style>{'*{margin:0;padding:0;box-sizing:border-box} html{scroll-behavior:smooth} body.modal-open{overflow:hidden} button{font-family:inherit;cursor:pointer} @media (prefers-reduced-motion: reduce){ html{scroll-behavior:auto} }'}</style>
      </head>
      <body>{children}</body>
    </html>
  );
}

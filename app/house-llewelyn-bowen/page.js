import BrandBrochure from '@/components/BrandBrochure';
import { getBrand, getTheme, getDownload, getSelKey } from '@/lib/catalogue';

const KEY = 'LLB';

export function generateMetadata() {
  const t = getTheme(KEY);
  return {
    title: t.display_name + ' | ' + (t.SUB || 'Washable Rug Collection') + ' | Think Rugs',
    description: t.BLURB,
  };
}

export default function Page() {
  return (
    <BrandBrochure
      theme={getTheme(KEY)}
      data={getBrand(KEY)}
      downloadHref={getDownload(KEY)}
      selKey={getSelKey(KEY)}
    />
  );
}

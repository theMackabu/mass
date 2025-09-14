import { tw } from '@/service/utils';

import Link from 'next/link';
import Image from 'next/image';
import MassImage from '@/assets/mass.png';

type MassLogoProps = {
  size?: number;
  href?: string;
  className?: string;
};

export const MassLogo = ({ href, size = 110, className }: MassLogoProps) => {
  const image = (
    <Image
      width={size}
      height={size}
      src={MassImage}
      className={tw('pointer-events-none select-none', className)}
      alt="Mass Platform"
    />
  );
  return href ? <Link href={href}>{image}</Link> : image;
};

import Image from "next/image";

/* The सेतु mark. The gradient carries the brand, so it stays as artwork rather
   than being recolored per theme — it reads on both surfaces as-is. */
export default function Logo({ size = 24 }: { size?: number }) {
  return (
    <Image
      src="/logo.png"
      alt=""
      width={size}
      height={Math.round((size * 438) / 512)}
      priority
      className="shrink-0"
    />
  );
}

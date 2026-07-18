"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/**
 * Header nav item with active-route state. Active links carry the seal accent
 * plus an underline rule so the current section is legible without relying on
 * colour alone (accessibility: colour is never the only indicator).
 */
export function NavLink({ href, label }: { href: string; label: string }) {
  const pathname = usePathname();
  const active = href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={`relative py-1 transition-colors duration-200 hover:text-parchment ${
        active
          ? "text-seal after:absolute after:inset-x-0 after:-bottom-px after:h-px after:bg-seal"
          : "text-parchment-dim"
      }`}
    >
      {label}
    </Link>
  );
}

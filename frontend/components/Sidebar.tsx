"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "ホーム", href: "/dashboard", icon: "��" },
  { name: "ベンダー", href: "/dashboard/vendors", icon: "🏢" },
  { name: "検索", href: "/dashboard/search", icon: "🔍" },
  { name: "設定", href: "/dashboard/settings", icon: "⚙️" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="bg-white shadow-lg w-64 min-h-screen">
      <div className="p-6">
        <h2 className="text-lg font-semibold text-gray-900">メニュー</h2>
      </div>
      <nav className="mt-6">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center px-6 py-3 text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-50 text-blue-700 border-r-2 border-blue-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <span className="mr-3 text-lg">{item.icon}</span>
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
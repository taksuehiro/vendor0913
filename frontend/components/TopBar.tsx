"use client";

import { useSession, signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";

export default function TopBar() {
  const { data: session } = useSession();

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="flex items-center justify-between px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">
            AIベンダー調査システム
          </h1>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-600">
            ようこそ、{session?.user?.name}さん
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => signOut()}
          >
            ログアウト
          </Button>
        </div>
      </div>
    </header>
  );
}
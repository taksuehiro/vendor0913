import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <div className="text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-8">
        AIベンダー調査システム
      </h1>
      <p className="text-xl text-gray-600 mb-8">
        LangChainを使用したAI市場調査システム
      </p>
      <div className="space-x-4">
        <Link href="/login">
          <Button size="lg">ログイン</Button>
        </Link>
        <Link href="/dashboard">
          <Button variant="outline" size="lg">ダッシュボード</Button>
        </Link>
      </div>
    </div>
  );
}
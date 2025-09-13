import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-6">
            🚀 Vendor Management System
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Next.js 15 + AWS Amplify でデプロイ成功！
          </p>
          
          <div className="space-y-4">
            <div className="bg-white rounded-lg shadow-md p-6 max-w-md mx-auto">
              <h2 className="text-lg font-semibold mb-4">システム情報</h2>
              <ul className="text-left space-y-2 text-sm text-gray-600">
                <li>✅ Next.js 15.5.3</li>
                <li>✅ App Router</li>
                <li>✅ NextAuth.js</li>
                <li>✅ Tailwind CSS v4</li>
                <li>✅ AWS Amplify Hosting</li>
              </ul>
            </div>
            
            <div className="space-x-4">
              <Link 
                href="/login"
                className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
              >
                ログインページへ
              </Link>
              <Link 
                href="/dashboard"
                className="inline-block bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
              >
                ダッシュボードへ
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
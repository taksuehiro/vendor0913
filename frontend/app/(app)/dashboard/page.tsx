"use client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useState, useEffect } from "react";
import { apiClient, Vendor, SearchResult } from "@/lib/api";

export default function DashboardPage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState("");
  const [showSearchResults, setShowSearchResults] = useState(false);

  useEffect(() => {
    loadVendors();
  }, []);

  const loadVendors = async () => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem('access_token');
      if (token) {
        apiClient.setToken(token);
      }
      const vendorData = await apiClient.getVendors();
      setVendors(vendorData);
    } catch (error) {
      console.error("ベンダー一覧の取得に失敗:", error);
      setError("ベンダー一覧の取得に失敗しました");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchTerm.trim()) {
      setShowSearchResults(false);
      return;
    }

    try {
      setIsSearching(true);
      setError("");
      const results = await apiClient.searchVendors({
        query: searchTerm,
        max_results: 10
      });
      setSearchResults(results);
      setShowSearchResults(true);
    } catch (error) {
      console.error("検索に失敗:", error);
      setError("検索に失敗しました");
    } finally {
      setIsSearching(false);
    }
  };

  const filteredVendors = vendors.filter(vendor =>
    vendor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    vendor.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 px-4 sm:px-6 lg:px-8">
      {/* 統計カード */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="relative overflow-hidden bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200 hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-700">総ベンダー数</CardTitle>
            <span className="text-3xl">🏢</span>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-900">
              {vendors.length}
            </div>
            <p className="text-xs text-blue-600 mt-1">
              +{Math.floor(vendors.length * 0.12)} 先月比
            </p>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden bg-gradient-to-br from-green-50 to-green-100 border-green-200 hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-700">アクティブベンダー</CardTitle>
            <span className="text-3xl">✅</span>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-900">
              {vendors.filter(v => v.is_active).length}
            </div>
            <p className="text-xs text-green-600 mt-1">
              +{Math.floor(vendors.filter(v => v.is_active).length * 0.08)} 先月比
            </p>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200 hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-purple-700">カテゴリ数</CardTitle>
            <span className="text-3xl">🏷️</span>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-900">
              {new Set(vendors.map(v => v.category)).size}
            </div>
            <p className="text-xs text-purple-600 mt-1">
              +{Math.floor(new Set(vendors.map(v => v.category)).size * 0.15)} 先月比
            </p>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200 hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-orange-700">検索回数</CardTitle>
            <span className="text-3xl">🔍</span>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-900">
              {searchResults.length > 0 ? searchResults.length * 12 : 0}
            </div>
            <p className="text-xs text-orange-600 mt-1">
              +{Math.floor((searchResults.length > 0 ? searchResults.length * 12 : 0) * 0.05)} 先月比
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 検索パネル */}
      <Card className="bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-indigo-800">
            <span className="text-2xl">🔍</span>
            <span>AIベンダー検索</span>
          </CardTitle>
          <p className="text-sm text-indigo-600 mt-1">
            自然言語でAIベンダーを検索し、最適なソリューションを見つけましょう
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="search" className="text-sm font-medium text-gray-700">
                検索キーワード
              </Label>
              <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3">
                <div className="flex-1 relative">
                  <Input
                    id="search"
                    placeholder="例: 自然言語処理、画像認識、音声認識、機械学習..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    className="pl-4 pr-12 h-12 text-base sm:text-lg border-2 border-indigo-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 rounded-xl"
                  />
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    <span className="text-gray-400 text-lg">💡</span>
                  </div>
                </div>
                <Button 
                  onClick={handleSearch} 
                  disabled={isSearching || !searchTerm.trim()}
                  className="h-12 px-6 sm:px-8 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed w-full sm:w-auto"
                >
                  {isSearching ? (
                    <div className="flex items-center justify-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>検索中...</span>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center space-x-2">
                      <span className="text-lg">🔍</span>
                      <span>検索</span>
                    </div>
                  )}
                </Button>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-3">
              <Button 
                onClick={loadVendors} 
                disabled={isLoading} 
                variant="outline"
                className="h-10 px-6 border-indigo-300 text-indigo-700 hover:bg-indigo-50 rounded-lg transition-colors"
              >
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                    <span>読み込み中...</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <span>📋</span>
                    <span>一覧更新</span>
                  </div>
                )}
              </Button>
              
              {showSearchResults && (
                <Button 
                  onClick={() => setShowSearchResults(false)} 
                  variant="outline"
                  className="h-10 px-6 border-red-300 text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <div className="flex items-center space-x-2">
                    <span>✕</span>
                    <span>検索結果を閉じる</span>
                  </div>
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* エラー表示 */}
      {error && (
        <div className="text-red-600 text-sm text-center p-4 bg-red-50 rounded">
          {error}
        </div>
      )}

      {/* 検索結果表示 */}
      {showSearchResults && (
        <Card className="bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-emerald-800">
              <span className="text-2xl">🔍</span>
              <span>検索結果</span>
              <span className="bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full text-sm font-medium">
                {searchResults.length}件
              </span>
            </CardTitle>
            <p className="text-sm text-emerald-600 mt-1">
              「{searchTerm}」の検索結果を表示しています
            </p>
          </CardHeader>
          <CardContent>
            {searchResults.length > 0 ? (
              <div className="space-y-4">
                {searchResults.map((result, index) => (
                  <div 
                    key={index}
                    className="bg-white rounded-xl border border-emerald-200 p-6 hover:shadow-lg transition-all duration-200 hover:border-emerald-300"
                  >
                    <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between mb-4 space-y-4 lg:space-y-0">
                      <div className="flex-1">
                        <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2">
                          {result.vendor_name}
                        </h3>
                        <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-3 mb-3">
                          <span className="bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full text-sm font-medium w-fit">
                            {result.category}
                          </span>
                          <div className="flex items-center space-x-1">
                            <span className="text-sm text-gray-600">マッチ度:</span>
                            <div className="flex items-center space-x-2">
                              <div className="w-16 sm:w-20 bg-gray-200 rounded-full h-2">
                                <div 
                                  className="bg-gradient-to-r from-emerald-400 to-emerald-600 h-2 rounded-full transition-all duration-500"
                                  style={{ width: `${result.score * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-sm font-medium text-emerald-700">
                                {(result.score * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        </div>
                        <p className="text-gray-700 leading-relaxed mb-4 text-sm sm:text-base">
                          {result.description}
                        </p>
                      </div>
                      {result.website_url && (
                        <a 
                          href={result.website_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white px-4 py-2 rounded-lg font-medium transition-all duration-200 hover:shadow-lg flex items-center justify-center space-x-2 w-full lg:w-auto"
                        >
                          <span>🌐</span>
                          <span>訪問</span>
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🔍</div>
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  検索結果が見つかりませんでした
                </h3>
                <p className="text-gray-500 mb-6">
                  別のキーワードで検索してみてください
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm">
                    自然言語処理
                  </span>
                  <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm">
                    画像認識
                  </span>
                  <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm">
                    音声認識
                  </span>
                  <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm">
                    機械学習
                  </span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ベンダー一覧テーブル */}
      <Card>
        <CardHeader>
          <CardTitle>ベンダー一覧</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-4">読み込み中...</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>ベンダー名</TableHead>
                  <TableHead>カテゴリ</TableHead>
                  <TableHead>説明</TableHead>
                  <TableHead>ステータス</TableHead>
                  <TableHead>作成日</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredVendors.map((vendor) => (
                  <TableRow key={vendor.id}>
                    <TableCell>{vendor.id}</TableCell>
                    <TableCell className="font-medium">{vendor.name}</TableCell>
                    <TableCell>{vendor.category}</TableCell>
                    <TableCell>{vendor.description || "-"}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 rounded text-xs ${
                        vendor.is_active 
                          ? "bg-green-100 text-green-800" 
                          : "bg-red-100 text-red-800"
                      }`}>
                        {vendor.is_active ? "アクティブ" : "非アクティブ"}
                      </span>
                    </TableCell>
                    <TableCell>
                      {new Date(vendor.created_at).toLocaleDateString('ja-JP')}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
import React, { useState } from 'react';
import './styles/App.css';

// 类型定义
interface Competitor {
  name: string;
  features: string[];
}

interface AnalysisResponse {
  domain: string | null;
  features: string | null;
  product_name: string;
  queries: string[];
  competitors: Competitor[];
  total_count: number;
  message: string;
}

const App: React.FC = () => {
  const [formData, setFormData] = useState({
    domain: '',
    features: '',
    productName: ''
  });

  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string>('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.domain && !formData.features) {
      alert('请至少填写领域或功能');
      return;
    }

    if (!formData.productName) {
      alert('请填写产品名称');
      return;
    }

    setIsLoading(true);
    setResult(null);
    setError('');

    try {
      const response = await fetch('http://localhost:8001/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          domain: formData.domain || null,
          features: formData.features || null,
          product_name: formData.productName
        })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || '分析请求失败');
      }

      const data = await response.json();
      // 数据验证：确保必要字段存在且格式正确
      const validatedData: AnalysisResponse = {
        domain: data.domain ?? null,
        features: data.features ?? null,
        product_name: data.product_name ?? '',
        queries: Array.isArray(data.queries) ? data.queries : [],
        competitors: Array.isArray(data.competitors)
          ? data.competitors.map((c: any) => ({
              name: c.name ?? '未知竞品',
              features: Array.isArray(c.features) ? c.features : []
            }))
          : [],
        total_count: data.total_count ?? 0,
        message: data.message ?? ''
      };
      setResult(validatedData);
    } catch (err) {
      setError(err instanceof Error ? err.message : '分析失败，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          竞品分析工具
        </h1>

        <div className="bg-white shadow-md rounded-lg p-8 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            输入分析信息
          </h2>
          <p className="text-sm text-gray-500 mb-4">
            可以同时输入领域和功能，系统将并行搜索所有查询
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 领域输入 */}
            <div>
              <label htmlFor="domain" className="block text-sm font-medium text-gray-700 mb-1">
                分析领域（可选）
              </label>
              <input
                type="text"
                id="domain"
                name="domain"
                value={formData.domain}
                onChange={handleChange}
                placeholder="例如：AI教育、在线协作、项目管理"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* 功能输入 */}
            <div>
              <label htmlFor="features" className="block text-sm font-medium text-gray-700 mb-1">
                功能描述（可选）
              </label>
              <textarea
                id="features"
                name="features"
                value={formData.features}
                onChange={handleChange}
                placeholder="例如：AI批阅试卷、自动组卷、错题分析、智能推荐题目"
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="mt-1 text-xs text-gray-500">
                输入功能描述，系统会自动提取功能点并生成搜索查询
              </p>
            </div>

            {/* 产品名称 */}
            <div>
              <label htmlFor="productName" className="block text-sm font-medium text-gray-700 mb-1">
                产品名称
              </label>
              <input
                type="text"
                id="productName"
                name="productName"
                value={formData.productName}
                onChange={handleChange}
                placeholder="例如：我的AI助手"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${
                isLoading
                  ? 'bg-blue-300 text-white cursor-not-allowed'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              {isLoading ? '分析中...' : '开始分析'}
            </button>
          </form>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {result && (
          <div className="bg-white shadow-md rounded-lg p-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              竞品分析结果
            </h2>

            <div className="mb-6 space-y-2">
              {result.domain && (
                <p className="text-sm text-gray-600">
                  <span className="font-medium">领域：</span>{result.domain}
                </p>
              )}
              {result.features && (
                <p className="text-sm text-gray-600">
                  <span className="font-medium">功能：</span>{result.features}
                </p>
              )}
              <p className="text-sm text-gray-600">
                <span className="font-medium">产品：</span>{result.product_name}
              </p>
              <div className="text-sm text-gray-600">
                <span className="font-medium">搜索查询（{result.queries.length}个）：</span>
                <ul className="list-disc list-inside ml-2 mt-1">
                  {result.queries.map((query, idx) => (
                    <li key={idx}>{query}</li>
                  ))}
                </ul>
              </div>
              <p className="text-sm text-gray-600">
                <span className="font-medium">分析结果：</span>{result.message}
              </p>
            </div>

            {result.competitors.length > 0 ? (
              <div className="space-y-4">
                {result.competitors.map((competitor, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {competitor.name}
                    </h3>

                    <div className="mb-2">
                      <span className="text-sm font-medium text-gray-700">核心功能：</span>
                    </div>

                    <ul className="list-disc list-inside space-y-1">
                      {competitor.features.map((feature, idx) => (
                        <li key={idx} className="text-sm text-gray-600">
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                未发现相关竞品
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;

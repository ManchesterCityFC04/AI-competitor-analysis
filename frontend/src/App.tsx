import React, { useState } from 'react';
import './styles/App.css';

// 类型定义
interface Competitor {
  name: string;
  features: string[];
}

interface AnalysisResponse {
  domain: string;
  product_name: string;
  query: string;
  competitors: Competitor[];
  total_count: number;
  message: string;
}

const App: React.FC = () => {
  const [formData, setFormData] = useState({
    domain: '',
    productName: ''
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string>('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.domain || !formData.productName) {
      alert('请填写完整信息');
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
          domain: formData.domain,
          product_name: formData.productName
        })
      });

      if (!response.ok) {
        throw new Error('分析请求失败');
      }

      const data = await response.json();
      setResult(data);
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
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="domain" className="block text-sm font-medium text-gray-700 mb-1">
                分析领域
              </label>
              <input
                type="text"
                id="domain"
                name="domain"
                value={formData.domain}
                onChange={handleChange}
                placeholder="例如：AI教育、项目管理工具"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

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
            
            <div className="mb-6">
              <p className="text-sm text-gray-600 mb-2">
                <span className="font-medium">领域：</span>{result.domain}
              </p>
              <p className="text-sm text-gray-600 mb-2">
                <span className="font-medium">产品：</span>{result.product_name}
              </p>
              <p className="text-sm text-gray-600 mb-2">
                <span className="font-medium">搜索查询：</span>{result.query}
              </p>
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

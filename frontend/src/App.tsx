import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Target, Zap, Sparkles, Package, List, Brain, ChevronRight, AlertCircle, CheckCircle, RotateCcw as Loader } from 'lucide-react';

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
      setError('请至少填写领域或功能');
      return;
    }

    if (!formData.productName) {
      setError('请填写产品名称');
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/80 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Hero 区域 */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-600 rounded-full text-xs font-bold mb-6 border border-indigo-100 tracking-widest uppercase shadow-sm">
            <Sparkles className="w-3 h-3 fill-current" />
            AI 竞品分析
          </div>
          
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-4xl md:text-5xl font-black tracking-tight text-slate-900 mb-6"
          >
            智能竞品分析工具
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-lg text-slate-500 font-medium max-w-2xl mx-auto leading-relaxed"
          >
            通过 AI 智能分析，快速发现市场上的竞品产品，获取其核心功能和特点，助力您的产品决策。
          </motion.p>
        </motion.div>

        {/* 输入表单 */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 mb-12 shadow-xl border border-slate-100"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Target className="w-5 h-5 text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold text-slate-800">分析参数</h2>
          </div>
          
          <p className="text-slate-500 mb-8 text-sm">
            可以同时输入领域和功能，系统将并行搜索所有查询
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="domain" className="block text-sm font-bold text-slate-700 mb-3 flex items-center gap-2">
                <Search className="w-4 h-4" />
                分析领域（可选）
              </label>
              <input
                type="text"
                id="domain"
                name="domain"
                value={formData.domain}
                onChange={handleChange}
                placeholder="例如：AI教育、在线协作、项目管理、智能客服"
                className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-slate-700 placeholder-slate-400"
              />
            </div>

            <div>
              <label htmlFor="features" className="block text-sm font-bold text-slate-700 mb-3 flex items-center gap-2">
                <Brain className="w-4 h-4" />
                功能描述（可选）
              </label>
              <textarea
                id="features"
                name="features"
                value={formData.features}
                onChange={handleChange}
                placeholder="例如：AI批阅试卷、自动组卷、错题分析、智能推荐题目"
                rows={4}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-slate-700 placeholder-slate-400"
              />
              <p className="mt-2 text-xs text-slate-500">
                输入功能描述，系统会自动提取功能点并生成搜索查询
              </p>
            </div>

            <div>
              <label htmlFor="productName" className="block text-sm font-bold text-slate-700 mb-3 flex items-center gap-2">
                <Package className="w-4 h-4" />
                产品名称
              </label>
              <input
                type="text"
                id="productName"
                name="productName"
                value={formData.productName}
                onChange={handleChange}
                placeholder="例如：我的AI助手"
                className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-slate-700 placeholder-slate-400"
                required
              />
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={isLoading}
              className={`w-full py-4 rounded-xl font-bold text-lg shadow-lg transition-all flex items-center justify-center gap-3 ${
                isLoading
                  ? 'bg-blue-300 text-white cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 hover:shadow-xl'
              }`}
            >
              {isLoading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  分析中...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  开始智能分析
                  <ChevronRight className="w-5 h-5" />
                </>
              )}
            </motion.button>
          </form>
        </motion.div>

        {/* 错误提示 */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-red-50 border border-red-200 rounded-xl p-6 mb-8 flex items-start gap-3"
            >
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-red-700 font-medium">{error}</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 分析结果 */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -30 }}
              className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 shadow-xl border border-slate-100"
            >
              <div className="flex items-center gap-3 mb-8">
                <div className="p-3 bg-green-100 rounded-xl">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
                <h2 className="text-2xl font-bold text-slate-800">分析结果</h2>
              </div>

              <div className="mb-8 p-6 bg-slate-50 rounded-xl border border-slate-100">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-1">分析领域</p>
                    <p className="text-slate-800 font-bold">{result.domain || '未指定'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-1">产品名称</p>
                    <p className="text-slate-800 font-bold">{result.product_name}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-1">发现竞品</p>
                    <p className="text-slate-800 font-bold text-green-600">{result.total_count} 个</p>
                  </div>
                </div>
                
                <div className="mt-4 pt-4 border-t border-slate-200">
                  <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2">搜索查询</p>
                  <div className="flex flex-wrap gap-2">
                    {result.queries.map((query, idx) => (
                      <span key={idx} className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium">
                        {query}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 mb-6">
                <List className="w-5 h-5 text-slate-600" />
                <h3 className="text-xl font-bold text-slate-800">竞品列表</h3>
                <span className="ml-2 px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-bold">
                  {result.competitors.length} 个
                </span>
              </div>

              <div className="space-y-6">
                {result.competitors.length > 0 ? (
                  result.competitors.map((competitor, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-6 rounded-xl border border-slate-200 hover:border-indigo-300 transition-all hover:shadow-md bg-white"
                    >
                      <div className="flex items-start justify-between">
                        <h4 className="text-lg font-bold text-slate-900">{competitor.name}</h4>
                        <div className="p-2 bg-indigo-100 rounded-lg">
                          <Package className="w-4 h-4 text-indigo-600" />
                        </div>
                      </div>

                      <div className="mt-4">
                        <p className="text-sm font-bold text-slate-700 mb-3 flex items-center gap-2">
                          <Brain className="w-4 h-4" />
                          核心功能
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {competitor.features.map((feature, idx) => (
                            <span key={idx} className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg text-sm">
                              {feature}
                            </span>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  ))
                ) : (
                  <div className="text-center py-12 text-slate-500">
                    <Package className="w-12 h-12 mx-auto text-slate-300 mb-4" />
                    <p className="text-lg font-medium">未发现相关竞品</p>
                    <p className="text-sm mt-1">尝试调整搜索参数以获得更好的结果</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default App;

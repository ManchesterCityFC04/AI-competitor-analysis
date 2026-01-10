import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Target, Zap, Sparkles, Package, List, Brain, ChevronRight, AlertCircle, CheckCircle, RotateCcw as Loader, Star, Download, FileSpreadsheet, FileText } from 'lucide-react';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';

// 类型定义
interface Competitor {
  score: number;
  reason: string;
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

interface ProgressInfo {
  stage: string;
  progress: number;
  detail: string;
}

// 获取相关性标签
const getScoreLabel = (score: number) => {
  if (score >= 9) return { text: '高度相关', color: 'bg-green-100 text-green-700 border-green-200' };
  if (score >= 7) return { text: '中度相关', color: 'bg-yellow-100 text-yellow-700 border-yellow-200' };
  if (score >= 5) return { text: '低度相关', color: 'bg-orange-100 text-orange-700 border-orange-200' };
  return { text: '弱相关', color: 'bg-slate-100 text-slate-600 border-slate-200' };
};

// 进度阶段配置
const PROGRESS_STAGES = [
  { key: 'init', label: '初始化分析', icon: '🚀' },
  { key: 'query', label: '生成搜索查询', icon: '🔍' },
  { key: 'search', label: '搜索竞品信息', icon: '🌐' },
  { key: 'read', label: '读取网页内容', icon: '📄' },
  { key: 'extract', label: '提取竞品数据', icon: '🤖' },
  { key: 'merge', label: '合并去重', icon: '🔄' },
  { key: 'enrich', label: '深度分析功能', icon: '✨' },
  { key: 'complete', label: '分析完成', icon: '✅' },
];

const App: React.FC = () => {
  const [formData, setFormData] = useState({
    domain: '',
    features: '',
    productName: ''
  });

  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string>('');
  const [progress, setProgress] = useState<ProgressInfo>({ stage: '', progress: 0, detail: '' });
  const resultRef = useRef<HTMLDivElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // 导出为 Excel
  const exportToExcel = () => {
    if (!result) return;

    const data = result.competitors.map((comp, idx) => ({
      '序号': idx + 1,
      '竞品名称': comp.name,
      '相关性评分': comp.score,
      '相关性等级': getScoreLabel(comp.score).text,
      '评分理由': comp.reason || '',
      '核心功能': comp.features.join('、')
    }));

    const ws = XLSX.utils.json_to_sheet(data);

    // 设置列宽
    ws['!cols'] = [
      { wch: 6 },   // 序号
      { wch: 20 },  // 竞品名称
      { wch: 12 },  // 相关性评分
      { wch: 12 },  // 相关性等级
      { wch: 30 },  // 评分理由
      { wch: 60 },  // 核心功能
    ];

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '竞品分析结果');

    // 添加摘要信息
    const summaryData = [
      { '项目': '分析领域', '内容': result.domain || '未指定' },
      { '项目': '产品名称', '内容': result.product_name },
      { '项目': '发现竞品数', '内容': result.total_count },
      { '项目': '搜索查询', '内容': result.queries.join('、') },
      { '项目': '分析时间', '内容': new Date().toLocaleString() },
    ];
    const summaryWs = XLSX.utils.json_to_sheet(summaryData);
    summaryWs['!cols'] = [{ wch: 15 }, { wch: 60 }];
    XLSX.utils.book_append_sheet(wb, summaryWs, '分析摘要');

    const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    saveAs(blob, `竞品分析_${result.product_name}_${new Date().toISOString().slice(0, 10)}.xlsx`);
  };

  // 导出为 PDF（使用浏览器打印）
  const exportToPDF = () => {
    if (!resultRef.current) return;

    // 创建打印窗口
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      alert('请允许弹出窗口以导出PDF');
      return;
    }

    const content = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>竞品分析报告 - ${result?.product_name}</title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; color: #333; }
          h1 { color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 10px; }
          h2 { color: #4f46e5; margin-top: 30px; }
          .summary { background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }
          .summary-item { display: flex; margin: 8px 0; }
          .summary-label { font-weight: bold; width: 120px; color: #64748b; }
          .competitor { border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 15px 0; }
          .competitor-header { display: flex; align-items: center; gap: 15px; margin-bottom: 10px; }
          .competitor-name { font-size: 18px; font-weight: bold; }
          .score-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
          .score-high { background: #dcfce7; color: #166534; }
          .score-mid { background: #fef9c3; color: #854d0e; }
          .score-low { background: #ffedd5; color: #9a3412; }
          .reason { color: #64748b; font-style: italic; margin: 10px 0; }
          .features { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 15px; }
          .feature-tag { background: #f1f5f9; padding: 6px 12px; border-radius: 6px; font-size: 13px; }
          .footer { margin-top: 40px; text-align: center; color: #94a3b8; font-size: 12px; }
          @media print { body { padding: 20px; } }
        </style>
      </head>
      <body>
        <h1>竞品分析报告</h1>
        <div class="summary">
          <div class="summary-item"><span class="summary-label">分析领域：</span><span>${result?.domain || '未指定'}</span></div>
          <div class="summary-item"><span class="summary-label">产品名称：</span><span>${result?.product_name}</span></div>
          <div class="summary-item"><span class="summary-label">发现竞品：</span><span>${result?.total_count} 个</span></div>
          <div class="summary-item"><span class="summary-label">搜索查询：</span><span>${result?.queries.join('、')}</span></div>
          <div class="summary-item"><span class="summary-label">分析时间：</span><span>${new Date().toLocaleString()}</span></div>
        </div>

        <h2>竞品详情</h2>
        ${result?.competitors.map((comp, idx) => {
          const scoreLabel = getScoreLabel(comp.score);
          const scoreClass = comp.score >= 9 ? 'score-high' : comp.score >= 7 ? 'score-mid' : 'score-low';
          return `
            <div class="competitor">
              <div class="competitor-header">
                <span class="competitor-name">${idx + 1}. ${comp.name}</span>
                <span class="score-badge ${scoreClass}">${scoreLabel.text} (${comp.score}/10)</span>
              </div>
              ${comp.reason ? `<div class="reason">"${comp.reason}"</div>` : ''}
              <div><strong>核心功能：</strong></div>
              <div class="features">
                ${comp.features.map(f => `<span class="feature-tag">${f}</span>`).join('')}
              </div>
            </div>
          `;
        }).join('')}

        <div class="footer">
          <p>本报告由 AI 竞品分析工具自动生成</p>
        </div>
      </body>
      </html>
    `;

    printWindow.document.write(content);
    printWindow.document.close();
    printWindow.onload = () => {
      printWindow.print();
    };
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
    setProgress({ stage: 'init', progress: 5, detail: '正在初始化分析...' });

    try {
      // 使用 SSE 获取进度
      const eventSource = new EventSource(
        `http://localhost:8001/api/analyze/stream?domain=${encodeURIComponent(formData.domain || '')}&features=${encodeURIComponent(formData.features || '')}&product_name=${encodeURIComponent(formData.productName)}`
      );

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'progress') {
          setProgress({
            stage: data.stage,
            progress: data.progress,
            detail: data.detail
          });
        } else if (data.type === 'result') {
          eventSource.close();
          const validatedData: AnalysisResponse = {
            domain: data.data.domain ?? null,
            features: data.data.features ?? null,
            product_name: data.data.product_name ?? '',
            queries: Array.isArray(data.data.queries) ? data.data.queries : [],
            competitors: Array.isArray(data.data.competitors)
              ? data.data.competitors
                  .map((c: any) => ({
                    name: c.name ?? '未知竞品',
                    features: Array.isArray(c.features) ? c.features : [],
                    score: typeof c.score === 'number' ? c.score : 5,
                    reason: c.reason ?? ''
                  }))
                  .sort((a: Competitor, b: Competitor) => b.score - a.score)
              : [],
            total_count: data.data.total_count ?? 0,
            message: data.data.message ?? ''
          };
          setResult(validatedData);
          setProgress({ stage: 'complete', progress: 100, detail: '分析完成！' });
          setIsLoading(false);
        } else if (data.type === 'error') {
          eventSource.close();
          setError(data.message || '分析失败');
          setIsLoading(false);
        }
      };

      eventSource.onerror = async () => {
        eventSource.close();
        // 降级到普通请求
        console.log('SSE连接失败，降级到普通请求');
        await fallbackRequest();
      };

    } catch (err) {
      await fallbackRequest();
    }
  };

  // 降级请求（不支持SSE时使用）
  const fallbackRequest = async () => {
    // 模拟进度
    const stages = ['query', 'search', 'read', 'extract', 'merge', 'enrich'];
    let currentStage = 0;

    const progressInterval = setInterval(() => {
      if (currentStage < stages.length) {
        const stageInfo = PROGRESS_STAGES.find(s => s.key === stages[currentStage]);
        setProgress({
          stage: stages[currentStage],
          progress: Math.min(15 + currentStage * 15, 90),
          detail: stageInfo?.label || '处理中...'
        });
        currentStage++;
      }
    }, 3000);

    try {
      const response = await fetch('http://localhost:8001/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain: formData.domain || null,
          features: formData.features || null,
          product_name: formData.productName
        })
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || '分析请求失败');
      }

      const data = await response.json();
      const validatedData: AnalysisResponse = {
        domain: data.domain ?? null,
        features: data.features ?? null,
        product_name: data.product_name ?? '',
        queries: Array.isArray(data.queries) ? data.queries : [],
        competitors: Array.isArray(data.competitors)
          ? data.competitors
              .map((c: any) => ({
                name: c.name ?? '未知竞品',
                features: Array.isArray(c.features) ? c.features : [],
                score: typeof c.score === 'number' ? c.score : 5,
                reason: c.reason ?? ''
              }))
              .sort((a: Competitor, b: Competitor) => b.score - a.score)
          : [],
        total_count: data.total_count ?? 0,
        message: data.message ?? ''
      };
      setResult(validatedData);
      setProgress({ stage: 'complete', progress: 100, detail: '分析完成！' });
    } catch (err) {
      clearInterval(progressInterval);
      setError(err instanceof Error ? err.message : '分析失败，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/80 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
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

        {/* 进度显示 */}
        <AnimatePresence>
          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 mb-8 shadow-xl border border-slate-100"
            >
              <div className="flex items-center gap-3 mb-4">
                <Loader className="w-5 h-5 text-blue-600 animate-spin" />
                <h3 className="text-lg font-bold text-slate-800">分析进度</h3>
              </div>

              {/* 进度条 */}
              <div className="mb-4">
                <div className="flex justify-between text-sm text-slate-600 mb-2">
                  <span>{progress.detail}</span>
                  <span>{progress.progress}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-3">
                  <motion.div
                    className="bg-gradient-to-r from-blue-500 to-indigo-500 h-3 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress.progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </div>

              {/* 阶段指示器 */}
              <div className="grid grid-cols-4 md:grid-cols-8 gap-2 mt-4">
                {PROGRESS_STAGES.map((stage, idx) => {
                  const currentIdx = PROGRESS_STAGES.findIndex(s => s.key === progress.stage);
                  const isCompleted = idx < currentIdx;
                  const isCurrent = stage.key === progress.stage;

                  return (
                    <div
                      key={stage.key}
                      className={`flex flex-col items-center p-2 rounded-lg transition-all ${
                        isCurrent ? 'bg-blue-100 scale-105' : isCompleted ? 'bg-green-50' : 'bg-slate-50'
                      }`}
                    >
                      <span className="text-xl mb-1">{stage.icon}</span>
                      <span className={`text-xs text-center ${
                        isCurrent ? 'text-blue-700 font-bold' : isCompleted ? 'text-green-600' : 'text-slate-400'
                      }`}>
                        {stage.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

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

        <AnimatePresence>
          {result && (
            <motion.div
              ref={resultRef}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -30 }}
              className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 shadow-xl border border-slate-100"
            >
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-green-100 rounded-xl">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-800">分析结果</h2>
                </div>

                {/* 导出按钮 */}
                <div className="flex gap-2">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={exportToExcel}
                    className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-lg font-medium hover:bg-green-200 transition-all"
                  >
                    <FileSpreadsheet className="w-4 h-4" />
                    导出Excel
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={exportToPDF}
                    className="flex items-center gap-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg font-medium hover:bg-red-200 transition-all"
                  >
                    <FileText className="w-4 h-4" />
                    导出PDF
                  </motion.button>
                </div>
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
                  result.competitors.map((competitor, index) => {
                    const scoreLabel = getScoreLabel(competitor.score);
                    return (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="p-6 rounded-xl border border-slate-200 hover:border-indigo-300 transition-all hover:shadow-md bg-white"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            <h4 className="text-lg font-bold text-slate-900">{competitor.name}</h4>
                            <span className={`px-2.5 py-1 text-xs font-bold rounded-full border ${scoreLabel.color}`}>
                              <Star className="w-3 h-3 inline mr-1" />
                              {scoreLabel.text}
                            </span>
                            <span className="text-sm text-slate-400 font-medium">
                              {competitor.score}/10
                            </span>
                          </div>
                          <div className="p-2 bg-indigo-100 rounded-lg">
                            <Package className="w-4 h-4 text-indigo-600" />
                          </div>
                        </div>

                        {competitor.reason && (
                          <p className="mt-2 text-sm text-slate-500 italic">
                            "{competitor.reason}"
                          </p>
                        )}

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
                    );
                  })
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

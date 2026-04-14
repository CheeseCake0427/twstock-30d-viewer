interface Props {
  analysis: string | null;
}

export default function AnalysisPanel({ analysis }: Props) {
  if (!analysis) return null;

  return (
    <div className="analysis-panel">
      <h3>AI 分析</h3>
      <p className="analysis-text">{analysis}</p>
      <p className="analysis-disclaimer">* 此為 AI 生成內容，僅供參考</p>
    </div>
  );
}

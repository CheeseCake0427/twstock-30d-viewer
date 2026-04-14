import { useState } from "react";

interface Props {
  onSearch: (code: string) => void;
  loading: boolean;
}

export default function SearchBar({ onSearch, loading }: Props) {
  const [code, setCode] = useState("");

  const handleSubmit = () => {
    const trimmed = code.trim();
    if (trimmed) onSearch(trimmed);
  };

  return (
    <div className="search-bar">
      <input
        type="text"
        placeholder="輸入股票代號，例如 2330"
        value={code}
        onChange={(e) => setCode(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
        disabled={loading}
      />
      <button onClick={handleSubmit} disabled={loading || !code.trim()}>
        {loading ? "查詢中..." : "查詢"}
      </button>
    </div>
  );
}

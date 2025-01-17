import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./styles.css";

interface Transaction {
  transaction_id: number;
  item: string;
  amount: number;
  description: string;
  transaction_date: string;
  category_id: number;
  payer_id: number;
  split_count: number;
  category_name: string;

  // 保留原本的 splitters（若您後面還有用到），否則可刪
  splitters: { userId: number; amount: number }[];
}

// ★ 新增
interface SplitLine {
  splitId: string; // 前端暫時給的臨時ID
  transactionId: number;
  debtorId: number;
  payerId: number;
  amount: number;
}

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTransaction, setSelectedTransaction] =
    useState<Transaction | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [categories, setCategories] = useState<{ [key: number]: string }>({});
  // ★ 紀錄勾選的交易
  const [selectedTransactions, setSelectedTransactions] = useState<
    Transaction[]
  >([]);
  // ★ 控制「分帳」彈窗
  const [isSplitModalOpen, setIsSplitModalOpen] = useState(false);
  const [splitResults, setSplitResults] = useState<
    Record<string, Record<string, number>>
  >({});
  // ★ 新增：用來記錄要在分帳彈窗顯示的每筆分帳結果
  const [splitLines, setSplitLines] = useState<SplitLine[]>([]);

  const months = [
    "1月",
    "2月",
    "3月",
    "4月",
    "5月",
    "6月",
    "7月",
    "8月",
    "9月",
    "10月",
    "11月",
    "12月",
  ];
  const [currentMonthIndex, setCurrentMonthIndex] = useState(0);

  // 一進 HomePage 就撈交易資料 + 分類 (保留您原本的 fetchCategories() 不動)
  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        const response = await fetch("http://localhost:5001/api/transaction/");
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        const formattedData = (result.data || []).map((tx: any) => ({
          transaction_id: tx.transaction_ID || tx.transaction_id,
          item: tx.item,
          amount: parseFloat(tx.amount) || 0,
          description: tx.description || "",
          transaction_date: tx.transaction_date || "",
          category_id: tx.category_ID || tx.category_id,
          category_name: tx.category_name || "未分類",
          payer_id: tx.payer_ID || tx.payer_id,
          split_count: tx.split_count || 0,
          splitters: tx.splitters || [],
        }));

        setTransactions(formattedData);
      } catch (err) {
        console.error("Error fetching transactions:", err);
        setError("無法獲取交易記錄，請稍後重試");
      } finally {
        setLoading(false);
      }
    };

    const fetchCategories = async () => {
      try {
        const response = await fetch("http://localhost:5001/api/category/");
        if (!response.ok) {
          throw new Error("Failed to fetch category");
        }
        const result = await response.json();
        if (!result.data || !Array.isArray(result.data)) {
          throw new Error("No category data available");
        }
        const categoryMap = result.data.reduce(
          (map: { [key: number]: string }, category: any) => {
            map[category.category_ID] = category.category_name;
            return map;
          },
          {}
        );
        setCategories({});
      } catch (err) {
        console.error("Error fetching categories:", err);
      }
    };

    fetchCategories();
    fetchTransactions();
  }, []);

  // 勾選/取消勾選
  const handleCheckboxChange = (transaction: Transaction, checked: boolean) => {
    if (checked) {
      setSelectedTransactions((prev) => [...prev, transaction]);
    } else {
      setSelectedTransactions((prev) =>
        prev.filter((t) => t.transaction_id !== transaction.transaction_id)
      );
    }
  };

  const calculateSplits = () => {
    const newSplitLines: SplitLine[] = [];

    selectedTransactions.forEach((tx, index) => {
      const debtorId = 3;
      const payerId = tx.payer_id;
      
      const line: SplitLine = {
        splitId: "temp-" + index, // 假的 local ID
        transactionId: tx.transaction_id,
        debtorId: debtorId,
        payerId: payerId,
        amount: tx.amount, // or  (tx.amount / tx.split_count)
      };
      newSplitLines.push(line);

      // 若您一筆 transaction 要拆成多個債務人，也可 push 多筆
    });

    console.log("newSplitLines =", newSplitLines);

    setSplitLines(newSplitLines); // ★ 存到 state
    setIsSplitModalOpen(true); // 打開彈窗
  };
  const saveSplitLinesToDB = async () => {
    try {
      // 後端預期: [ {transactionId, debtorId, payerId, amount}, ... ]
      const payload = splitLines.map((line) => ({
        transactionId: line.transactionId,
        debtorId: line.debtorId,
        payerId: line.payerId,
        amount: line.amount,
      }));

      const resp = await fetch("http://localhost:5001/api/split/splits/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (resp.ok) {
        alert("分帳明細已成功寫入 DB！");
        setIsSplitModalOpen(false);
        setSplitLines([]);
        setSelectedTransactions([]);
      } else {
        const err = await resp.json();
        alert(`寫入失敗: ${err.error || "Unknown Error"}`);
      }
    } catch (error) {
      console.error("Error saving split lines:", error);
      alert("發生錯誤，請檢查 console");
    }
  };

  const saveSplitResults = async () => {
    console.log("Check splits before fetch:", splitResults);
    try {
      const response = await fetch(
        "http://localhost:5005/api/transactions/split/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            splits: splitResults,
            transaction_ids: selectedTransactions.map((t) => t.transaction_id),
          }),
        }
      );

      if (response.ok) {
        alert("分帳結果已成功儲存！");
        setIsSplitModalOpen(false);
        setSelectedTransactions([]);
      } else {
        const errorData = await response.json();
        alert(`儲存失敗：${errorData.error}`);
      }
    } catch (error) {
      console.error("Error saving split results:", error);
      alert("發生錯誤！");
    }
  };

  // 其餘UI
  const totalExpense = transactions.reduce(
    (sum, entry) => sum + (isNaN(entry.amount) ? 0 : entry.amount),
    0
  );

  const goToPreviousMonth = () => {
    setCurrentMonthIndex((prevIndex) =>
      prevIndex === 0 ? months.length - 1 : prevIndex - 1
    );
  };
  const goToNextMonth = () => {
    setCurrentMonthIndex((prevIndex) =>
      prevIndex === months.length - 1 ? 0 : prevIndex + 1
    );
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!transactions.length)
    return <div className="no-data">目前無交易記錄。</div>;

  return (
    <div className="home-container">
      {/* 頁首月份區塊 */}
      <div className="header">
        <button onClick={goToPreviousMonth} className="arrow-button">
          &#8249;
        </button>
        <h2 className="month-title">{months[currentMonthIndex]}</h2>
        <button onClick={goToNextMonth} className="arrow-button">
          &#8250;
        </button>
      </div>

      {/* 圓餅圖區塊 */}
      <div className="pie-chart-container">
        <svg viewBox="0 0 32 32" className="pie-chart">
          <defs>
            <radialGradient id="gradient-circle" cx="50%" cy="50%" r="50%">
              <stop offset="50%" stopColor="#FFECF5" />
              <stop offset="100%" stopColor="#F1E1FF" />
            </radialGradient>
          </defs>
          <circle cx="16" cy="16" r="16" fill="url(#gradient-circle)" />
        </svg>
        <div className="total-expense">總花費: {totalExpense.toFixed(2)}</div>
      </div>

      {/* 交易列表 */}
      <div className="transaction-records">
        <div className="transaction-header">
          <div>帳務紀錄✨</div>
          <button
            className="search-button"
            onClick={() => setIsSearchModalOpen(true)}
          >
            🔍
          </button>
        </div>

        <div className="transaction-table-header">
          <div>選取</div>
          <div>類別</div>
          <div>日期</div>
          <div>名稱</div>
          <div>金額</div>
          <div>描述</div>
        </div>

        <div className="transaction-table-body">
          <table className="transaction-table">
            <tbody>
              {transactions.map((tx) => (
                <tr key={tx.transaction_id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedTransactions.some(
                        (t) => t.transaction_id === tx.transaction_id
                      )}
                      onChange={() =>
                        setSelectedTransactions((prev) =>
                          prev.some(
                            (t) => t.transaction_id === tx.transaction_id
                          )
                            ? prev.filter(
                                (t) => t.transaction_id !== tx.transaction_id
                              )
                            : [...prev, tx]
                        )
                      }
                    />
                  </td>
                  <td>{tx.category_name}</td>
                  <td>{tx.transaction_date}</td>
                  <td>{tx.item}</td>
                  <td>{tx.amount.toFixed(2)}</td>
                  <td>{tx.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <button
        onClick={calculateSplits}
        disabled={selectedTransactions.length === 0}
      >
        計算分帳結果
      </button>

      {/* 其餘小彈窗(交易詳情、搜尋...)等請保持原有，不動 */}
      {isModalOpen && selectedTransaction && (
        <div className="modal">
          <div className="modal-content">
            <h3>交易詳細資訊</h3>
            {/* 省略... */}
            <button onClick={() => setIsModalOpen(false)}>關閉</button>
          </div>
        </div>
      )}

      {isSearchModalOpen && (
        <div className="modal">
          <div className="modal-content">
            <h3>篩選交易記錄</h3>
            {/* 保持原有 */}
            <button onClick={() => setIsSearchModalOpen(false)}>關閉</button>
          </div>
        </div>
      )}

      {isSplitModalOpen && (
        <div className="modal">
          <div className="modal-content">
            <h3>分帳結果 (Split Lines)</h3>

            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th>split_ID</th>
                  <th>transaction_ID</th>
                  <th>debtor_ID</th>
                  <th>payer_ID</th>
                  <th>amount</th>
                </tr>
              </thead>
              <tbody>
                {splitLines.map((line) => (
                  <tr key={line.splitId} style={{ textAlign: "center" }}>
                    <td>{line.splitId}</td>
                    <td>{line.transactionId}</td>
                    <td>{line.debtorId}</td>
                    <td>{line.payerId}</td>
                    <td>{line.amount}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <button onClick={() => setIsSplitModalOpen(false)}>關閉</button>

            {/* ★ 新增：把 splitLines 寫進 DB */}
            <button onClick={saveSplitLinesToDB}>寫入 DB</button>
          </div>
        </div>
      )}

      <div className="action-buttons">
        <button className="add-button" onClick={() => navigate("/accounting")}>
          ✒️
        </button>
        <button
          className="view-score-button"
          onClick={() => navigate("/score")}
        >
          信譽積分
        </button>
      </div>

      {/* 側邊欄 */}
      <div className={`sidebar ${isSidebarOpen ? "open" : ""}`}>
        {isSidebarOpen && (
          <div className="sidebar-content">
            <ul>
              <li>
                <button onClick={() => navigate("/friendlist")}>
                  好友清單
                </button>
              </li>
              <li>
                <button onClick={() => navigate("/split")}>
                  分帳紀錄
                </button>
              </li>
              <li>
                <button onClick={() => navigate("/settings")}>個人檔案</button>
              </li>
            </ul>
          </div>
        )}
      </div>

      <button
        className="sidebar-toggle"
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
      >
        {isSidebarOpen ? "<" : ">"}
      </button>
    </div>
  );
};

export default HomePage;

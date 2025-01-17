import React, { useState, useEffect } from "react";
import "./SplitPage.css";


interface SplitRecord {
  split_id: number;
  transaction_id: number;
  debtor_id: number;
  payer_id: number;
  amount: number;
}

const SplitPage: React.FC = () => {
  const [splits, setSplits] = useState<SplitRecord[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSplits = async () => {
      try {
        const resp = await fetch("http://localhost:5001/api/split/");
        if (!resp.ok) {
          throw new Error(`Server Error: ${resp.status}`);
        }
        const data = await resp.json();
        if (data.data) {
          const formattedSplits = data.data.map((split: any) => ({
            split_id: split.split_id,
            transaction_id: split.transaction_id,
            debtor_id: split.debtor_id,
            payer_id: split.payer_id,
            amount: split.amount,
          }));
          setSplits(formattedSplits);
        }
      } catch (err: any) {
        console.error("Error fetching splits:", err);
        setError(err.message);
      }
    };    
    fetchSplits();
  }, []);

  if (error) {
    return <div>無法取得分帳紀錄: {error}</div>;
  }

  if (!splits.length) {
    return <div>目前沒有任何分帳紀錄</div>;
  }

  return (
    <div>
      <h2>所有分帳紀錄</h2>
      <table>
        <thead>
          <tr>
            <th>split_id</th>
            <th>transaction_id</th>
            <th>debtor_id</th>
            <th>payer_id</th>
            <th>amount</th>
          </tr>
        </thead>
        <tbody>
          {splits.map((s) => (
            <tr key={s.split_id}>
              <td>{s.split_id}</td>
              <td>{s.transaction_id}</td>
              <td>{s.debtor_id}</td>
              <td>{s.payer_id}</td>
              <td>{s.amount}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default SplitPage;

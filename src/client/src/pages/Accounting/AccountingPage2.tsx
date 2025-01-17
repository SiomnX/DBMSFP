import React, { useEffect, useState } from "react";

 const AccountingPage: React.FC = () => {
   const [payer, setPayer] = useState("6"); // 預設登入用戶是 testuser（user_id: 6）
   const [amount, setAmount] = useState("");
   const [date, setDate] = useState(new Date().toISOString().split("T")[0]); // 預設當天日期
   const [splitters, setSplitters] = useState<string[]>([]); // 債務人 ID
   const [description, setDescription] = useState("");
   const [category, setCategory] = useState("");
   const [note, setNote] = useState("");
   const [loading, setLoading] = useState(false);
   const [friends, setFriends] = useState<any[]>([]); // 儲存好友列表（完整數據）
   const [categories, setCategories] = useState<any[]>([]); // 儲存分類列表

   // 模擬當前登入用戶
   const loggedInUser = { id: "6", name: "testuser" };

   // 獲取好友列表
   useEffect(() => {
     const fetchFriends = async () => {
       try {
         const response = await fetch(
           `http://127.0.0.1:5001/api/friendslist?user_id=${loggedInUser.id}`
         );
         if (!response.ok) {
           throw new Error("無法獲取好友列表");
         }

         const result = await response.json();

         // 調試用：打印原始數據
         console.log("原始好友數據:", result);

         // 將整個數據存入狀態
         setFriends(result);

         // 調試用：確認狀態是否更新
         console.log("存入的好友數據:", result);
       } catch (error) {
         console.error("Error fetching friends:", error);
         alert("獲取好友列表失敗，請稍後再試！");
      }
    };
     fetchFriends();
   }, []);

   // 獲取分類列表
   useEffect(() => {
     const fetchCategories = async () => {
       try {
         const response = await fetch("http://127.0.0.1:5001/api/transaction/categories");
         if (!response.ok) {
           throw new Error("無法獲取分類列表");
         }

         const result = await response.json();
         setCategories(result.data || []);
       } catch (error) {
         console.error("Error fetching categories:", error);
         alert("獲取分類列表失敗，請稍後再試！");
       }
     };
     fetchCategories();
   }, []);

   const handleSplitterChange = (userId: string) => {
     setSplitters((prev) =>
       prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };
  const handleSubmit = async () => {
    try {
      if (!description.trim()) {
        alert("請輸入交易名稱！");
        return;
      }
      if (!amount || parseFloat(amount) <= 0) {
        alert("請輸入有效金額！");
        return;
      }
      if (!splitters.length) {
         alert("請選擇至少一個分帳者！");
         return;
       }
       if (!category) {
         alert("請選擇分類！");
         return;
       }

       setLoading(true);

       const payload = {
         item: description,
         amount: parseFloat(amount),
         description: note,
         transaction_date: date,
         category_id: parseInt(category, 10),
         payer_id: parseInt(payer, 10),
         splitters: splitters.map((debtor_id) => parseInt(debtor_id, 10)),
       };

       console.log("Submitting payload:", payload); // 調試用
       const response = await fetch("http://127.0.0.1:5001/api/transaction/split", {
         method: "POST",
         headers: {
           "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || "提交失敗，請稍後再試！");
      }
      const result = await response.json();
      console.log("API Response:", result); // 調試用
      if (!result || !result.data || !result.data.transaction_id) {
        alert("提交成功，但未返回交易ID！");
        return;
      }
      alert(`交易已提交成功！交易ID: ${result.data.transaction_id}`);
      // 重置表單
      setPayer(loggedInUser.id);
      setAmount("");
       setDate(new Date().toISOString().split("T")[0]);
       setSplitters([]);
       setDescription("");
       setCategory("");
       setNote("");
     } catch (error) {
       if (error instanceof Error) {
        alert(error.message);
      } else {
        alert("未知錯誤！");
      }
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="container mt-5">
      <h2 className="text-center text-success mb-4">新增交易</h2>
      <div className="mb-3">
        <label className="form-label">付款人</label>
        <select
          className="form-select"
          value={payer}
          onChange={(e) => setPayer(e.target.value)}
          disabled
        >
          <option value={loggedInUser.id}>{loggedInUser.name}</option>
        </select>
      </div>
      <div className="mb-3">
        <label className="form-label">金額</label>
        <input
          type="number"
          className="form-control"
          placeholder="輸入金額"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
      </div>
      <div className="mb-3">
        <label className="form-label">交易名稱</label>
        <input
          type="text"
          className="form-control"
          placeholder="輸入交易名稱"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>
      <div className="mb-3">
        <label className="form-label">日期</label>
        <input
          type="date"
          className="form-control"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
      </div>
      <div className="mb-3">
        <label className="form-label">分類</label>
        <select
          className="form-select"
           value={category}
           onChange={(e) => setCategory(e.target.value)}
         >
           <option value="">選擇分類</option>
           {categories.map((cat) => (
             <option key={cat.category_id} value={cat.category_id}>
               {cat.category_name}
             </option>
           ))}
         </select>
       </div>
       <div className="mb-3">
         <label className="form-label">分帳者</label>
         {friends.length === 0 ? (
           <p>無好友可分帳</p>
         ) : (
           friends.map((friend, index) => (
             <div key={index} className="form-check">
               <input
                 className="form-check-input"
                 type="checkbox"
                 id={`splitter-${friend.friend_id}`}
                 value={friend.friend_id}
                 checked={splitters.includes(friend.friend_id.toString())}
                 onChange={(e) => handleSplitterChange(e.target.value)}
               />
               <label
                 className="form-check-label"
                 htmlFor={`splitter-${friend.friend_id}`}
               >
                 {friend.nickname}
               </label>
             </div>
           ))
        )}
      </div>
      <div className="mb-3">
        <label className="form-label">備註</label>
        <textarea
          className="form-control"
          rows={3}
          placeholder="輸入備註"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        ></textarea>
      </div>
      <button
        className="btn btn-success w-100"
        onClick={handleSubmit}
        disabled={loading}
      >
        {loading ? "提交中..." : "確認"}
      </button>
    </div>


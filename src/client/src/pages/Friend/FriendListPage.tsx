import React, { useState, useEffect } from 'react';
import FriendList from './FriendList';
import AddFriendModal from './AddFriend';
import DeleteConfirmation from './DeleteConfirmation';
import axios from 'axios';

interface Friend {
  list_id: number;
  friend_id: number;
  nickname: string;
}


const FriendListPage: React.FC = () => {
  const [friends, setFriends] = useState<Friend[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [friendToDelete, setFriendToDelete] = useState<Friend | null>(null); // Track 刪除的好友
  const [friendToRate, setFriendToRate] = useState<Friend | null>(null); // 用來追蹤要評分的好友
  const [selectedScore, setSelectedScore] = useState<number>(0); // 選擇的評分
  const [userId] = useState<number>(1); // temp hardcode user ID for testing

  //const userId = 1;

  // fetch friends from backend
  useEffect(() => {
    console.log('Fetching friends for user:', userId); // Debug log
    axios
      .get(`http://localhost:5001/api/friendslist/?user_id=${userId}`)
      .then((response) => {
        if (response.data) {
          console.log('Friends fetched:', response.data); // debug msg
          setFriends(response.data); // updt friends from backend
        } else { console.error('No data received from backend :('); }
      })
      .catch((error) => console.error('Error fetching friends:', error));
  }, [userId]);

  // 新增好友
  const addFriend = (friendId: number, nickname: string) => {

    // 檢查是否已經加過好友
    if(friends.some((friend) => friend.friend_id === friendId)){
      alert("你們已經是朋友！");
    return; // Stop
    }

    axios
      .post('http://localhost:5001/api/friendslist/', {
        user_id: userId, // dynamic uID
        friend_id: friendId,
        nickname,
      })
      .then((response) => {
        // safety check, ensure backend resp is valid before updating state
        if(response.data && response.data.list_id){ 
          setFriends((prev) => [
            ...prev,
            { list_id: response.data.list_id, friend_id: friendId, nickname },
          ]);
        }
        setShowAddModal(false);
      })
      .catch((error) => console.error('Error adding friend:', error));
  };

 // delete a friend
  const deleteFriend = () => {
    console.log('Deleting friend:', friendToDelete); // Debug
    if (friendToDelete) {
      axios
        .delete(`http://localhost:5001/api/friendslist/${friendToDelete.list_id}`)
        .then(() => {
          setFriends((prev) =>
            prev.filter((friend) => friend.list_id !== friendToDelete.list_id)
          );
          setFriendToDelete(null);
        })
        .catch((error) => console.error('Error deleting friend:', error));
    }
  };

    // 評分好友
  const rateFriend = () => {
    if (!friendToRate || selectedScore === 0) {
      alert("請選擇好友並設定評分！");
      return;
    }
  
    axios
      .post(`http://localhost:5001/api/leaderboard/creditEvaluation`, {
        user_id: userId,
        friend_id: friendToRate.friend_id,
        score: selectedScore,
      })
      .then((response) => {
        alert("評分成功！");
        setFriendToRate(null);
        setSelectedScore(0); // 重置選擇的分數
      })
      .catch((error) => console.error("Error rating friend:", error));
  };

  return (
    <div className="container">
      <h2 className="text-center mt-5 mb-4">好友清單</h2> {/* Add margin-bottom */}
      <button
        className="btn btn-primary mb-4"
        onClick={() => setShowAddModal(true)}
      >
        新增好友
      </button>

      {friends.length === 0 ? (
        <p className="text-center text-muted">
          你還沒有好友 😢，快來新增一個吧！
        </p>
      ) : (
        <FriendList
          friends={friends}
          onDelete={(listId: number) => {
            const friend = friends.find((f) => f.list_id === listId);
            if (friend) setFriendToDelete(friend); // Show confirmation modal
          }}

          onRate={(listId: number) => {
            const friend = friends.find((f) => f.list_id === listId);
            if (friend) setFriendToRate(friend); // 開啟評分模式
          }}
        />
      )}

      <AddFriendModal
        show={showAddModal}
        onAdd={(friendId, nickname) => addFriend(Number(friendId), nickname)}
        onClose={() => setShowAddModal(false)}
      />

      <DeleteConfirmation
        show={!!friendToDelete}
        friendName={friendToDelete?.nickname}
        onConfirm={deleteFriend}
        onCancel={() => setFriendToDelete(null)}
      />

      {/* 評分對話框 */}
      {friendToRate && (
        <div className="modal show d-block" style={{ backgroundColor: "rgba(0, 0, 0, 0.5)" }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">評分 {friendToRate.nickname}</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setFriendToRate(null)}
                ></button>
              </div>
              <div className="modal-body">
                <label htmlFor="score">選擇分數 (1-5):</label>
                <select
                  id="score"
                  className="form-select"
                  value={selectedScore}
                  onChange={(e) => setSelectedScore(Number(e.target.value))}
                >
                  <option value={0}>請選擇</option>
                  <option value={-20}>1 - 很差</option>
                  <option value={-10}>2 - 不太好</option>
                  <option value={0}>3 - 普通</option>
                  <option value={10}>4 - 不錯</option>
                  <option value={20}>5 - 很棒</option>
                </select>
              </div>
              <div className="modal-footer">
                <button
                  className="btn btn-secondary"
                  onClick={() => setFriendToRate(null)}
                >
                  關閉
                </button>
                <button className="btn btn-primary" onClick={rateFriend}>
                  評分
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FriendListPage;
FriendListPage.tsx

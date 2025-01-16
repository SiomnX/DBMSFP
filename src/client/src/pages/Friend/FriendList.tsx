import React from 'react';

interface Friend {
  list_id: number;
  friend_id: number;
  nickname: string;
}

interface FriendListProps {
  friends: Friend[];
  onDelete: (friend_id: number) => void;
  onRate: (listId: number) => void; // 評分按鈕的回調
}

const FriendList: React.FC<FriendListProps> = ({ friends, onDelete, onRate }) => {
  return (
    <ul className="list-group">
      {friends.map((friend) => (
        <li
          key={friend.friend_id}
          className="list-group-item d-flex justify-content-between align-items-center"
        >
          <div style={{ flex: 1 }}>
            <strong className="d-block">{friend.nickname}</strong>
            <span className="text-muted" style={{ fontSize: '0.9rem' }}>
              @{friend.friend_id}
            </span>
          </div>
          <button
            className="btn btn-danger btn-sm me-2"
            style={{ marginLeft: '200px' }} // spacing between Uname and delete button
            onClick={() => onDelete(friend.list_id)}
          >
            刪除
          </button>
          {/* 評分按鈕 */}
          <button
            className="btn btn-warning btn-sm me-2"
            onClick={() => onRate(friend.list_id)}
          >
            評分
          </button>
        </li>
      ))}
    </ul>
  );
};

export default FriendList;

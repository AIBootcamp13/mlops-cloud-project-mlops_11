import React from 'react';
import './CardGrid.css'; // 스타일 분리 권장

export default function CardGrid({ contentIds }) {
  return (
    <div className="card-grid">
      {contentIds.map((id, idx) => (
        <div className="card" key={idx}>
          <img src={`poster/${id}.jpg`} alt={id} />
        </div>
      ))}
    </div>
  );
}

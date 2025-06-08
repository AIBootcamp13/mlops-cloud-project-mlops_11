import React, { useState, useEffect } from 'react';
import { getRecommendContents } from './api';
import CardGrid from './components/CardGrid';
import DEFAULT_CONTENTS_IDS from './poster.json'


function getRandomContentsIds(count = 10) {
  const shuffled = [...DEFAULT_CONTENTS_IDS].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
}

function App() {
  const k = 10;
  const user = "000";
  const [contentIds, setContentIds] = useState([]);

  useEffect(() => {
    (async () => {
      const ids = await getRecommendContents(k);
      console.log("ids : ", ids)
      setContentIds(ids.length > 0 ? ids : getRandomContentsIds(k));
    })();
  }, []);

  return (    
    <div className="App" style={{ padding: '2rem' }}>
      <h2>{user} 님이 좋아할 만한 콘텐츠</h2>
      <hr />
      <br />
      {console.log("contentIds : ", contentIds)}
      {contentIds.length > 0 && <CardGrid contentIds={contentIds} />}      
    </div>
  );
}

export default App;

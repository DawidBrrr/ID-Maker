import React, { useEffect, useState } from 'react';

function App() {
  const [message, setMessage] = useState('Loading...');

  useEffect(() => {
    fetch("http://localhost:5000/api/hello")
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch((error) => setMessage('Error fetching message'));
  }, []);

  return (
    <div style={{ textAlign: "center", marginTop: "2rem" }}>
      <h1>{message}</h1>
    </div>
  );

}

export default App;
import React, { useRef,useEffect, useState } from 'react';

function App() {
  const [message, setMessage] = useState('Loading...');
  const [uploadResponse, setUploadResponse] = useState("");
  const [croppedUrl, setCroppedUrl] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [sessionId, setSessionId] = useState(localStorage.getItem("session_id") || "");
  const downloadRef = useRef(null);

  useEffect(() => {
    fetch("http://localhost:5000/api/hello")
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch((error) => {
        console.error('Error:', error);
        setMessage('Error fetching message');
      });
  }, []);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setUploadResponse("Uploading and processing...");
    setCroppedUrl("");

    const formData = new FormData();
    formData.append("file", file);
    if(sessionId) formData.append("session_id", sessionId);

    fetch("http://localhost:5000/api/upload", {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.session_id) {
          setSessionId(data.session_id);
          pollStatus(data.task_id, data.session_id);
        }
        if (data.error) {
          setUploadResponse(`Error: ${data.error}`);
        } else {
          setUploadResponse(data.message);
          // Fix the URL construction
          const imageUrl = `http://localhost:5000${data.cropped_file_url}`;
          setCroppedUrl(imageUrl);
        }
      })
      .catch((error) => {
        console.error('Upload error:', error);
        setUploadResponse('Error uploading file');
      })
      .finally(() => {
        setIsUploading(false);
      });
  };

  function pollStatus(taskId, sessionId) {
    const interval = setInterval(() => {
      fetch(`http://localhost:5000/api/status/${taskId}`)
        .then(res => res.json())
        .then(data => {
          if (data.status === "done") {
            clearInterval(interval);
            setUploadResponse("Processing completed successfully!");
            // Zbuduj link do obrazka:
            const imageUrl = `http://localhost:5000/api/output/${sessionId}/${data.file}`;
            setCroppedUrl(imageUrl);
          } else if (data.status === "error") {
            clearInterval(interval);
            setUploadResponse(`Error: ${data.message}`);
          }
        });
    }, 1000);
  }
  const handleDownload = () => {
    if (downloadRef.current) {
      downloadRef.current.click();
    }
  };

  // Czyszczenie przy zamknięciu strony:
useEffect(() => {
  const handleUnload = () => {
    if (sessionId) {
      navigator.sendBeacon(
        "http://localhost:5000/api/clear",
        JSON.stringify({ session_id: sessionId })
      );
    }
  };
  window.addEventListener("beforeunload", handleUnload);
  return () => window.removeEventListener("beforeunload", handleUnload);
}, [sessionId]);

  return (
    <div style={{ textAlign: "center", marginTop: "2rem", padding: "20px" }}>
      <h1>{message}</h1>
      
      <div style={{ margin: "20px 0" }}>
        <input 
          type="file" 
          onChange={handleFileChange} 
          accept="image/*"
          disabled={isUploading}
        />
      </div>
      
      {uploadResponse && (
        <p style={{ 
          color: uploadResponse.includes('Error') ? 'red' : 'green',
          fontWeight: 'bold'
        }}>
          {uploadResponse}
        </p>
      )}

      {croppedUrl && (
        <div style={{ marginTop: "20px" }}>
          <h3>Cropped Image:</h3>
          <img 
            src={croppedUrl} 
            alt="Cropped result" 
            style={{ 
              border: "1px solid #ccc", 
              maxWidth: "100%", 
              height: "auto",
              borderRadius: "8px"
            }} 
          />
          <div style={{ marginTop: "16px" }}>
            {/* Ukryty link do pobrania */}
            <a
              href={croppedUrl}
              download
              ref={downloadRef}
              style={{ display: "none" }}
            >
              Download
            </a>
            <button
              onClick={handleDownload}
              style={{
                display: "inline-block",
                padding: "10px 24px",
                background: "#1976d2",
                color: "#fff",
                borderRadius: "6px",
                textDecoration: "none",
                fontWeight: "bold",
                border: "none",
                cursor: "pointer"
              }}
            >
              Download
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
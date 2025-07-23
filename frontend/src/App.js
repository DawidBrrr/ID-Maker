import React, { useEffect, useState, useRef } from "react";
import styles from "./styles/App.module.css";
import FileUpload from "./components/FileUpload";
import ImagePreview from "./components/ImagePreview";
import Message from "./components/Message";
import { fetchHello, clearSession, pollStatus } from "./utils/api";

function App() {
  const [message, setMessage] = useState("Ładowanie...");
  const [uploadResponse, setUploadResponse] = useState("");
  const [croppedUrl, setCroppedUrl] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [sessionId, setSessionId] = useState(localStorage.getItem("session_id") || "");
  const downloadRef = useRef(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchHello()
      .then((data) => setMessage(data.message))
      .catch(() => setMessage("Problem z pobraniem danych"));
  }, []);

  const startPolling = (taskId, sessionId) => {
    const interval = setInterval(() => {
      pollStatus(taskId).then((data) => {
        if (data.status === "done") {
          clearInterval(interval);
          setUploadResponse("Przetwarzanie zakończone pomyślnie!");
          setCroppedUrl(`${BACKEND_URL}/api/output/${sessionId}/${data.file}`);
        } else if (data.status === "error") {
          clearInterval(interval);
          setUploadResponse(`Error: ${data.message}`);
        }
      });
    }, 1000);
  };

  const handleUpload = (data, formData) => {
    if (data.session_id) {
      setSessionId(data.session_id);
      localStorage.setItem("session_id", data.session_id);
      startPolling(data.task_id, data.session_id);
    }
    if (data.error) {
      setUploadResponse(`Error: ${data.error}`);
    } else {
      setUploadResponse(data.message);
      if (data.cropped_file_url) {
        const imageUrl = `${BACKEND_URL}${data.cropped_file_url}`;
        setCroppedUrl(imageUrl);
      }
    }
  };

  useEffect(() => {
    const handleUnload = () => {
      if (sessionId) clearSession(sessionId);
    };
    window.addEventListener("beforeunload", handleUnload);
    return () => window.removeEventListener("beforeunload", handleUnload);
  }, [sessionId]);

  return (
    <div className={styles.container}>
      <h1>{message}</h1>
      <FileUpload
        onUploadComplete={handleUpload}
        setIsUploading={setIsUploading}
        isUploading={isUploading}
        setUploadResponse={setUploadResponse}
        setCroppedUrl={setCroppedUrl}
        sessionId={sessionId}
      />
      <Message message={uploadResponse} />
      {croppedUrl && (
        <ImagePreview
          imageUrl={croppedUrl}
          downloadRef={downloadRef}
          onDownload={() => downloadRef.current?.click()}
        />
      )}
    </div>
  );
}

export default App;

import React, { useEffect, useState, useRef } from "react";
import styles from "./styles/App.module.css";
import FileUpload from "./components/FileUpload";
import ImagePreview from "./components/ImagePreview";
import Message from "./components/Message";
import DocumentTypeSelector from "./components/DocumentTypeSelector";
import { fetchHello, clearSession, pollStatus } from "./utils/api";

function App() {
  const [message, setMessage] = useState("Ładowanie...");
  const [uploadResponse, setUploadResponse] = useState("");
  const [croppedUrl, setCroppedUrl] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [sessionId, setSessionId] = useState(localStorage.getItem("session_id") || "");
  const [documentType, setDocumentType] = useState("id_card"); // domyślnie dowód osobisty
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
          setCroppedUrl(`${BACKEND_URL}${data.cropped_file_url}`);
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
    <div className={styles.app}>
      <div className={styles.container}>
        <div className={styles.header}>
          <div className={styles.iconWrapper}>
            <svg className={styles.icon} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 19V5C21 3.9 20.1 3 19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="8.5" cy="8.5" r="1.5" stroke="currentColor" strokeWidth="2"/>
              <path d="M21 15L16 10L5 21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h1 className={styles.title}>Przycinanie Zdjęć Dokumentów</h1>
          <p className={styles.subtitle}>Automatyczne kadrowanie zdjęć do paszportu i dowodu osobistego</p>
        </div>

        <div className={styles.content}>
          <DocumentTypeSelector 
            documentType={documentType}
            setDocumentType={setDocumentType}
          />
          
          <FileUpload
            onUploadComplete={handleUpload}
            setIsUploading={setIsUploading}
            isUploading={isUploading}
            setUploadResponse={setUploadResponse}
            setCroppedUrl={setCroppedUrl}
            sessionId={sessionId}
            documentType={documentType}
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
      </div>
    </div>
  );
}

export default App;
import React, { useEffect, useState, useRef } from "react";
import styles from "./styles/App.module.css";
import FileUpload from "./components/FileUpload";
import ImagePreview from "./components/ImagePreview";
import Message from "./components/Message";
import DocumentTypeSelector from "./components/DocumentTypeSelector";
import PrivacyPage from "./components/PrivacyPage";
import AboutPage from "./components/AboutPage";
import { clearSession, pollStatus } from "./utils/api";

function App() {
  const [currentPage, setCurrentPage] = useState("main");
  const [uploadResponse, setUploadResponse] = useState("");
  const [croppedUrl, setCroppedUrl] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [sessionId, setSessionId] = useState(localStorage.getItem("session_id") || "");
  const [documentType, setDocumentType] = useState("id_card"); // domyślnie dowód osobisty
  const downloadRef = useRef(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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
  const handleDownload = async () => {
    try {
      const response = await fetch(croppedUrl);
      const blob = await response.blob();

      // Extract the original file name from the URL
      const originalFileName = croppedUrl.split("/").pop();
      const fileName = originalFileName.replace(/(\.[^.]*)$/, "-skadrowane$1"); // Append '-skadrowane' before the extension

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fileName; // Use the modified file name
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error downloading file:", error);
    }
  };

  return (
    <div className={styles.app}>
      <nav className={styles.navbar}>
        <div className={styles.navbarBrand}>
          <button className={styles.brandButton} onClick={() => setCurrentPage("main")}>
            Kaidr
          </button>
        </div>
        <div className={styles.navbarLinks}>
          <button className={styles.navLink} onClick={() => setCurrentPage("privacy")}>
            Polityka Prywatności
          </button>
          <button className={styles.navLink} onClick={() => setCurrentPage("about")}>
            O stronie
          </button>
        </div>
      </nav>
      <div className={styles.container}>
        {currentPage === "main" && (
          <>
            <div className={styles.header}>
              <h1 className={styles.title}>Przerabianie Zdjęć Do Dokumentów</h1>
              <p className={styles.subtitle}>Automatyczne kadrowanie i poprawianie zdjęć do paszportu i dowodu osobistego</p>
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
                  onDownload={handleDownload}
                />
              )}
            </div>
          </>
        )}
        
        {currentPage === "privacy" && <PrivacyPage />}
        {currentPage === "about" && <AboutPage />}
      </div>
    </div>
  );
}

export default App;
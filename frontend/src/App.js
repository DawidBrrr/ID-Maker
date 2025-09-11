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
  const [biometricWarnings, setBiometricWarnings] = useState([]);
  const [biometricErrors, setBiometricErrors] = useState([]);
  const downloadRef = useRef(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Utility function to construct URLs properly
  const constructUrl = (baseUrl, path) => {
    if (!baseUrl || !path) return "";
    const cleanBase = baseUrl.replace(/\/$/, ""); // Remove trailing slash
    const cleanPath = path.startsWith("/") ? path : `/${path}`; // Ensure leading slash
    return `${cleanBase}${cleanPath}`;
  };

  const startPolling = (taskId, sessionId) => {
    const interval = setInterval(() => {
      pollStatus(taskId).then((data) => {
        if (data.status === "completed") {
          clearInterval(interval);
          setUploadResponse("Przetwarzanie zakończone pomyślnie!");
          // Use the full URL provided by backend
          if (data.cropped_file_url) {
            setCroppedUrl(constructUrl(BACKEND_URL, data.cropped_file_url));
          }

          // Handle biometric information
          if (data.biometric_warnings && data.biometric_warnings.length > 0) {
            setBiometricWarnings(data.biometric_warnings);
          }
          if (data.biometric_errors && data.biometric_errors.length > 0) {
            setBiometricErrors(data.biometric_errors);
          }
        } else if (data.status === "failed") {
          clearInterval(interval);
          setUploadResponse(`Błąd: ${data.error_message || "Wystąpił błąd podczas przetwarzania"}`);

          // Handle biometric errors in failed status
          if (data.biometric_errors && data.biometric_errors.length > 0) {
            setBiometricErrors(data.biometric_errors);
          }
        }
      });
    }, 1000);
  };

  const handleUpload = (data, formData) => {
    // Reset previous states
    setBiometricWarnings([]);
    setBiometricErrors([]);
    setCroppedUrl("");

    if (data.session_id) {
      setSessionId(data.session_id);
      localStorage.setItem("session_id", data.session_id);
      startPolling(data.task_id, data.session_id);
    }
    if (data.error) {
      setUploadResponse(`Błąd: ${data.error}`);
    } else {
      setUploadResponse(data.message);
      if (data.cropped_file_url) {
        const imageUrl = constructUrl(BACKEND_URL, data.cropped_file_url);
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
      if (!croppedUrl) {
        throw new Error("No image URL available for download");
      }

      const response = await fetch(croppedUrl);

      if (!response.ok) {
        throw new Error(`Failed to fetch image: ${response.status} ${response.statusText}`);
      }

      const blob = await response.blob();

      // Extract the original file name from the URL
      const urlParts = croppedUrl.split("/");
      const originalFileName = urlParts[urlParts.length - 1] || "downloaded-image.jpg";
      const fileName = originalFileName.replace(/(\.[^.]*)$/, "-skadrowane$1");

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error downloading file:", error);
      setUploadResponse(`Błąd pobierania: ${error.message}`);
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
              
              <Message message={uploadResponse} type="auto" />
              
              {/* Display biometric errors */}
              {biometricErrors.map((error, index) => (
                <Message key={`error-${index}`} message={error} type="auto" />
              ))}
              
              {/* Display biometric warnings */}
              {biometricWarnings.map((warning, index) => (
                <Message key={`warning-${index}`} message={warning} type="auto" />
              ))}
              
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
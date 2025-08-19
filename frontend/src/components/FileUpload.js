import React, { useRef } from "react";
import styles from "../styles/FileUpload.module.css";
import { uploadFile } from "../utils/api";

export default function FileUpload({
  onUploadComplete,
  setIsUploading,
  isUploading,
  setUploadResponse,
  setCroppedUrl,
  sessionId,
  documentType
}) {
  const fileInputRef = useRef();



  const handleClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Check extension
    const allowedExtensions = ["jpg", "jpeg", "png", "webp"];
    const fileExt = file.name.split('.').pop().toLowerCase();
    if (!allowedExtensions.includes(fileExt)) {
      setUploadResponse("Nieprawidłowy format pliku. Dozwolone: JPG, JPEG, PNG, WEBP.");
      return;
    }

    // Check file size max 25MB
    const maxSize = 25 * 1024 * 1024;
    if (file.size > maxSize) {
      setUploadResponse("Plik jest za duży (maksymalnie 25MB).");
      return;
    }

    setIsUploading(true);
    setUploadResponse("Przesyłanie i przetwarzanie danych...");
    setCroppedUrl("");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("document_type", documentType); 
    if (sessionId) formData.append("session_id", sessionId);

    try {
      const data = await uploadFile(formData);
      onUploadComplete(data, formData);
    } catch (error) {
      setUploadResponse("Nie udało się przesłać pliku");
      console.error(error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className={styles.uploadContainer}>
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        ref={fileInputRef}
        style={{ display: "none" }}
        disabled={isUploading}
      />
      
      <button 
        className={`${styles.uploadButton} ${isUploading ? styles.loading : ''}`} 
        onClick={handleClick} 
        disabled={isUploading}
      >
        {isUploading ? (
          <>
            <div className={styles.spinner}></div>
            <span>Przetwarzanie...</span>
          </>
        ) : (
          <>
            <svg className={styles.uploadIcon} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 15V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <polyline points="7,10 12,15 17,10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <span>Wybierz zdjęcie</span>
          </>
        )}
      </button>
      
      <p className={styles.uploadHint}>
        Obsługiwane formaty: JPG, PNG, WEBP • Maksymalny rozmiar: 25MB
      </p>
    </div>
  );
}
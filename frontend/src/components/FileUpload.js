import React, { useRef } from "react";
import styles from "../styles/FileUpload.module.css";
import { uploadFile } from "../utils/api";

export default function FileUpload({
  onUploadComplete,
  setIsUploading,
  isUploading,
  setUploadResponse,
  setCroppedUrl,
  sessionId
}) {
  const fileInputRef = useRef();

  const handleClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setUploadResponse("Przesyłanie i przetwarzanie danych...");
    setCroppedUrl("");

    const formData = new FormData();
    formData.append("file", file);
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
      {/* Ukryty input */}
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        ref={fileInputRef}
        style={{ display: "none" }}
        disabled={isUploading}
      />
      {/* Stylowany przycisk */}
      <button className={styles.customButton} onClick={handleClick} disabled={isUploading}>
        {isUploading ? "Ładowanie..." : "Wybierz zdjęcie"}
      </button>
    </div>
  );
}

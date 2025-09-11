import React from "react";
import styles from "../styles/ImagePreview.module.css";

export default function ImagePreview({ imageUrl, downloadRef, onDownload }) {
  return (
    <div className={styles.previewContainer}>
      <h3>Skadrowane zdjęcie:</h3>
      <img src={imageUrl} alt="Skadrowane zdjęcie" className={styles.image} />
      <a href={imageUrl} download ref={downloadRef} style={{ display: "none" }}>
        Download
      </a>
      <button onClick={onDownload} className={styles.button}>
        Pobierz
      </button>
    </div>
  );
}

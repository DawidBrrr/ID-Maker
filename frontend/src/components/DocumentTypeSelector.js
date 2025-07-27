import React from "react";
import styles from "../styles/DocumentTypeSelector.module.css";

export default function DocumentTypeSelector({ documentType, setDocumentType }) {
  const documentTypes = [
    { 
      id: "passport", 
      label: "Paszport", 
      description: "35x45mm, wymagania UE",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M4 6C4 4.89543 4.89543 4 6 4H18C19.1046 4 20 4.89543 20 6V18C20 19.1046 19.1046 20 18 20H6C4.89543 20 4 19.1046 4 18V6Z" stroke="currentColor" strokeWidth="2"/>
          <path d="M9 9H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          <path d="M9 13H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          <path d="M9 17H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      )
    },
    { 
      id: "id_card", 
      label: "Dowód Osobisty", 
      description: "35x45mm, normy polskie",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="5" width="20" height="14" rx="2" stroke="currentColor" strokeWidth="2"/>
          <path d="M8 11H8.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          <path d="M12 9H18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          <path d="M12 11H18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          <path d="M12 13H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          <circle cx="8" cy="11" r="2" stroke="currentColor" strokeWidth="2"/>
        </svg>
      )
    }
  ];

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Wybierz typ dokumentu</h2>
      <div className={styles.options}>
        {documentTypes.map(type => (
          <button
            key={type.id}
            className={`${styles.option} ${documentType === type.id ? styles.selected : ''}`}
            onClick={() => setDocumentType(type.id)}
          >
            <div className={styles.iconContainer}>
              {type.icon}
            </div>
            <div className={styles.optionContent}>
              <h3 className={styles.optionTitle}>{type.label}</h3>
              <p className={styles.optionDescription}>{type.description}</p>
            </div>
            {documentType === type.id && (
              <div className={styles.checkmark}>
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 6L9 17L4 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
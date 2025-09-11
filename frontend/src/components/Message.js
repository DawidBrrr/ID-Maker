import React from "react";
import styles from "../styles/Message.module.css";

export default function Message({ message, type = "info" }) {
  if (!message) return null;

  // Determine message type based on content or explicit type
  let messageType = type;
  if (type === "auto") {
    const lowerMessage = message.toLowerCase();
    if (lowerMessage.includes("error") || lowerMessage.includes("failed") || lowerMessage.includes("błąd")) {
      messageType = "error";
    } else if (lowerMessage.includes("warning") || lowerMessage.includes("ostrzeżenie") || lowerMessage.includes("biometric check")) {
      messageType = "warning";
    } else if (lowerMessage.includes("success") || lowerMessage.includes("pomyślnie") || 
               lowerMessage.includes("passed") || lowerMessage.includes("wszystkie")) {
      messageType = "success";
    } else {
      messageType = "info";
    }
  }

  return (
    <p className={`${styles.message} ${styles[messageType]}`}>
      {message}
    </p>
  );
}

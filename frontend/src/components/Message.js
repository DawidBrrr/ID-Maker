import React from "react";
import styles from "../styles/Message.module.css";

export default function Message({ message }) {
  if (!message) return null;
  const isError = message.toLowerCase().includes("error");
  return (
    <p className={`${styles.message} ${isError ? styles.error : styles.success}`}>
      {message}
    </p>
  );
}

import React from "react";
import styles from "../styles/Page.module.css";

const AboutPage = () => {
  return (
    <div className={styles.pageContent}>
      <h1 className={styles.pageTitle}>O Stronie</h1>
      
      <div className={styles.section}>
        <h2>Czym jest Kaidr?</h2>
        <p>
          Kaidr to nowoczesna aplikacja webowa zaprojektowana z myślą o automatycznym 
          kadrowaniu i poprawianiu zdjęć do dokumentów urzędowych. Nasza technologia 
          wykorzystuje zaawansowane algorytmy sztucznej inteligencji do precyzyjnego 
          wykrywania twarzy i dostosowywania zdjęć zgodnie z wymaganiami różnych dokumentów.
        </p>
      </div>

      <div className={styles.section}>
        <h2>Jak to działa?</h2>
        <p>Proces jest prosty i intuicyjny:</p>
        <ol>
          <li><strong>Wybierz typ dokumentu</strong> - dowód osobisty lub paszport</li>
          <li><strong>Prześlij zdjęcie</strong> - wystarczy przeciągnąć plik lub kliknąć aby wybrać</li>
          <li><strong>Automatyczne przetwarzanie</strong> - nasza technologia wykrywa twarz i kadruje zdjęcie</li>
          <li><strong>Pobierz wynik</strong> - gotowe zdjęcie spełniające wymogi urzędowe</li>
        </ol>
      </div>

      <div className={styles.section}>
        <h2>Obsługiwane formaty dokumentów</h2>
        <ul>
          <li><strong>Dowód osobisty</strong> - format 35x45mm zgodny z polskimi standardami</li>
          <li><strong>Paszport</strong> - format 35x45mm zgodny z międzynarodowymi wymogami ICAO</li>
        </ul>
      </div>

      <div className={styles.section}>
        <h2>Zalety korzystania z Kaidr</h2>
        <ul>
          <li><strong>Szybkość</strong> - przetwarzanie zajmuje tylko kilka sekund</li>
          <li><strong>Precyzja</strong> - zaawansowane algorytmy zapewniają dokładne kadrowanie</li>
          <li><strong>Wygoda</strong> - wszystko online, bez potrzeby wizyty w studiu fotograficznym</li>
          <li><strong>Bezpieczeństwo</strong> - zdjęcia są automatycznie usuwane po przetworzeniu</li>
          <li><strong>Darmowe</strong> - podstawowa usługa jest całkowicie bezpłatna</li>
        </ul>
      </div>

      <div className={styles.section}>
        <h2>Wymagania techniczne</h2>
        <p>
          Aplikacja działa w każdej nowoczesnej przeglądarce internetowej i nie wymaga 
          instalacji dodatkowego oprogramowania. Obsługiwane formaty zdjęć to JPG, PNG i WEBP.
        </p>
      </div>

      <div className={styles.section}>
        <h2>Wsparcie techniczne</h2>
        <p>
          Jeśli napotkasz jakiekolwiek problemy z korzystaniem z aplikacji lub masz pytania 
          dotyczące funkcjonalności, możesz skontaktować się z naszym zespołem wsparcia 
          technicznego poprzez formularz kontaktowy.
        </p>
      </div>

      <div className={styles.section}>
        <h2>Przyszłe funkcje</h2>
        <p>Planujemy wprowadzenie dodatkowych funkcji, takich jak:</p>
        <ul>
          <li>Wsparcie dla zdjęć grupowych</li>
          <li>Dodatkowe formaty dokumentów</li>
          <li>Zaawansowane opcje edycji</li>
          <li>API dla deweloperów</li>
        </ul>
      </div>

      <div className={styles.section}>
        <p>
          <strong>Dziękujemy za korzystanie z Kaidr!</strong><br/>
          Zespół Kaidr
        </p>
      </div>
    </div>
  );
};

export default AboutPage;

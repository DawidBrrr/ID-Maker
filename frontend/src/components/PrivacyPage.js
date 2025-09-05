import React from "react";
import styles from "../styles/Page.module.css";

const PrivacyPage = () => {
  return (
    <div className={styles.pageContent}>
      <h1 className={styles.pageTitle}>Polityka Prywatności</h1>
      
      <div className={styles.section}>
        <h2>1. Informacje ogólne</h2>
        <p>
          Niniejsza Polityka Prywatności określa zasady przetwarzania i ochrony danych osobowych 
          użytkowników korzystających z serwisu Kaidr - aplikacji do automatycznego kadrowania 
          zdjęć do dokumentów.
        </p>
      </div>

      <div className={styles.section}>
        <h2>2. Administrator danych</h2>
        <p>
          Administratorem danych osobowych zbieranych za pośrednictwem serwisu jest właściciel 
          aplikacji Kaidr. W sprawach związanych z ochroną danych osobowych można się kontaktować 
          pod adresem email podanym w sekcji kontakt.
        </p>
      </div>

      <div className={styles.section}>
        <h2>3. Jakie dane zbieramy</h2>
        <p>W ramach świadczenia usług możemy przetwarzać następujące dane:</p>
        <ul>
          <li>Zdjęcia przesłane w celu przetworzenia</li>
          <li>Dane techniczne (adres IP, typ przeglądarki)</li>
          <li>Informacje o sesji użytkownika</li>
        </ul>
      </div>

      <div className={styles.section}>
        <h2>4. Cel przetwarzania danych</h2>
        <p>Dane osobowe przetwarzamy w celu:</p>
        <ul>
          <li>Świadczenia usługi kadrowania zdjęć</li>
          <li>Zapewnienia bezpieczeństwa serwisu</li>
          <li>Analizy i ulepszania funkcjonalności</li>
        </ul>
      </div>

      <div className={styles.section}>
        <h2>5. Okres przechowywania danych</h2>
        <p>
          Przesłane zdjęcia są przetwarzane jedynie w celu realizacji usługi i usuwane automatycznie 
          po zakończeniu sesji. Dane techniczne mogą być przechowywane przez okres niezbędny do 
          zapewnienia bezpieczeństwa serwisu.
        </p>
      </div>

      <div className={styles.section}>
        <h2>6. Prawa użytkownika</h2>
        <p>Użytkownik ma prawo do:</p>
        <ul>
          <li>Dostępu do swoich danych osobowych</li>
          <li>Sprostowania nieprawidłowych danych</li>
          <li>Usunięcia danych osobowych</li>
          <li>Ograniczenia przetwarzania</li>
          <li>Przenoszenia danych</li>
          <li>Wniesienia sprzeciwu wobec przetwarzania</li>
        </ul>
      </div>

      <div className={styles.section}>
        <h2>7. Bezpieczeństwo danych</h2>
        <p>
          Stosujemy odpowiednie środki techniczne i organizacyjne w celu zapewnienia bezpieczeństwa 
          przetwarzanych danych osobowych, w tym ochrony przed nieuprawnionym dostępem, utratą, 
          zniszczeniem lub uszkodzeniem.
        </p>
      </div>

      <div className={styles.section}>
        <h2>8. Zmiany w Polityce Prywatności</h2>
        <p>
          Zastrzegamy sobie prawo do wprowadzania zmian w niniejszej Polityce Prywatności. 
          O wszelkich zmianach będziemy informować użytkowników poprzez publikację zaktualizowanej 
          wersji na stronie serwisu.
        </p>
      </div>

      <div className={styles.section}>
        <p><strong>Data ostatniej aktualizacji:</strong> 5 września 2025</p>
      </div>
    </div>
  );
};

export default PrivacyPage;

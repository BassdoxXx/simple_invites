// Verbesserte filterTable-Funktion, die auch Tischkarten filtert

// Helper function for debug templates
window.adminJsLoaded = function() {
  console.log("admin.js loaded successfully");
  return true;
};

function filterTable() {
  const searchInput = document.getElementById("searchInput").value.toLowerCase();
  const tischFilter = document.getElementById("tischFilter").value;
  
  // 1. Tabelle filtern
  const rows = document.querySelectorAll("#invitesTable tbody tr");
  let visibleVereine = new Set(); // Sammlung aller sichtbaren Vereine
  
  rows.forEach((row) => {
    const text = row.textContent.toLowerCase();
    const tischZelle = row.cells[1].textContent.trim();
    const verein = row.cells[0].textContent.trim(); // Name des Vereins speichern
    
    const textMatch = text.includes(searchInput);
    const tischMatch = !tischFilter || tischZelle.includes(tischFilter);
    
    const visible = (textMatch && tischMatch);
    row.style.display = visible ? "" : "none";
    
    // Wenn sichtbar, füge Verein zur Liste der sichtbaren Vereine hinzu
    if (visible) {
      visibleVereine.add(verein);
    }
  });
  
  // 2. Tischkarten filtern
  const tischCards = document.querySelectorAll(".tisch-card");
  
  if (searchInput) {
    // Wenn nach Text gesucht wird, zeige nur Tischkarten mit dem gesuchten Verein
    tischCards.forEach(card => {
      const vereinsItems = card.querySelectorAll("li");
      let showCard = false;
      
      // Prüfe, ob einer der Vereine in dieser Karte im Suchfilter enthalten ist
      vereinsItems.forEach(item => {
        const vereinName = item.querySelector(".font-medium").textContent.trim();
        if (vereinName.toLowerCase().includes(searchInput) || visibleVereine.has(vereinName)) {
          showCard = true;
          item.style.display = ""; // Zeige den Verein in der Karte
        } else {
          item.style.display = "none"; // Verstecke Vereine, die nicht dem Suchbegriff entsprechen
        }
      });
      
      card.style.display = showCard ? "" : "none";
    });
  } else if (tischFilter) {
    // Wenn nach Tischnummer gefiltert wird
    tischCards.forEach(card => {
      const tischNr = card.dataset.tisch;
      card.style.display = (tischNr === tischFilter) ? "" : "none";
    });
  } else {
    // Kein Filter aktiv, zeige alle Karten
    tischCards.forEach(card => {
      card.style.display = "";
      const vereinsItems = card.querySelectorAll("li");
      vereinsItems.forEach(item => {
        item.style.display = "";
      });
    });
  }
}

// Sortierfunktion für die Tabelle
document.addEventListener("DOMContentLoaded", function () {
  // Funktion zum Sortieren der Tabelle
  function sortTable(sortBy, ascending, headerElement = null) {
    const table = document.getElementById("invitesTable");
    const tbody = table.querySelector("tbody");
    const rows = Array.from(tbody.querySelectorAll("tr"));

    // Alle Sortierklassen entfernen und die richtige setzen
    document.querySelectorAll(".sortable").forEach((h) => {
      h.classList.remove("sort-asc", "sort-desc");
    });

    if (headerElement) {
      headerElement.classList.add(ascending ? "sort-asc" : "sort-desc");
    }

    // Zeilen sortieren
    rows.sort(function (a, b) {
      let valA, valB;

      if (sortBy === "verein") {
        valA = a.cells[0].textContent.toLowerCase();
        valB = b.cells[0].textContent.toLowerCase();
      } else if (sortBy === "tisch") {
        const tischA = a.cells[1].textContent;
        const tischB = b.cells[1].textContent;
        valA = tischA === "-" ? 9999 : parseInt(tischA) || 9999;
        valB = tischB === "-" ? 9999 : parseInt(tischB) || 9999;
      } else if (sortBy === "personen") {
        valA = parseInt(a.cells[5].textContent) || 0;
        valB = parseInt(b.cells[5].textContent) || 0;
      } else if (sortBy === "status") {
        valA = a.cells[4].textContent;
        valB = b.cells[4].textContent;
      }

      if (ascending) {
        return valA > valB ? 1 : -1;
      } else {
        return valA < valB ? 1 : -1;
      }
    });

    // Neu sortierte Zeilen einfügen
    rows.forEach(function (row) {
      tbody.appendChild(row);
    });
  }

  // Standardmäßig nach Vereinsnamen sortieren (aufsteigend)
  const vereinsHeader = document.querySelector('.sortable[data-sort="verein"]');
  if (vereinsHeader) {
    sortTable("verein", true, vereinsHeader);
  }

  // Event-Listener für Klicks auf Spaltenüberschriften
  document.querySelectorAll(".sortable").forEach(function (header) {
    header.addEventListener("click", function () {
      const sortBy = this.dataset.sort;
      // Sortierrichtung umschalten
      const ascending = !this.classList.contains("sort-asc");
      sortTable(sortBy, ascending, this);

    });
  });
});

// Kopieren-Funktion für Einladungslink
function copyToClipboard(btn) {
  const text = btn.dataset.link;
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(
      function () {
        showCopySuccess(btn);
      },
      function (err) {
        alert("Kopieren fehlgeschlagen: " + err);
      }
    );
  } else {
    // Fallback für unsichere Kontexte/ältere Browser
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed"; // Verhindert Scrollen
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    try {
      document.execCommand("copy");
      showCopySuccess(btn);
    } catch (err) {
      alert("Kopieren fehlgeschlagen: " + err);
    }
    document.body.removeChild(textarea);
  }
}

function showCopySuccess(btn) {
  const old = btn.innerHTML;
  btn.innerHTML = "✅";
  setTimeout(() => {
    btn.innerHTML = old;
  }, 1200);
}
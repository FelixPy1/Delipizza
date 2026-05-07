// ---- NOTES MODULE (localStorage) ----
document.addEventListener('DOMContentLoaded', function() {
  var NOTES_KEY = 'delipizza_notes';

  function getNotes() {
    try { return JSON.parse(localStorage.getItem(NOTES_KEY)) || []; }
    catch(e) { return []; }
  }

  function saveNotes(n) {
    localStorage.setItem(NOTES_KEY, JSON.stringify(n));
  }

  function escHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function renderNotes() {
    var all     = getNotes();
    var pending = all.filter(function(n){ return !n.paid; });
    var paid    = all.filter(function(n){ return  n.paid; });

    var pc = document.getElementById('notes-pending-count');
    var oc = document.getElementById('notes-paid-count');
    if (pc) pc.textContent = pending.length + ' pendiente' + (pending.length !== 1 ? 's' : '');
    if (oc) oc.textContent = paid.length    + ' pagado'    + (paid.length    !== 1 ? 's' : '');

    renderNoteList('notes-pending-list', 'notes-empty-pending', pending);
    renderNoteList('notes-paid-list',    'notes-empty-paid',    paid);
  }

  function renderNoteList(listId, emptyId, items) {
    var list  = document.getElementById(listId);
    var empty = document.getElementById(emptyId);
    if (!list || !empty) return;

    // Remove old items
    var existing = list.querySelectorAll('.note-item');
    existing.forEach(function(el){ el.remove(); });

    if (!items.length) {
      empty.style.display = 'flex';
      return;
    }
    empty.style.display = 'none';

    items.forEach(function(note) {
      var div = document.createElement('div');
      div.className = 'note-item' + (note.paid ? ' paid' : '');

      var d = new Date(note.createdAt);
      var ds = d.toLocaleDateString('es-DO', {timeZone: 'America/Santo_Domingo', day:'numeric', month:'short', hour:'2-digit', minute:'2-digit'});

      var statusHtml = note.paid
        ? '<div class="note-status">✓ Pagado</div>'
        : '<div class="note-date">' + ds + '</div>';

      div.innerHTML =
        '<input type="checkbox" class="note-checkbox" ' + (note.paid ? 'checked' : '') + '>' +
        '<div class="note-body">' +
          '<div class="note-text">' + escHtml(note.text) + '</div>' +
          statusHtml +
        '</div>' +
        '<button class="note-del" title="Eliminar">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">' +
            '<polyline points="3 6 5 6 21 6"/>' +
            '<path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>' +
            '<path d="M10 11v6m4-6v6"/><path d="M9 6V4h6v2"/>' +
          '</svg>' +
        '</button>';

      // Toggle paid/pending
      div.querySelector('.note-checkbox').addEventListener('change', function(e) {
        var ns = getNotes();
        var found = ns.find(function(x){ return x.id === note.id; });
        if (found) {
          found.paid = e.target.checked;
          saveNotes(ns);
          renderNotes();
        }
      });

      // Delete
      div.querySelector('.note-del').addEventListener('click', function() {
        saveNotes(getNotes().filter(function(x){ return x.id !== note.id; }));
        renderNotes();
        showAppToast('Nota eliminada');
      });

      list.appendChild(div);
    });
  }

  function addNote() {
    var input = document.getElementById('note-input');
    if (!input) return;
    var text = input.value.trim();
    if (!text) { input.focus(); return; }
    var ns = getNotes();
    ns.unshift({ id: Date.now().toString(), text: text, paid: false, createdAt: new Date().toISOString() });
    saveNotes(ns);
    input.value = '';
    renderNotes();
    showAppToast('Nota agregada');
  }

  // Use the app's showToast if available, else alert
  function showAppToast(msg) {
    if (typeof showToast === 'function') { showToast(msg); return; }
    var t = document.getElementById('toast');
    var m = document.getElementById('toast-msg');
    if (t && m) {
      m.textContent = msg;
      t.classList.add('show');
      clearTimeout(t._t);
      t._t = setTimeout(function(){ t.classList.remove('show'); }, 3000);
    }
  }

  var btnAdd   = document.getElementById('btn-add-note');
  var noteInp  = document.getElementById('note-input');
  var btnClear = document.getElementById('btn-clear-paid');

  if (btnAdd)   btnAdd.addEventListener('click', addNote);
  if (noteInp)  noteInp.addEventListener('keydown', function(e){ if (e.key === 'Enter') addNote(); });
  if (btnClear) btnClear.addEventListener('click', function() {
    saveNotes(getNotes().filter(function(n){ return !n.paid; }));
    renderNotes();
    showAppToast('Notas pagadas eliminadas');
  });

  // Re-render when navigating to notes view
  document.querySelectorAll('.nav-item').forEach(function(btn) {
    if (btn.dataset.view === 'notes') {
      btn.addEventListener('click', function() { setTimeout(renderNotes, 50); });
    }
  });

  // Initial render
  renderNotes();
});

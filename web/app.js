// Configurações
const API_BASE = window.location.port === "5000" ? "" : "http://localhost:5000";
let pollInterval = null;

// Estados locais para controle de dados e detecção de mudanças
let currentBooks = [];
let lastHistoryIds = new Set();
let isFirstLoad = true;

// Elementos do DOM
const elServerStatus = document.getElementById("status-server");
const elRfidStatus = document.getElementById("status-rfid");
const btnReset = document.getElementById("btn-reset");

const metricDisponiveis = document.getElementById("metric-disponiveis");
const metricEmprestados = document.getElementById("metric-emprestados");
const metricAtrasados = document.getElementById("metric-atrasados");
const cardAtraso = document.getElementById("metric-card-atraso");

const searchInput = document.getElementById("search-input");
const statusFilter = document.getElementById("status-filter");
const booksTableBody = document.querySelector("#books-table tbody");

const timelineHistory = document.getElementById("timeline-history");
const reviewsContainer = document.getElementById("reviews-container");

const rankingBorrowed = document.getElementById("ranking-borrowed");
const rankingRated = document.getElementById("ranking-rated");

// Barra de Notificação
const notificationBar = document.getElementById("notification-bar");
const notificationMessage = document.getElementById("notification-message");
const btnNotifyReview = document.getElementById("btn-notify-review");
const btnNotifyClose = document.getElementById("btn-notify-close");

// Modal de Avaliação
const reviewModal = document.getElementById("review-modal");
const btnModalClose = document.getElementById("btn-modal-close");
const btnModalCancel = document.getElementById("btn-modal-cancel");
const reviewForm = document.getElementById("review-form");
const formBookId = document.getElementById("form-book-id");
const formBookTitle = document.getElementById("form-book-title");
const formRatingValue = document.getElementById("form-rating-value");
const formStars = document.querySelectorAll("#form-stars .star");

// Inicialização
document.addEventListener("DOMContentLoaded", () => {
    // Iniciar busca de dados
    fetchDashboardData();
    pollInterval = setInterval(fetchDashboardData, 2000);

    // Eventos de Filtro
    searchInput.addEventListener("input", renderBooksTable);
    statusFilter.addEventListener("change", renderBooksTable);

    // Evento de Reset do Banco
    btnReset.addEventListener("click", resetDatabase);

    // Eventos do Modal
    btnModalClose.addEventListener("click", hideModal);
    btnModalCancel.addEventListener("click", hideModal);
    reviewForm.addEventListener("submit", submitReview);

    // Configurar seleção de estrelas interativa
    formStars.forEach(star => {
        star.addEventListener("click", (e) => {
            const rating = parseInt(e.target.getAttribute("data-rating"));
            setStarRating(rating);
        });
        star.addEventListener("mouseover", (e) => {
            const rating = parseInt(e.target.getAttribute("data-rating"));
            highlightStars(rating);
        });
        star.addEventListener("mouseout", () => {
            const rating = parseInt(formRatingValue.value);
            highlightStars(rating);
        });
    });

    // Eventos da Notificação
    btnNotifyClose.addEventListener("click", hideNotification);
    btnNotifyReview.addEventListener("click", () => {
        const bookId = btnNotifyReview.getAttribute("data-book-id");
        const bookTitle = btnNotifyReview.getAttribute("data-book-title");
        showModal(bookId, bookTitle);
        hideNotification();
    });
});

// Buscar dados do Dashboard
async function fetchDashboardData() {
    try {
        const response = await fetch(`${API_BASE}/api/dashboard`);
        if (!response.ok) throw new Error("Erro na resposta do servidor");
        const data = await response.json();

        // Atualizar status de conexões
        updateConnectionStatus(true, data.serial_connected);

        // Atualizar Métricas
        metricDisponiveis.textContent = data.counts.disponiveis;
        metricEmprestados.textContent = data.counts.emprestados;
        metricAtrasados.textContent = data.counts.atrasados;

        if (data.counts.atrasados > 0) {
            cardAtraso.classList.add("has-atraso");
        } else {
            cardAtraso.classList.remove("has-atraso");
        }

        // Salvar livros e renderizar tabela
        // O ranking_emprestimos traz todos os livros cadastrados junto com a contagem de empréstimos
        currentBooks = data.ranking_emprestimos || [];
        renderBooksTable();

        // Renderizar Histórico e verificar Devoluções recentes
        renderHistory(data.historico_recente);

        // Renderizar Feedbacks
        renderReviews(data.avaliacoes);

        // Renderizar Rankings
        renderRankings(data.ranking_emprestimos, data.ranking_avaliacoes);

        isFirstLoad = false;
    } catch (error) {
        console.error("Erro ao buscar dados do dashboard:", error);
        updateConnectionStatus(false, false);
    }
}

// Atualizar indicadores de conexão
function updateConnectionStatus(serverOnline, rfidConnected) {
    if (serverOnline) {
        elServerStatus.className = "status-pill online";
        elServerStatus.querySelector(".status-label").textContent = "Servidor: Online";
    } else {
        elServerStatus.className = "status-pill offline";
        elServerStatus.querySelector(".status-label").textContent = "Servidor: Offline";
    }

    if (rfidConnected) {
        elRfidStatus.className = "status-pill online";
        elRfidStatus.querySelector(".status-label").textContent = "RFID Arduino: Conectado";
    } else {
        elRfidStatus.className = "status-pill offline";
        elRfidStatus.querySelector(".status-label").textContent = "RFID Arduino: Desconectado";
    }
}

// Renderizar Tabela de Livros
function renderBooksTable() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const filterValue = statusFilter.value;

    const filtered = currentBooks.filter(book => {
        const matchesSearch = book.titulo.toLowerCase().includes(searchTerm) || 
                              book.autor.toLowerCase().includes(searchTerm);
        const matchesStatus = filterValue === "todos" || book.status === filterValue;
        return matchesSearch && matchesStatus;
    });

    if (filtered.length === 0) {
        booksTableBody.innerHTML = `<tr><td colspan="5" class="table-placeholder">Nenhum livro localizado.</td></tr>`;
        return;
    }

    booksTableBody.innerHTML = filtered.map(book => {
        let statusClass = "badge-disponivel";
        let statusLabel = "Disponível";
        
        if (book.status === "emprestado") {
            statusClass = "badge-emprestado";
            statusLabel = "Emprestado";
        } else if (book.status === "atrasado") {
            statusClass = "badge-atrasado";
            statusLabel = "Em Atraso";
        }

        return `
            <tr>
                <td style="font-weight: 600; color: #fff;">${book.titulo}</td>
                <td>${book.autor}</td>
                <td style="font-family: monospace; font-size: 0.8rem; color: var(--text-muted);">${book.id_rfid}</td>
                <td><span class="badge ${statusClass}">${statusLabel}</span></td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="showModal('${book.id_rfid}', '${book.titulo.replace(/'/g, "\\'")}')">
                        ⭐ Avaliar
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// Renderizar Histórico
function renderHistory(history) {
    if (!history || history.length === 0) {
        timelineHistory.innerHTML = `<p class="timeline-placeholder">Nenhuma movimentação registrada.</p>`;
        lastHistoryIds.clear();
        return;
    }

    // Verificar transições (devoluções recentes) para notificação de feedback
    const currentHistoryIds = new Set();
    history.forEach(item => {
        currentHistoryIds.add(item.id);
        
        // Se não for a primeira carga da página e detectarmos um item que foi finalizado recentemente
        if (!isFirstLoad && !lastHistoryIds.has(item.id) && item.status === "finalizado") {
            showReturnNotification(item.livro_id, item.livro_titulo, item.aluno_nome);
        }
    });

    // Atualizar o cache de IDs históricos
    lastHistoryIds = currentHistoryIds;

    timelineHistory.innerHTML = history.map(item => {
        let dotClass = "ativo";
        let actionLabel = "emprestou";
        let dateToShow = item.data_emprestimo;

        if (item.status === "finalizado") {
            dotClass = "finalizado";
            actionLabel = "devolveu";
            dateToShow = item.data_devolucao || item.data_emprestimo;
        } else if (item.status === "atrasado") {
            dotClass = "atrasado";
            actionLabel = "atrasou na devolução de";
        }

        return `
            <div class="timeline-item">
                <div class="timeline-dot-container">
                    <span class="timeline-dot ${dotClass}"></span>
                    <span class="timeline-line"></span>
                </div>
                <div class="timeline-content">
                    <div class="timeline-info">
                        <p><strong>${item.aluno_nome}</strong> ${actionLabel} <em>"${item.livro_titulo}"</em></p>
                        <span>Matrícula: ${item.aluno_matricula}</span>
                    </div>
                    <span class="timeline-date">${formatDate(dateToShow)}</span>
                </div>
            </div>
        `;
    }).join('');
}

// Renderizar Avaliações
function renderReviews(reviews) {
    if (!reviews || reviews.length === 0) {
        reviewsContainer.innerHTML = `<p class="reviews-placeholder">Nenhum feedback registrado ainda.</p>`;
        return;
    }

    reviewsContainer.innerHTML = reviews.map(rev => {
        const stars = "★".repeat(rev.nota) + "☆".repeat(5 - rev.nota);
        return `
            <div class="review-card">
                <div class="review-header">
                    <span class="review-book-title" title="${rev.livro_titulo}">${rev.livro_titulo}</span>
                    <span class="stars-display">${stars}</span>
                </div>
                <p class="review-comment">"${rev.comentario}"</p>
            </div>
        `;
    }).join('');
}

// Renderizar Rankings
function renderRankings(byBorrowed, byRated) {
    // 1. Mais Emprestados
    if (!byBorrowed || byBorrowed.length === 0) {
        rankingBorrowed.innerHTML = `<li class="ranking-placeholder">Nenhum dado disponível.</li>`;
    } else {
        // Ordenar desc por empréstimos
        const sortedBorrowed = [...byBorrowed].sort((a, b) => b.emprestimos_count - a.emprestimos_count).slice(0, 3);
        rankingBorrowed.innerHTML = sortedBorrowed.map((book, idx) => {
            const rankClass = idx === 0 ? "rank-1" : (idx === 1 ? "rank-2" : "rank-3");
            return `
                <li class="ranking-item ${rankClass}">
                    <div class="ranking-position">${idx + 1}</div>
                    <div class="ranking-details">
                        <div class="ranking-name">${book.titulo}</div>
                        <div class="ranking-meta">${book.emprestimos_count} empréstimo(s)</div>
                    </div>
                </li>
            `;
        }).join('');
    }

    // 2. Melhor Avaliados
    if (!byRated || byRated.length === 0) {
        rankingRated.innerHTML = `<li class="ranking-placeholder">Nenhuma avaliação cadastrada.</li>`;
    } else {
        const top3Rated = byRated.slice(0, 3);
        rankingRated.innerHTML = top3Rated.map((book, idx) => {
            const rankClass = idx === 0 ? "rank-1" : (idx === 1 ? "rank-2" : "rank-3");
            const ratingFormatted = parseFloat(book.nota_media).toFixed(1);
            return `
                <li class="ranking-item ${rankClass}">
                    <div class="ranking-position">${idx + 1}</div>
                    <div class="ranking-details">
                        <div class="ranking-name">${book.titulo}</div>
                        <div class="ranking-meta">⭐ ${ratingFormatted} (${book.avaliacoes_count} votos)</div>
                    </div>
                </li>
            `;
        }).join('');
    }
}

// Formatar Data para exibição amigável
function formatDate(dateStr) {
    if (!dateStr) return "";
    try {
        // Formato original: YYYY-MM-DD HH:MM:SS
        const parts = dateStr.split(" ");
        const timePart = parts[1] || "";
        const timeSubparts = timePart.split(":");
        return `${timeSubparts[0]}:${timeSubparts[1]}`; // Retorna apenas HH:MM
    } catch (e) {
        return dateStr;
    }
}

// Notificação de Devolução Recente
function showReturnNotification(bookId, bookTitle, studentName) {
    notificationMessage.innerHTML = `🎉 <strong>${studentName}</strong> devolveu o livro <strong>"${bookTitle}"</strong>!`;
    btnNotifyReview.setAttribute("data-book-id", bookId);
    btnNotifyReview.setAttribute("data-book-title", bookTitle);
    notificationBar.classList.remove("hidden");
    
    // Auto-ocultar após 12 segundos
    setTimeout(hideNotification, 12000);
}

function hideNotification() {
    notificationBar.classList.add("hidden");
}

// Modal de Avaliação
function showModal(bookId, bookTitle) {
    formBookId.value = bookId;
    formBookTitle.value = bookTitle;
    setStarRating(5); // Default 5 estrelas
    document.getElementById("form-comment").value = "";
    reviewModal.classList.remove("hidden");
}

function hideModal() {
    reviewModal.classList.add("hidden");
}

function setStarRating(rating) {
    formRatingValue.value = rating;
    highlightStars(rating);
}

function highlightStars(rating) {
    formStars.forEach(star => {
        const starRating = parseInt(star.getAttribute("data-rating"));
        if (starRating <= rating) {
            star.classList.add("selected");
        } else {
            star.classList.remove("selected");
        }
    });
}

// Salvar Avaliação via API
async function submitReview(e) {
    e.preventDefault();
    const bookId = formBookId.value;
    const rating = parseInt(formRatingValue.value);
    const comment = document.getElementById("form-comment").value;

    try {
        const response = await fetch(`${API_BASE}/api/avaliar`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                livro_id: bookId,
                nota: rating,
                comentario: comment
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || "Erro ao salvar avaliação");
        }

        hideModal();
        fetchDashboardData(); // Recarregar dados do dashboard
        alert("Avaliação salva com sucesso! Obrigado pelo feedback.");
    } catch (error) {
        alert("Falha ao salvar avaliação: " + error.message);
    }
}

// Resetar o Banco de Dados
async function resetDatabase() {
    if (!confirm("Tem certeza que deseja resetar o banco de dados? Todos os empréstimos e avaliações serão deletados.")) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/reset`, {
            method: "POST"
        });

        if (!response.ok) throw new Error("Falha ao resetar");
        
        alert("Banco de dados reinicializado com sucesso!");
        fetchDashboardData();
    } catch (error) {
        alert("Erro ao resetar o banco de dados: " + error.message);
    }
}

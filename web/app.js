const API_BASE = window.location.port === "5000" ? "" : "http://localhost:5000";
let pollInterval = null;

let currentBooks = [];
let lastHistoryIds = new Set();
let isFirstLoad = true;
let mockEnabled = false;

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

const notificationBar = document.getElementById("notification-bar");
const notificationMessage = document.getElementById("notification-message");
const btnNotifyReview = document.getElementById("btn-notify-review");
const btnNotifyClose = document.getElementById("btn-notify-close");

const reviewModal = document.getElementById("review-modal");
const btnModalClose = document.getElementById("btn-modal-close");
const btnModalCancel = document.getElementById("btn-modal-cancel");
const reviewForm = document.getElementById("review-form");
const formBookId = document.getElementById("form-book-id");
const formBookTitle = document.getElementById("form-book-title");
const formRatingValue = document.getElementById("form-rating-value");
const formStars = document.querySelectorAll("#form-stars .star");

const mockPanel = document.getElementById("mock-panel");
const mockPanelSubtitle = document.getElementById("mock-panel-subtitle");
const mockStudents = document.getElementById("mock-students");
const mockBooks = document.getElementById("mock-books");
const mockResult = document.getElementById("mock-result");

document.addEventListener("DOMContentLoaded", () => {
    fetchDashboardData();
    pollInterval = setInterval(fetchDashboardData, 2000);

    searchInput.addEventListener("input", renderBooksTable);
    statusFilter.addEventListener("change", renderBooksTable);
    btnReset.addEventListener("click", resetDatabase);

    btnModalClose.addEventListener("click", hideModal);
    btnModalCancel.addEventListener("click", hideModal);
    reviewForm.addEventListener("submit", submitReview);

    formStars.forEach(star => {
        star.addEventListener("click", event => {
            const rating = parseInt(event.target.getAttribute("data-rating"), 10);
            setStarRating(rating);
        });
        star.addEventListener("mouseover", event => {
            const rating = parseInt(event.target.getAttribute("data-rating"), 10);
            highlightStars(rating);
        });
        star.addEventListener("mouseout", () => {
            const rating = parseInt(formRatingValue.value, 10);
            highlightStars(rating);
        });
    });

    btnNotifyClose.addEventListener("click", hideNotification);
    btnNotifyReview.addEventListener("click", () => {
        const bookId = btnNotifyReview.getAttribute("data-book-id");
        const bookTitle = btnNotifyReview.getAttribute("data-book-title");
        showModal(bookId, bookTitle);
        hideNotification();
    });
});

async function fetchDashboardData() {
    try {
        const response = await fetch(`${API_BASE}/api/dashboard`);
        if (!response.ok) {
            throw new Error("Erro na resposta do servidor");
        }

        const data = await response.json();

        updateConnectionStatus(true, data.serial_connected, data.serial_mode);

        metricDisponiveis.textContent = data.counts.disponiveis;
        metricEmprestados.textContent = data.counts.emprestados;
        metricAtrasados.textContent = data.counts.atrasados;

        if (data.counts.atrasados > 0) {
            cardAtraso.classList.add("has-atraso");
        } else {
            cardAtraso.classList.remove("has-atraso");
        }

        currentBooks = data.ranking_emprestimos || [];
        renderBooksTable();
        renderHistory(data.historico_recente);
        renderReviews(data.avaliacoes);
        renderRankings(data.ranking_emprestimos, data.ranking_avaliacoes);
        renderMockPanel(data);

        isFirstLoad = false;
    } catch (error) {
        console.error("Erro ao buscar dados do dashboard:", error);
        updateConnectionStatus(false, false, "hardware");
    }
}

function updateConnectionStatus(serverOnline, rfidConnected, serialMode) {
    if (serverOnline) {
        elServerStatus.className = "status-pill online";
        elServerStatus.querySelector(".status-label").textContent = "Servidor: Online";
    } else {
        elServerStatus.className = "status-pill offline";
        elServerStatus.querySelector(".status-label").textContent = "Servidor: Offline";
    }

    if (rfidConnected) {
        elRfidStatus.className = "status-pill online";
        elRfidStatus.querySelector(".status-label").textContent =
            serialMode === "mock" ? "RFID: Mock ativo" : "RFID Arduino: Conectado";
    } else {
        elRfidStatus.className = "status-pill offline";
        elRfidStatus.querySelector(".status-label").textContent = "RFID Arduino: Desconectado";
    }
}

function renderBooksTable() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const filterValue = statusFilter.value;

    const filtered = currentBooks.filter(book => {
        const matchesSearch =
            book.titulo.toLowerCase().includes(searchTerm) ||
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
        let statusLabel = "Disponivel";

        if (book.status === "emprestado") {
            statusClass = "badge-emprestado";
            statusLabel = "Emprestado";
        } else if (book.status === "atrasado") {
            statusClass = "badge-atrasado";
            statusLabel = "Em atraso";
        }

        return `
            <tr>
                <td style="font-weight: 600; color: #fff;">${book.titulo}</td>
                <td>${book.autor}</td>
                <td style="font-family: monospace; font-size: 0.8rem; color: var(--text-muted);">${book.id_rfid}</td>
                <td><span class="badge ${statusClass}">${statusLabel}</span></td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="showModal('${book.id_rfid}', '${book.titulo.replace(/'/g, "\\'")}')">
                        Avaliar
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

function renderHistory(history) {
    if (!history || history.length === 0) {
        timelineHistory.innerHTML = `<p class="timeline-placeholder">Nenhuma movimentacao registrada.</p>`;
        lastHistoryIds.clear();
        return;
    }

    const currentHistoryIds = new Set();
    history.forEach(item => {
        currentHistoryIds.add(item.id);

        if (!isFirstLoad && !lastHistoryIds.has(item.id) && item.status === "finalizado") {
            showReturnNotification(item.livro_id, item.livro_titulo, item.aluno_nome);
        }
    });

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
            actionLabel = "atrasou na devolucao de";
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
                        <span>Matricula: ${item.aluno_matricula}</span>
                    </div>
                    <span class="timeline-date">${formatDate(dateToShow)}</span>
                </div>
            </div>
        `;
    }).join("");
}

function renderReviews(reviews) {
    if (!reviews || reviews.length === 0) {
        reviewsContainer.innerHTML = `<p class="reviews-placeholder">Nenhum feedback registrado ainda.</p>`;
        return;
    }

    reviewsContainer.innerHTML = reviews.map(review => {
        const stars = "★".repeat(review.nota) + "☆".repeat(5 - review.nota);
        return `
            <div class="review-card">
                <div class="review-header">
                    <span class="review-book-title" title="${review.livro_titulo}">${review.livro_titulo}</span>
                    <span class="stars-display">${stars}</span>
                </div>
                <p class="review-comment">"${review.comentario}"</p>
            </div>
        `;
    }).join("");
}

function renderRankings(byBorrowed, byRated) {
    if (!byBorrowed || byBorrowed.length === 0) {
        rankingBorrowed.innerHTML = `<li class="ranking-placeholder">Nenhum dado disponivel.</li>`;
    } else {
        const sortedBorrowed = [...byBorrowed]
            .sort((a, b) => b.emprestimos_count - a.emprestimos_count)
            .slice(0, 3);

        rankingBorrowed.innerHTML = sortedBorrowed.map((book, index) => {
            const rankClass = index === 0 ? "rank-1" : (index === 1 ? "rank-2" : "rank-3");
            return `
                <li class="ranking-item ${rankClass}">
                    <div class="ranking-position">${index + 1}</div>
                    <div class="ranking-details">
                        <div class="ranking-name">${book.titulo}</div>
                        <div class="ranking-meta">${book.emprestimos_count} emprestimo(s)</div>
                    </div>
                </li>
            `;
        }).join("");
    }

    if (!byRated || byRated.length === 0) {
        rankingRated.innerHTML = `<li class="ranking-placeholder">Nenhuma avaliacao cadastrada.</li>`;
    } else {
        rankingRated.innerHTML = byRated.slice(0, 3).map((book, index) => {
            const rankClass = index === 0 ? "rank-1" : (index === 1 ? "rank-2" : "rank-3");
            const ratingFormatted = parseFloat(book.nota_media).toFixed(1);
            return `
                <li class="ranking-item ${rankClass}">
                    <div class="ranking-position">${index + 1}</div>
                    <div class="ranking-details">
                        <div class="ranking-name">${book.titulo}</div>
                        <div class="ranking-meta">★ ${ratingFormatted} (${book.avaliacoes_count} votos)</div>
                    </div>
                </li>
            `;
        }).join("");
    }
}

function renderMockPanel(data) {
    mockEnabled = Boolean(data.mock_enabled);

    if (!mockEnabled) {
        mockPanel.classList.add("hidden");
        return;
    }

    mockPanel.classList.remove("hidden");
    mockPanelSubtitle.textContent = `Porta atual: ${data.serial_mode}. Timeout de atraso: ${data.loan_timeout_seconds}s.`;

    const alunos = (data.mock_data && data.mock_data.alunos) || [];
    const livros = (data.mock_data && data.mock_data.livros) || [];

    mockStudents.innerHTML = alunos.map(aluno => `
        <button class="btn btn-secondary btn-sm mock-action-button"
            onclick="simulateScan('ALUNO', '${aluno.id_rfid}')">
            ${aluno.nome}
        </button>
    `).join("");

    mockBooks.innerHTML = livros.map(livro => `
        <button class="btn btn-secondary btn-sm mock-action-button"
            onclick="simulateScan('LIVRO', '${livro.id_rfid}')">
            ${livro.titulo}
        </button>
    `).join("");
}

async function simulateScan(type, rfidId) {
    try {
        const response = await fetch(`${API_BASE}/api/mock/scan`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                type,
                rfid_id: rfidId
            })
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || "Falha ao simular leitura");
        }

        mockResult.className = result.success ? "mock-result success" : "mock-result error";
        mockResult.textContent = `${result.response} | ${result.message}`;
        await fetchDashboardData();
    } catch (error) {
        mockResult.className = "mock-result error";
        mockResult.textContent = error.message;
    }
}

function formatDate(dateStr) {
    if (!dateStr) {
        return "";
    }

    try {
        const parts = dateStr.split(" ");
        const timePart = parts[1] || "";
        const timeSubparts = timePart.split(":");
        return `${timeSubparts[0]}:${timeSubparts[1]}`;
    } catch (error) {
        return dateStr;
    }
}

function showReturnNotification(bookId, bookTitle, studentName) {
    notificationMessage.innerHTML = `<strong>${studentName}</strong> devolveu o livro <strong>"${bookTitle}"</strong>.`;
    btnNotifyReview.setAttribute("data-book-id", bookId);
    btnNotifyReview.setAttribute("data-book-title", bookTitle);
    notificationBar.classList.remove("hidden");

    setTimeout(hideNotification, 12000);
}

function hideNotification() {
    notificationBar.classList.add("hidden");
}

function showModal(bookId, bookTitle) {
    formBookId.value = bookId;
    formBookTitle.value = bookTitle;
    setStarRating(5);
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
        const starRating = parseInt(star.getAttribute("data-rating"), 10);
        if (starRating <= rating) {
            star.classList.add("selected");
        } else {
            star.classList.remove("selected");
        }
    });
}

async function submitReview(event) {
    event.preventDefault();
    const bookId = formBookId.value;
    const rating = parseInt(formRatingValue.value, 10);
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
            throw new Error(err.error || "Erro ao salvar avaliacao");
        }

        hideModal();
        fetchDashboardData();
        alert("Avaliacao salva com sucesso.");
    } catch (error) {
        alert(`Falha ao salvar avaliacao: ${error.message}`);
    }
}

async function resetDatabase() {
    if (!confirm("Tem certeza que deseja resetar o banco de dados?")) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/reset`, {
            method: "POST"
        });

        if (!response.ok) {
            throw new Error("Falha ao resetar");
        }

        mockResult.className = "mock-result";
        mockResult.textContent = "Banco reinicializado com os dados padrao.";
        alert("Banco de dados reinicializado com sucesso.");
        fetchDashboardData();
    } catch (error) {
        alert(`Erro ao resetar o banco de dados: ${error.message}`);
    }
}

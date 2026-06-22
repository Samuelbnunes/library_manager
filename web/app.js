const API_BASE = window.location.port === "5000" ? "" : "http://localhost:5000";

let currentBooks = [];
let currentReviews = [];
let currentActiveStudent = null;
let lastHistoryIds = new Set();
let isFirstLoad = true;
let isReviewReadonly = false;
let activeReviewMode = "create";
let activeReviewId = null;
let originalReviewSnapshot = null;
let activeReviewerName = null;

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

const activeStudentCard = document.getElementById("active-student-card");
const overdueSummaryCard = document.getElementById("overdue-summary-card");
const overdueList = document.getElementById("overdue-list");
const eventsList = document.getElementById("events-list");
const timelineHistory = document.getElementById("timeline-history");
const reviewsContainer = document.getElementById("reviews-container");
const rankingBorrowed = document.getElementById("ranking-borrowed");
const rankingRated = document.getElementById("ranking-rated");

const notificationBar = document.getElementById("notification-bar");
const notificationMessage = document.getElementById("notification-message");
const btnNotifyReview = document.getElementById("btn-notify-review");
const btnNotifyClose = document.getElementById("btn-notify-close");
const successToast = document.getElementById("success-toast");
let successToastTimeout = null;

const reviewModal = document.getElementById("review-modal");
const reviewModalTitle = reviewModal.querySelector(".modal-header h2");
const btnModalClose = document.getElementById("btn-modal-close");
const btnModalCancel = document.getElementById("btn-modal-cancel");
const reviewForm = document.getElementById("review-form");
const btnReviewSubmit = reviewForm.querySelector("button[type='submit']");
const formBookId = document.getElementById("form-book-id");
const formRatingValue = document.getElementById("form-rating-value");
const formStars = document.querySelectorAll("#form-stars .star");
const ratingError = document.getElementById("rating-error");
const formComment = document.getElementById("form-comment");
const commentLabel = document.getElementById("comment-label");
const commentCounter = document.getElementById("comment-counter");
const reviewBookCover = document.getElementById("review-book-cover");
const reviewBookPreviewTitle = document.getElementById("review-book-preview-title");
const reviewBookPreviewAuthor = document.getElementById("review-book-preview-author");
const reviewAuthorName = document.getElementById("review-author-name");

const mockPanel = document.getElementById("mock-panel");
const mockPanelSubtitle = document.getElementById("mock-panel-subtitle");
const mockStudents = document.getElementById("mock-students");
const mockBooks = document.getElementById("mock-books");
const mockGeneric = document.getElementById("mock-generic");
const mockResult = document.getElementById("mock-result");

const pageBadges = document.querySelectorAll("[data-page-target]");
const pagePanels = document.querySelectorAll("[data-page-section]");

const bookCovers = {
    "63 6F 2C FE": {
        src: "assets/books/metamorfose.png",
        author: "Franz Kafka",
    },
    "43 82 51 FE": {
        src: "assets/books/diario-de-um-banana-rodrick.png",
        author: "Jeff Kinney",
    },
    "73 BD BF 02": {
        src: "assets/books/odisseia.png",
        author: "Homero",
    },
    "63 34 63 FB": {
        src: "assets/books/hamlet.png",
        author: "William Shakespeare",
    },
};

document.addEventListener("DOMContentLoaded", () => {
    fetchDashboardData();
    setInterval(fetchDashboardData, 2000);

    searchInput.addEventListener("input", renderBooksTable);
    statusFilter.addEventListener("change", renderBooksTable);
    btnReset.addEventListener("click", resetDatabase);

    btnModalClose.addEventListener("click", hideModal);
    btnModalCancel.addEventListener("click", hideModal);
    reviewForm.addEventListener("submit", submitReview);
    formComment.addEventListener("invalid", () => {
        formComment.setCustomValidity(formComment.dataset.requiredMessage);
        formComment.classList.add("field-error");
    });
    formComment.addEventListener("input", () => {
        formComment.setCustomValidity("");
        formComment.classList.remove("field-error");
        updateCommentCounter();
        updateReviewEditActions();
    });

    formStars.forEach(star => {
        star.addEventListener("click", event => {
            if (isReviewReadonly) {
                return;
            }
            const rating = parseInt(event.target.getAttribute("data-rating"), 10);
            setStarRating(rating);
            updateReviewEditActions();
        });
        star.addEventListener("mouseover", event => {
            if (isReviewReadonly) {
                return;
            }
            const rating = parseInt(event.target.getAttribute("data-rating"), 10);
            highlightStars(rating);
        });
        star.addEventListener("mouseout", () => {
            if (isReviewReadonly) {
                return;
            }
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

    pageBadges.forEach(badge => {
        badge.addEventListener("click", () => {
            showPage(badge.getAttribute("data-page-target"));
        });
    });
});

function showPage(pageName) {
    pageBadges.forEach(badge => {
        badge.classList.toggle("active", badge.getAttribute("data-page-target") === pageName);
    });

    pagePanels.forEach(panel => {
        panel.classList.toggle("active", panel.getAttribute("data-page-section") === pageName);
    });
}

async function fetchDashboardData() {
    try {
        const response = await fetch(`${API_BASE}/api/dashboard`);
        if (!response.ok) {
            throw new Error("Erro na resposta do servidor.");
        }

        const data = await response.json();
        updateConnectionStatus(true, data.serial_connected, data.serial_mode);
        updateMetrics(data.counts);

        currentBooks = data.acervo || [];
        currentActiveStudent = data.active_student || null;
        renderBooksTable();
        renderActiveStudent(data.active_student);
        renderOverdueSummary(data.atrasos || [], data.loan_timeout_seconds);
        renderOverdueList(data.atrasos || []);
        renderEvents(data.eventos || []);
        renderHistory(data.historico_recente || []);
        renderReviews(data.avaliacoes || []);
        renderRankings(data.ranking_emprestimos || [], data.ranking_avaliacoes || []);
        renderMockPanel(data);

        isFirstLoad = false;
    } catch (error) {
        console.error("Erro ao buscar dados do dashboard:", error);
        updateConnectionStatus(false, false, "hardware");
        activeStudentCard.className = "state-card error";
        activeStudentCard.textContent = "Nao foi possivel carregar os dados do sistema.";
    }
}

function updateConnectionStatus(serverOnline, rfidConnected, serialMode) {
    elServerStatus.className = serverOnline ? "status-pill online" : "status-pill offline";
    elServerStatus.querySelector(".status-label").textContent = serverOnline
        ? "Servidor: Online"
        : "Servidor: Offline";

    if (rfidConnected) {
        elRfidStatus.className = "status-pill online";
        elRfidStatus.querySelector(".status-label").textContent =
            serialMode === "mock"
                ? "RFID: MOCK ativo"
                : "RFID Arduino: Conectado";
    } else {
        elRfidStatus.className = "status-pill offline";
        elRfidStatus.querySelector(".status-label").textContent = "RFID Arduino: Desconectado";
    }
}

function updateMetrics(counts) {
    metricDisponiveis.textContent = counts.disponiveis;
    metricEmprestados.textContent = counts.emprestados;
    metricAtrasados.textContent = counts.atrasados;

    if (counts.atrasados > 0) {
        cardAtraso.classList.add("has-atraso");
    } else {
        cardAtraso.classList.remove("has-atraso");
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
        booksTableBody.innerHTML = `<tr><td colspan="6" class="table-placeholder">Nenhum livro localizado.</td></tr>`;
        return;
    }

    booksTableBody.innerHTML = filtered.map(book => {
        const statusData = getStatusData(book.status);
        const borrower = book.aluno_nome || "Sem aluno vinculado";
        const coverData = bookCovers[book.id_rfid];
        const coverMarkup = coverData
            ? `<img src="${coverData.src}" alt="Capa do livro ${book.titulo}" class="table-book-cover">`
            : "";
        return `
            <tr>
                <td>
                    <div class="table-book-title">
                        ${coverMarkup}
                        <span>${book.titulo}</span>
                    </div>
                </td>
                <td>${book.autor}</td>
                <td style="font-family: monospace; font-size: 0.8rem; color: var(--text-muted);">${book.id_rfid}</td>
                <td><span class="badge ${statusData.className}">${statusData.label}</span></td>
                <td>${borrower}</td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="showModal('${book.id_rfid}', '${book.titulo.replace(/'/g, "\\'")}')">
                        Avaliar
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

function renderActiveStudent(activeStudent) {
    if (!activeStudent) {
        activeStudentCard.className = "state-card neutral";
        activeStudentCard.innerHTML = "Nenhum aluno identificado no momento.";
        return;
    }

    activeStudentCard.className = "state-card success";
    activeStudentCard.innerHTML = `
        <strong>${activeStudent.nome}</strong><br>
        Matricula ${activeStudent.matricula}<br>
        Janela de leitura ativa por mais ${activeStudent.remaining_seconds}s.
    `;
}

function renderOverdueSummary(overdueItems, timeoutSeconds) {
    if (!overdueItems.length) {
        overdueSummaryCard.className = "state-card neutral";
        overdueSummaryCard.innerHTML = "Nenhum emprestimo atrasado agora.";
        return;
    }

    overdueSummaryCard.className = "state-card error";
    overdueSummaryCard.innerHTML = `
        <strong>${overdueItems.length} emprestimo(s) em atraso.</strong><br>
        Regra ativa: vencimento apos ${timeoutSeconds}s para demonstracao.
    `;
}

function renderOverdueList(overdueItems) {
    if (!overdueItems.length) {
        overdueList.innerHTML = `<p class="timeline-placeholder">Nenhum atraso registrado.</p>`;
        return;
    }

    overdueList.innerHTML = overdueItems.map(item => `
        <article class="stack-item danger">
            <strong>${item.livro_titulo}</strong>
            <span>Aluno: ${item.aluno_nome} (${item.aluno_matricula})</span>
            <span>Emprestado em: ${item.data_emprestimo}</span>
            <span>Atraso atual: ${item.seconds_overdue}s</span>
        </article>
    `).join("");
}

function renderEvents(events) {
    if (!events.length) {
        eventsList.innerHTML = `<p class="ranking-placeholder">Nenhum evento registrado.</p>`;
        return;
    }

    eventsList.innerHTML = events.map(event => `
        <article class="event-item ${event.status}">
            <div class="event-meta">
                <strong>${formatEventType(event.event_type)}</strong>
                <span>${formatDate(event.created_at)}</span>
            </div>
            <p>${event.message}</p>
            <span class="event-foot">${event.source} ${event.rfid_id ? `| RFID ${event.rfid_id}` : ""}</span>
        </article>
    `).join("");
}

function renderHistory(history) {
    if (!history.length) {
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
            actionLabel = "esta com atraso em";
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
    if (!reviews.length) {
        currentReviews = [];
        reviewsContainer.innerHTML = `<p class="reviews-placeholder">Nenhum feedback registrado ainda.</p>`;
        return;
    }

    currentReviews = reviews;
    reviewsContainer.innerHTML = reviews.map((review, reviewIndex) => {
        const reviewerName = review.aluno_nome || "Avaliador nao identificado";
        const stars = "★".repeat(review.nota) + "☆".repeat(5 - review.nota);
        const coverData = bookCovers[review.livro_id];
        const coverMarkup = coverData
            ? `<img src="${coverData.src}" alt="Capa do livro ${review.livro_titulo}" class="review-book-cover-small">`
            : "";
        return `
            <button type="button" class="review-card review-card-clickable" data-review-index="${reviewIndex}" aria-label="Abrir avaliacao de ${review.livro_titulo}">
                <div class="review-card-main">
                    ${coverMarkup}
                    <div class="review-card-content">
                        <div class="review-header">
                            <span class="review-book-title" title="${review.livro_titulo}">${review.livro_titulo}</span>
                            <span class="stars-display">${stars}</span>
                        </div>
                        <span class="reviewer-name">Avaliado por ${reviewerName}</span>
                        <p class="review-comment">"${review.comentario}"</p>
                    </div>
                </div>
            </button>
        `;
    }).join("");

    reviewsContainer.querySelectorAll("[data-review-index]").forEach(card => {
        card.addEventListener("click", () => {
            openExistingReview(Number(card.dataset.reviewIndex));
        });
    });
}

function renderRankings(byBorrowed, byRated) {
    if (!byBorrowed.length) {
        rankingBorrowed.innerHTML = `<li class="ranking-placeholder">Nenhum dado disponivel.</li>`;
    } else {
        rankingBorrowed.innerHTML = [...byBorrowed]
            .sort((a, b) => b.emprestimos_count - a.emprestimos_count)
            .slice(0, 3)
            .map((book, index) => {
                const coverData = bookCovers[book.id_rfid];
                const coverMarkup = coverData
                    ? `<img src="${coverData.src}" alt="Capa do livro ${book.titulo}" class="ranking-book-cover">`
                    : "";
                return `
                    <li class="ranking-item rank-${index + 1}">
                        <div class="ranking-position">${index + 1}</div>
                        ${coverMarkup}
                        <div class="ranking-details">
                            <div class="ranking-name">${book.titulo}</div>
                            <div class="ranking-meta">${book.emprestimos_count} emprestimo(s)</div>
                        </div>
                    </li>
                `;
            }).join("");
    }

    if (!byRated.length) {
        rankingRated.innerHTML = `<li class="ranking-placeholder">Nenhuma avaliacao cadastrada.</li>`;
    } else {
        rankingRated.innerHTML = byRated.slice(0, 3).map((book, index) => {
            const coverData = bookCovers[book.id_rfid];
            const coverMarkup = coverData
                ? `<img src="${coverData.src}" alt="Capa do livro ${book.titulo}" class="ranking-book-cover">`
                : "";
            return `
                <li class="ranking-item rank-${index + 1}">
                    <div class="ranking-position">${index + 1}</div>
                    ${coverMarkup}
                    <div class="ranking-details">
                        <div class="ranking-name">${book.titulo}</div>
                        <div class="ranking-meta">★ ${parseFloat(book.nota_media).toFixed(1)} (${book.avaliacoes_count} voto(s))</div>
                    </div>
                </li>
            `;
        }).join("");
    }
}

function renderMockPanel(data) {
    if (!data.mock_enabled) {
        mockPanel.classList.add("hidden");
        return;
    }

    mockPanel.classList.remove("hidden");
    mockPanelSubtitle.textContent = `Porta atual: ${data.serial_mode}. Timeout de demonstracao: ${data.loan_timeout_seconds}s.`;

    const alunos = data.mock_data?.alunos || [];
    const livros = data.mock_data?.livros || [];

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

    mockGeneric.innerHTML = [...alunos, ...livros].map(item => {
        const label = item.nome || item.titulo;
        return `
            <button class="btn btn-secondary btn-sm mock-action-button"
                onclick="simulateScan('RFID', '${item.id_rfid}')">
                ${label}
            </button>
        `;
    }).join("");
}

async function simulateScan(type, rfidId) {
    try {
        const response = await fetch(`${API_BASE}/api/mock/scan`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                type,
                rfid_id: rfidId,
            }),
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || "Falha ao simular leitura.");
        }

        mockResult.className = result.success ? "mock-result success" : "mock-result error";
        mockResult.textContent = `${result.response} | ${result.message}`;
        await fetchDashboardData();
    } catch (error) {
        mockResult.className = "mock-result error";
        mockResult.textContent = error.message;
    }
}

function getStatusData(status) {
    if (status === "emprestado") {
        return { className: "badge-emprestado", label: "Emprestado" };
    }
    if (status === "atrasado") {
        return { className: "badge-atrasado", label: "Em atraso" };
    }
    return { className: "badge-disponivel", label: "Disponivel" };
}

function formatEventType(eventType) {
    const labels = {
        serial_connection: "Conexao serial",
        student_identified: "Aluno identificado",
        rfid_classification: "Classificacao RFID",
        loan_created: "Emprestimo",
        loan_returned: "Devolucao",
        loan_overdue: "Atraso",
        review_created: "Avaliacao",
        book_scan: "Leitura de livro",
        system: "Sistema",
        daemon_error: "Erro interno",
        book_state_repaired: "Ajuste de estado",
    };
    return labels[eventType] || eventType;
}

function formatDate(dateStr) {
    if (!dateStr) {
        return "";
    }

    try {
        const parts = dateStr.split(" ");
        const timePart = parts[1] || "";
        const timeSubparts = timePart.split(":");
        return `${parts[0]} ${timeSubparts[0]}:${timeSubparts[1]}`;
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
    setReviewModalMode("create");
    originalReviewSnapshot = null;
    activeReviewerName = null;
    formBookId.value = bookId;
    renderReviewBookPreview(bookId, bookTitle);
    renderReviewAuthor(null);
    setStarRating(0);
    formComment.value = "";
    formComment.setCustomValidity("");
    formComment.classList.remove("field-error");
    updateCommentCounter();
    ratingError.classList.add("hidden");
    reviewModal.classList.remove("hidden");
}

function openExistingReview(reviewIndex) {
    const review = currentReviews[reviewIndex];
    if (!review) {
        return;
    }

    const isOwnReview =
        review.aluno_id &&
        currentActiveStudent &&
        review.aluno_id === currentActiveStudent.id_rfid;

    activeReviewerName = review.aluno_nome || null;
    setReviewModalMode(isOwnReview ? "view-own" : "view");
    activeReviewId = review.id;
    formBookId.value = review.livro_id;
    renderReviewBookPreview(review.livro_id, review.livro_titulo);
    renderReviewAuthor(review.aluno_nome);
    setStarRating(Number(review.nota) || 0);
    formComment.value = review.comentario || "";
    originalReviewSnapshot = {
        rating: Number(review.nota) || 0,
        comment: review.comentario || "",
    };
    formComment.setCustomValidity("");
    formComment.classList.remove("field-error");
    updateCommentCounter();
    updateReviewEditActions();
    ratingError.classList.add("hidden");
    reviewModal.classList.remove("hidden");
}

function setReviewModalMode(mode) {
    activeReviewMode = mode;
    isReviewReadonly = mode === "view" || mode === "view-own";
    activeReviewId = mode === "create" ? null : activeReviewId;

    const titles = {
        create: "Avaliar livro",
        "view-own": "Minha avaliação",
        edit: "Editar minha avaliação",
        view: "Avaliação registrada",
    };

    reviewModalTitle.textContent = titles[mode];
    commentLabel.textContent = mode === "view"
        ? getReviewerLabel(activeReviewerName)
        : "Sua avaliação sobre a leitura";
    btnReviewSubmit.classList.toggle("hidden", mode === "view");
    btnReviewSubmit.textContent = mode === "view-own"
        ? "Alterar avaliação"
        : mode === "edit"
            ? "Salvar alterações"
            : "Salvar avaliação";
    btnReviewSubmit.classList.toggle("btn-primary", mode === "view-own");
    btnReviewSubmit.classList.toggle("btn-success", mode !== "view-own");
    btnModalCancel.classList.add("hidden");
    btnModalCancel.textContent = isReviewReadonly ? "Fechar" : "Cancelar";
    formComment.readOnly = isReviewReadonly;
    formComment.disabled = isReviewReadonly;
    formComment.required = !isReviewReadonly;
    reviewForm.classList.toggle("review-form-readonly", isReviewReadonly);
    updateReviewEditActions();
}

function updateCommentCounter() {
    commentCounter.textContent = `${formComment.value.length}/50`;
}

function updateReviewEditActions() {
    if (activeReviewMode !== "edit") {
        return;
    }

    const currentSnapshot = {
        rating: parseInt(formRatingValue.value, 10),
        comment: formComment.value,
    };
    const hasChanged =
        !originalReviewSnapshot ||
        currentSnapshot.rating !== originalReviewSnapshot.rating ||
        currentSnapshot.comment !== originalReviewSnapshot.comment;

    btnReviewSubmit.classList.toggle("hidden", !hasChanged);
}

function renderReviewBookPreview(bookId, bookTitle) {
    const coverData = bookCovers[bookId];
    const book = currentBooks.find(item => item.id_rfid === bookId);
    const author = book?.autor || coverData?.author || "Autor nao informado";

    reviewBookPreviewTitle.textContent = bookTitle;
    reviewBookPreviewAuthor.textContent = author;

    if (coverData) {
        reviewBookCover.src = coverData.src;
        reviewBookCover.alt = `Capa do livro ${bookTitle}`;
        reviewBookCover.classList.remove("hidden");
    } else {
        reviewBookCover.removeAttribute("src");
        reviewBookCover.alt = "";
        reviewBookCover.classList.add("hidden");
    }
}

function renderReviewAuthor(reviewerName) {
    if (!reviewerName) {
        reviewAuthorName.textContent = "";
        reviewAuthorName.classList.add("hidden");
        return;
    }

    reviewAuthorName.textContent = `Avaliado por ${reviewerName}`;
    reviewAuthorName.classList.remove("hidden");
}

function getReviewerLabel(reviewerName) {
    return reviewerName
        ? `Avaliação de ${reviewerName} sobre a leitura`
        : "Avaliação do leitor sobre a leitura";
}

function hideModal() {
    reviewModal.classList.add("hidden");
    setReviewModalMode("create");
    originalReviewSnapshot = null;
    activeReviewerName = null;
}

function showSuccessToast(message) {
    successToast.textContent = message;
    successToast.classList.remove("hidden");

    if (successToastTimeout) {
        clearTimeout(successToastTimeout);
    }

    successToastTimeout = setTimeout(() => {
        successToast.classList.add("hidden");
    }, 2000);
}

function setStarRating(rating) {
    formRatingValue.value = rating;
    ratingError.classList.add("hidden");
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

    if (activeReviewMode === "view-own") {
        setReviewModalMode("edit");
        btnReviewSubmit.classList.add("hidden");
        return;
    }

    if (isReviewReadonly) {
        return;
    }

    const bookId = formBookId.value;
    const rating = parseInt(formRatingValue.value, 10);
    const comment = formComment.value.trim().slice(0, 50);

    if (rating < 1) {
        ratingError.classList.remove("hidden");
        return;
    }

    try {
        const isEditingReview = activeReviewMode === "edit" && activeReviewId;
        const response = await fetch(
            isEditingReview
                ? `${API_BASE}/api/avaliacoes/${activeReviewId}`
                : `${API_BASE}/api/avaliar`,
            {
                method: isEditingReview ? "PATCH" : "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    livro_id: bookId,
                    nota: rating,
                    comentario: comment,
                }),
            }
        );

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || "Erro ao salvar avaliacao.");
        }

        hideModal();
        await fetchDashboardData();
        showSuccessToast(
            isEditingReview
                ? "Avaliacao atualizada com sucesso!"
                : "Avaliacao realizada com sucesso!"
        );
    } catch (error) {
        alert(`Falha ao salvar avaliacao: ${error.message}`);
    }
}

async function resetDatabase() {
    if (!confirm("Tem certeza que deseja resetar o banco de dados de demonstracao?")) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/reset`, { method: "POST" });
        if (!response.ok) {
            throw new Error("Falha ao resetar o banco de dados.");
        }

        mockResult.className = "mock-result";
        mockResult.textContent = "Banco reinicializado com os dados padrao.";
        await fetchDashboardData();
        alert("Banco de dados reinicializado com sucesso.");
    } catch (error) {
        alert(`Erro ao resetar o banco de dados: ${error.message}`);
    }
}
